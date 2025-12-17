# Appointment Tool Implementation (GA Realtime API)

## Overview

The `create_appointment` tool is a unified function that handles the complete appointment scheduling flow:
1. **Database Storage** - Saves appointment to PostgreSQL
2. **Google Calendar Integration** - Creates calendar event with attendee as guest
3. **Email Confirmation** - Sends confirmation email via Resend with calendar link

## Tool Definition

The tool is defined in `backend/app/services/realtime_service.py` and follows the GA Realtime API function calling format:

```python
{
    "type": "function",
    "name": "create_appointment",
    "description": "Create an appointment, add it to Google Calendar, and send a confirmation email...",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", ...},
            "start_time": {"type": "string", ...},  # ISO 8601 with timezone
            "end_time": {"type": "string", ...},     # ISO 8601 with timezone
            "attendee_email": {"type": "string", ...},  # Required
            "attendee_name": {"type": "string", ...},   # Optional
            "description": {"type": "string", ...},      # Optional
            "timezone": {"type": "string", ...}          # Optional, defaults to UTC
        },
        "required": ["title", "start_time", "end_time", "attendee_email"]
    }
}
```

## Flow

### 1. Agent Calls Tool
When the AI agent decides to create an appointment, it calls the `create_appointment` tool with the collected information.

### 2. Frontend Receives Function Call
The frontend (`components/voice-call.tsx`) receives the function call event from the WebSocket:

```typescript
// Event types handled:
- "response.function_call_arguments_part.done"
- "response.output_item.function_call.done"
- "response.output_item.function_call_arguments_part.done"
- "response.output_item.done" (with item.type === "function_call")
```

### 3. Frontend Calls Backend API
The frontend makes a POST request to `/api/appointments`:

```typescript
const response = await fetch("/api/appointments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    call_id: callId,
    org_id: orgId,
    title: args.title,
    start_time: args.start_time,
    end_time: args.end_time,
    attendee_email: args.attendee_email,
    attendee_name: args.attendee_name,
    timezone: args.timezone || "UTC",
  }),
})
```

### 4. Backend Processing (`backend/app/api/appointments.py`)

The backend endpoint performs these steps in order:

#### Step 1: Email Validation
```python
is_valid, error_msg = validation_service.validate_email(request.attendee_email)
if not is_valid:
    raise HTTPException(status_code=400, detail=f"Invalid email address: {error_msg}")
```

#### Step 2: Database Storage
```python
appointment = Appointment(
    call_id=call_id,
    org_id=org_id,
    title=title,
    start_time=start_time,
    end_time=end_time,
    attendee_email=normalized_email,
    # ... other fields
)
db.add(appointment)
await db.flush()  # Get appointment.id
```

#### Step 3: Google Calendar Event Creation
```python
calendar_result = await calendar_service.create_event(
    title=title,
    start_time=start_time,
    end_time=end_time,
    attendee_email=normalized_email,
    attendee_name=attendee_name,
    description=description,
    timezone=timezone,
)
# Updates appointment with calendar_event_id and calendar_link
```

#### Step 4: Confirmation Email
```python
email_result = await email_service.send_appointment_confirmation(
    to_email=normalized_email,
    attendee_name=attendee_name,
    appointment_title=title,
    start_time=start_time,
    end_time=end_time,
    calendar_link=calendar_link,
    timezone=timezone,
)
# Updates appointment metadata with email status
```

### 5. Frontend Submits Tool Result
After receiving the response, the frontend submits the result back to OpenAI:

```typescript
submitToolResult(itemId, {
  success: true,
  appointment_id: appointment.id,
  calendar_link: appointment.google_calendar_link,
  email_sent: appointment.calendar_invite_sent,
  message: `Appointment created and confirmation email sent to ${args.attendee_email}`
})
```

The tool result is sent using GA API format:
```typescript
{
  type: "response.create_item",
  item: {
    type: "function_call_output",
    call_id: callId,
    output: JSON.stringify(result),  // Must be JSON string
  }
}
```

## Error Handling

### Email Validation Errors
- Invalid format → Returns 400 error to frontend
- Frontend submits error result to OpenAI
- Agent can re-ask for email

### Calendar Creation Errors
- If Google Calendar API fails, appointment is still saved
- Error logged in `appointment.meta_data["calendar_error"]`
- Status set to "scheduled" (not "confirmed")
- Frontend still receives success, but with `calendar_link: null`

### Email Sending Errors
- If Resend API fails, appointment and calendar are still created
- Error logged in `appointment.meta_data["email_error"]`
- Frontend receives success with `email_sent: false`

## System Prompt Instructions

The system prompt (`backend/app/services/prompt_service.py`) includes strict instructions:

1. **MUST ask for email first** - "What email address should I send the confirmation to?"
2. **MUST call the tool** - Do not just say you'll create it
3. **MUST validate email** - Re-ask if format looks invalid
4. **MUST confirm before booking** - "I'll create an appointment for [title] on [date/time] and send a confirmation to [email]. Should I proceed?"

## Key Files

- **Tool Definition**: `backend/app/services/realtime_service.py` (lines 118-157)
- **Frontend Handler**: `components/voice-call.tsx` (lines 418-519)
- **Backend Endpoint**: `backend/app/api/appointments.py`
- **Calendar Service**: `backend/app/services/calendar_service.py`
- **Email Service**: `backend/app/services/email_service.py`
- **Validation Service**: `backend/app/services/validation_service.py`

## Testing

To test the tool:

1. Start a voice call
2. Say: "I'd like to schedule an appointment"
3. Provide: date/time, email address, name
4. Agent should call the tool automatically
5. Check:
   - Database: `appointments` table should have new record
   - Google Calendar: Event should appear with attendee
   - Email: Confirmation email should arrive in inbox

## Debugging

Enable detailed logging:
- Frontend: Check browser console for `🔧 Tool call received:` messages
- Backend: Check server logs for `📧`, `📆`, `✅`, `❌` emoji markers
- WebSocket: All messages are logged with `📨 Received message:`

## GA API Compliance

This implementation follows GA Realtime API patterns:
- ✅ Uses ephemeral client secrets
- ✅ Sends full session config via `session.update`
- ✅ Handles multiple function call event formats
- ✅ Submits tool results as JSON strings
- ✅ Uses correct event names (`response.output_item.done`, etc.)

