# OpenAI Realtime → Zapier Pipeline

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION PIPELINE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   OpenAI    │     │  Frontend   │     │   Backend   │     │   Zapier    │
│  Realtime   │     │  voice-call │     │  FastAPI    │     │  Webhook    │
│   (Voice)   │     │    .tsx     │     │             │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  tool_call:       │                   │                   │
       │  create_          │                   │                   │
       │  appointment      │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │  POST /api/       │                   │
       │                   │  execute-intent   │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │           ┌───────┴───────┐           │
       │                   │           │ IntentService │           │
       │                   │           │  (Validate)   │           │
       │                   │           └───────┬───────┘           │
       │                   │                   │                   │
       │                   │           ┌───────┴───────┐           │
       │                   │           │ ExecutionSvc  │           │
       │                   │           │ (Idempotency) │           │
       │                   │           └───────┬───────┘           │
       │                   │                   │                   │
       │                   │                   │  POST webhook     │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │<──────────────────│
       │                   │                   │     200 OK        │
       │                   │<──────────────────│                   │
       │                   │   {success: true} │                   │
       │                   │                   │                   │
       │  tool_result:     │                   │                   │
       │  {success: true,  │                   │                   │
       │   email_sent: ..} │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  "I've created    │                   │                   │
       │   your appt..."   │                   │                   │
       │──────────────────>│                   │                   │
```

## Key Components

### 1. IntentService (`app/services/intent_service.py`)

**Purpose:** Strict validation of tool call arguments

```python
# Example usage
result = intent_service.validate_calendar_intent(
    tool_args={"title": "Meeting", "start_time": "...", "attendee_email": "..."},
    call_id="call_123",
    org_id="org_demo_001"
)

if result.is_valid:
    # Proceed to execution
    intent = result.intent
else:
    # Return errors to model for clarification
    errors = result.errors
```

**What it validates:**
- Required fields exist (title, start_time, end_time, attendee_email)
- ISO-8601 datetime format
- Valid email format
- Non-empty values

**What it rejects:**
- Missing fields → Returns clarification message
- Invalid email → Returns validation error
- Malformed JSON → Safely handles parse errors

### 2. ExecutionService (`app/services/execution_service.py`)

**Purpose:** Idempotent Zapier webhook execution

```python
# Example usage
result = await execution_service.execute_calendar_intent(intent)

if result.is_duplicate:
    # Same appointment was already created
    pass
elif result.success:
    # Zapier webhook executed successfully
    pass
else:
    # Zapier error - can retry
    pass
```

**Idempotency:**
- Generates deterministic ID from: `title|start_time|end_time|email`
- Same appointment details = same ID
- Duplicate requests return `is_duplicate: true` without calling Zapier

**Thread Safety:**
- Uses asyncio.Lock per intent_id
- Prevents race conditions on rapid reconnects

### 3. RealtimeHandler (`app/services/realtime_handler.py`)

**Purpose:** Orchestration layer

```python
# Main entry point
result = await realtime_handler.handle_tool_call(
    tool_name="create_appointment",
    tool_args={...},
    call_id="...",
    org_id="..."
)
```

**Routes tool calls to appropriate handlers:**
- `create_appointment` → Full pipeline (validate → execute → Zapier)
- `escalate_call` → Immediate success
- `complete_intake` → Immediate success
- `end_call` → Immediate success + cleanup

### 4. Execute API (`app/api/execute.py`)

**Endpoint:** `POST /api/execute-intent`

**Request:**
```json
{
  "tool_name": "create_appointment",
  "tool_args": {
    "title": "Consultation",
    "start_time": "2024-12-20T14:00:00Z",
    "end_time": "2024-12-20T15:00:00Z",
    "attendee_email": "user@example.com"
  },
  "call_id": "call_abc123",
  "org_id": "org_demo_001"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Appointment created and confirmation email sent to user@example.com",
  "appointment_id": "5b6948ce80b595f2",
  "email_sent": true,
  "is_duplicate": false
}
```

**Validation Error Response:**
```json
{
  "success": false,
  "error": "Missing required fields: attendee_email",
  "should_retry": true,
  "clarification": "VALIDATION_FAILED: Cannot create appointment. Missing required fields: attendee_email. Please ask the user to provide the missing or correct information."
}
```

## Why This Architecture?

### 1. Zapier Must Be Server-Side

**Problem:** Browsers cannot call Zapier webhooks directly
- CORS blocks cross-origin requests
- API keys would be exposed in browser

**Solution:** All Zapier calls go through FastAPI backend

### 2. Validation Prevents Model Hallucination

**Problem:** Model might "think" it created an appointment
- Partial responses before final JSON
- Natural language mixed with tool calls

**Solution:** Strict schema validation
- Required fields enforced
- Invalid data rejected with clarification
- Model must ask user for missing info

### 3. Idempotency Prevents Duplicates

**Problem:** Realtime reconnects cause duplicate tool calls
- Network blips trigger retries
- Same intent received multiple times

**Solution:** Deterministic intent ID
- Same appointment details = same ID
- Second request returns `is_duplicate: true`
- Zapier only called once

### 4. Structured Results Guide Model

**Problem:** Model doesn't know if action succeeded

**Solution:** Clear success/failure in tool results
- Success: Model confirms to user
- Validation error: Model asks for clarification
- Execution error: Model apologizes and offers retry

## Testing

```bash
# Test successful appointment
curl -X POST "http://localhost:8000/api/execute-intent" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_appointment",
    "tool_args": {
      "title": "Test Meeting",
      "start_time": "2024-12-20T14:00:00Z",
      "end_time": "2024-12-20T15:00:00Z",
      "attendee_email": "test@example.com"
    },
    "org_id": "org_demo_001"
  }'

# Test validation error (missing email)
curl -X POST "http://localhost:8000/api/execute-intent" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_appointment",
    "tool_args": {
      "title": "Test Meeting",
      "start_time": "2024-12-20T14:00:00Z",
      "end_time": "2024-12-20T15:00:00Z"
    },
    "org_id": "org_demo_001"
  }'

# Check pipeline stats
curl http://localhost:8000/api/execute-intent/stats
```

## Debugging

### Common Issues

1. **Zapier returns non-200**
   - Check webhook URL in `.env`
   - Verify Zap is published and ON
   - Check Zapier Task History

2. **Duplicate appointments created**
   - Backend was restarted (clears in-memory state)
   - Different tool_args hash (check exact values)
   - Solution: Use Redis for persistent idempotency

3. **Model not calling tool**
   - Check system prompt includes tool instructions
   - Verify tools are sent in session.update
   - Check WebSocket logs for function_call events

4. **Validation always failing**
   - Check tool_args format (JSON vs string)
   - Verify datetime format is ISO-8601 with timezone
   - Email must be valid format

### Logs to Check

```bash
# Backend logs
tail -f backend/logs/app.log | grep -E "(execute-intent|Zapier|Intent)"

# Or in terminal where uvicorn runs
# Look for:
# 📥 Execute intent request: create_appointment
# 🔍 Validating calendar intent: ...
# 🔑 Generated idempotency key: ...
# 📤 Executing Zapier webhook for intent: ...
# ✅ Zapier webhook executed successfully
```

