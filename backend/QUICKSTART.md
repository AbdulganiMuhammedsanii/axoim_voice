# Quick Start Guide

Get the backend up and running in minutes.

## Prerequisites

- Python 3.10+
- PostgreSQL database (or Supabase account)
- OpenAI API key with Realtime API access

## Setup Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL`: Your PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `CORS_ORIGINS`: Your frontend URL (e.g., `["http://localhost:3000"]`)

### 3. Set Up Database

```bash
# Using psql
psql -U postgres -d voice_agent_db -f database/schema.sql

# Or using Supabase:
# 1. Go to SQL Editor
# 2. Copy contents of database/schema.sql
# 3. Run the SQL
```

### 4. Seed Sample Data (Optional)

```bash
psql -U postgres -d voice_agent_db -f database/seed.sql
```

This creates a sample organization with ID `org_demo_001`.

### 5. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 6. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Get organization config (using seeded org)
curl http://localhost:8000/api/org/config/org_demo_001

# Start a call
curl -X POST http://localhost:8000/api/call/start \
  -H "Content-Type: application/json" \
  -d '{"org_id": "org_demo_001"}'

# Create Realtime session
curl -X POST http://localhost:8000/api/realtime/session \
  -H "Content-Type: application/json" \
  -d '{"org_id": "org_demo_001"}'
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Next Steps

1. **Frontend Integration**: Update your Next.js frontend to call these APIs
2. **OpenAI Realtime**: Use the session credentials to connect to Realtime API
3. **Testing**: Create test organizations and make test calls
4. **Production**: Set up proper authentication, monitoring, and deployment

## Common Issues

### Database Connection Error

- Verify `DATABASE_URL` is correct
- Ensure PostgreSQL is running
- Check firewall/network settings

### OpenAI API Error

- Verify `OPENAI_API_KEY` is set correctly
- Ensure you have access to Realtime API (may require waitlist)
- Check API rate limits

### CORS Errors

- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Restart the server after changing `.env`

## Development Tips

- Use `--reload` flag for auto-reload during development
- Check logs for detailed error messages
- Use Swagger UI to test endpoints interactively
- Enable Redis for state management in production: set `USE_REDIS=true`

