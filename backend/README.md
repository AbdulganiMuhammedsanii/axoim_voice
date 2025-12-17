# AI Voice Agent Backend

Production-ready FastAPI backend for an AI voice agent platform with OpenAI Realtime API integration.

## Architecture

This backend provides:
- REST API endpoints for call management
- OpenAI Realtime API session creation and management
- PostgreSQL database for persistent storage
- In-memory or Redis-based state management
- Safety and escalation logic
- Organization-specific configuration

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── app/
│   ├── api/               # API route handlers
│   │   ├── realtime.py    # Realtime session endpoints
│   │   ├── calls.py       # Call management endpoints
│   │   └── org.py         # Organization config endpoints
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings and environment variables
│   │   └── database.py    # Database connection and session management
│   ├── models/            # SQLAlchemy database models
│   │   ├── organization.py
│   │   └── call.py
│   ├── schemas/           # Pydantic request/response schemas
│   │   ├── realtime.py
│   │   ├── call.py
│   │   └── org.py
│   └── services/          # Business logic services
│       ├── realtime_service.py    # OpenAI Realtime API integration
│       ├── prompt_service.py      # System prompt generation
│       ├── org_service.py         # Organization data access
│       ├── state_service.py       # Call state management
│       └── escalation_service.py  # Safety and escalation logic
├── database/
│   └── schema.sql         # Database schema SQL
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `CORS_ORIGINS`: Allowed frontend origins

### 3. Set Up Database

Create the database and run the schema:

```bash
# Using psql
psql -U postgres -d voice_agent_db -f database/schema.sql

# Or using Supabase SQL editor
# Copy and paste the contents of database/schema.sql
```

### 4. Run the Server

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Realtime Sessions

- `POST /api/realtime/session` - Create a new OpenAI Realtime session

### Call Management

- `POST /api/call/start` - Start a new call
- `POST /api/call/end` - End a call and persist data
- `GET /api/calls` - List calls (with optional org_id filter)
- `GET /api/calls/{call_id}` - Get detailed call information

### Organization Configuration

- `GET /api/org/config/{org_id}` - Get organization configuration
- `POST /api/org/config/{org_id}` - Update organization configuration

## OpenAI Realtime Integration

The backend creates Realtime sessions with:
- System prompt injected with organization-specific rules
- Function calling tools for escalation, intake completion, and call termination
- Turn-taking and audio streaming configuration
- Safety constraints built into the prompt

### Session Creation Flow

1. Frontend calls `POST /api/realtime/session` with `org_id`
2. Backend fetches organization configuration
3. Backend generates system prompt with org rules
4. Backend creates Realtime session via OpenAI API
5. Backend returns `session_id` and `client_secret` to frontend
6. Frontend connects directly to OpenAI Realtime API using credentials

### Event Handling

The frontend should handle Realtime events and:
- Send transcript events to backend for storage
- Handle tool calls (escalation, intake completion) by calling backend endpoints
- Update call state as conversation progresses

## System Prompt

The system prompt includes:
- Clear safety constraints (NOT a medical professional)
- Organization-specific information
- Intake process guidelines
- Escalation triggers
- Structured output format

See `app/services/prompt_service.py` for the full prompt.

## State Management

Call state is managed in-memory by default, with optional Redis support:

- Conversation phase tracking (greeting, intake, clarification, escalation, completed)
- Transcript buffering before DB persistence
- Escalation status and metadata
- Intake data before finalization

To enable Redis:
1. Set `USE_REDIS=true` in `.env`
2. Set `REDIS_URL` to your Redis instance
3. Install Redis: `pip install redis[hiredis]`

## Safety & Escalation

The escalation service detects:
- Emergency keywords (immediate escalation)
- High-priority keywords
- Explicit escalation requests
- Uncertainty patterns

Escalation can be triggered:
- Automatically via keyword detection
- Via tool call from the AI agent
- Manually via backend override

## Database Models

### Organizations
- Organization configuration and business rules

### Calls
- Call metadata, status, timestamps
- Escalation flags

### CallTranscripts
- Conversation messages with speaker labels
- Timestamps and metadata

### CallIntakes
- Structured intake data in JSON format
- Urgency levels and completion status

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Production Considerations

1. **Database**: Use connection pooling and proper indexing
2. **Redis**: Enable Redis for state management in production
3. **Security**: Implement proper authentication/authorization
4. **Monitoring**: Add logging and monitoring (e.g., Sentry, DataDog)
5. **Rate Limiting**: Add rate limiting to prevent abuse
6. **Error Handling**: Implement comprehensive error handling and retries
7. **Scaling**: Consider horizontal scaling with load balancer

## Future Enhancements

- Twilio integration for phone-based calls
- Webhook support for real-time updates
- Analytics and reporting endpoints
- Multi-tenant support with proper isolation
- Audio recording storage
- Advanced escalation workflows

