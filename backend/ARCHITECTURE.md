# Backend Architecture

## Overview

This backend is designed as a production-ready FastAPI application for an AI voice agent platform. It provides REST APIs for call management, OpenAI Realtime API integration, and organization configuration.

## Key Design Decisions

### 1. Separation of Concerns

- **API Layer** (`app/api/`): Handles HTTP requests/responses, validation, and routing
- **Service Layer** (`app/services/`): Contains business logic and external API integrations
- **Model Layer** (`app/models/`): SQLAlchemy ORM models for database entities
- **Schema Layer** (`app/schemas/`): Pydantic models for request/response validation

### 2. Async/Await Throughout

All database operations and external API calls use async/await for better performance and scalability.

### 3. State Management

- **In-memory by default**: Fast and sufficient for single-instance deployments
- **Redis optional**: Enable for multi-instance deployments or persistence requirements
- State includes: conversation phase, transcripts buffer, escalation status, intake data

### 4. Safety First

- System prompt explicitly states agent is NOT a medical professional
- Keyword-based emergency detection
- Multiple escalation triggers
- Backend can override and terminate sessions

### 5. Database Design

- **Organizations**: Central entity for multi-tenant support
- **Calls**: Core call tracking with status and metadata
- **CallTranscripts**: Separate table for scalability (can grow large)
- **CallIntakes**: Structured data extraction in JSONB for flexibility

## Data Flow

### Call Lifecycle

1. **Start Call**
   ```
   POST /api/call/start
   → Creates Call record
   → Initializes state (phase: greeting)
   → Returns call_id
   ```

2. **Create Realtime Session**
   ```
   POST /api/realtime/session
   → Fetches org config
   → Generates system prompt
   → Creates OpenAI Realtime session
   → Returns session credentials
   ```

3. **During Call**
   - Frontend connects to OpenAI Realtime API
   - Transcripts buffered in state
   - Tool calls handled by frontend → backend
   - State updated (phase, escalation, intake data)

4. **End Call**
   ```
   POST /api/call/end
   → Persists transcripts to DB
   → Persists intake data to DB
   → Updates call status
   → Cleans up state
   ```

## OpenAI Realtime Integration

### Session Creation

The backend creates Realtime sessions with:
- Organization-specific system prompt
- Function calling tools (escalation, intake, termination)
- Audio streaming configuration
- Turn-taking settings

### Event Handling

Events flow from OpenAI → Frontend → Backend:
- Transcripts: Frontend buffers, sends to backend on call end
- Tool calls: Frontend receives, calls backend, returns result to OpenAI
- State updates: Backend maintains call state throughout

## Escalation Logic

### Triggers

1. **Emergency Keywords**: Immediate escalation (e.g., "chest pain", "suicide")
2. **High-Priority Keywords**: Escalate with high urgency
3. **Explicit Requests**: User asks for human agent
4. **Uncertainty**: AI agent calls escalate_call tool
5. **Backend Override**: Admin can force escalation

### Process

1. Detection (keyword or tool call)
2. State updated (escalated: true, phase: escalation)
3. Call record updated in database
4. Frontend notified (via state or webhook - future)
5. Human agent connected (via Twilio - future)

## System Prompt Design

The system prompt is generated dynamically based on:
- Organization name and configuration
- Business hours and services
- Escalation policies
- Safety constraints (hardcoded)

Key safety elements:
- Explicit "NOT a medical professional" statement
- Clear boundaries on what agent can/cannot do
- Emergency keyword escalation instructions
- Structured output format requirements

## State Management Strategy

### In-Memory State

- Fast access
- No external dependencies
- Lost on server restart (acceptable - data persisted to DB)
- Suitable for single-instance deployments

### Redis State (Optional)

- Persistent across restarts
- Shared across multiple instances
- Better for production scaling
- Requires Redis infrastructure

### State Contents

```python
{
    "call_id": "call_123",
    "org_id": "org_456",
    "phase": "intake",  # greeting, intake, clarification, escalation, completed
    "transcripts": [...],  # Buffered before DB persistence
    "escalated": false,
    "escalation_reason": null,
    "intake_data": {...},  # Structured data before finalization
    "updated_at": "2024-12-15T10:30:00Z"
}
```

## API Design Principles

1. **RESTful**: Standard HTTP methods and status codes
2. **Idempotent**: Where possible (GET, PUT)
3. **Stateless**: Each request contains all needed info
4. **Versioned**: API version in path (`/api/v1/...`) - future
5. **Documented**: OpenAPI/Swagger auto-generated

## Error Handling

- **400 Bad Request**: Invalid input
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Server-side errors
- **503 Service Unavailable**: External service failures

All errors return JSON with:
```json
{
    "detail": "Error message"
}
```

## Security Considerations

### Current (Basic)

- CORS configuration
- Input validation via Pydantic
- SQL injection prevention (SQLAlchemy ORM)

### Future Enhancements

- Authentication/Authorization (JWT, OAuth)
- Rate limiting
- API key management
- Request signing
- Audit logging

## Scalability

### Horizontal Scaling

- Stateless API design
- Database connection pooling
- Redis for shared state
- Load balancer ready

### Performance Optimizations

- Database indexes on frequently queried fields
- Async operations throughout
- Connection pooling
- Efficient queries (select only needed fields)

## Monitoring & Observability

### Current

- Basic error logging
- Health check endpoint

### Future

- Structured logging (JSON)
- Metrics collection (Prometheus)
- Distributed tracing (OpenTelemetry)
- Error tracking (Sentry)

## Testing Strategy

### Unit Tests

- Service layer logic
- Escalation detection
- Prompt generation
- State management

### Integration Tests

- API endpoints
- Database operations
- OpenAI API integration (mocked)

### E2E Tests

- Full call lifecycle
- Escalation flows
- Error scenarios

## Deployment

### Development

```bash
uvicorn main:app --reload
```

### Production

- Use production ASGI server (Gunicorn + Uvicorn workers)
- Environment variables for configuration
- Database migrations (Alembic)
- Health checks and readiness probes
- Container orchestration (Kubernetes, Docker Compose)

## Future Enhancements

1. **Twilio Integration**: Phone-based calls
2. **Webhooks**: Real-time updates to external systems
3. **Analytics**: Call metrics and reporting
4. **Multi-tenancy**: Enhanced isolation and security
5. **Audio Storage**: Record and store call audio
6. **Advanced Escalation**: Workflow engine for escalation paths
7. **A/B Testing**: Different prompts/configurations
8. **Caching**: Redis caching for org configs

