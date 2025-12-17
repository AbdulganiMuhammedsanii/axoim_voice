# Frontend Integration with Backend

The frontend has been integrated with the FastAPI backend to enable voice calls with OpenAI Realtime API.

## What Was Implemented

### 1. API Route Proxies
All Next.js API routes now proxy to the FastAPI backend:
- `/api/call/start` → `http://localhost:8000/api/call/start`
- `/api/call/end` → `http://localhost:8000/api/call/end`
- `/api/calls` → `http://localhost:8000/api/calls`
- `/api/realtime/session` → `http://localhost:8000/api/realtime/session`
- `/api/org/config` → `http://localhost:8000/api/org/config/{org_id}`

### 2. Voice Call Component
Created `components/voice-call.tsx` - A React component that:
- Starts a call via the backend
- Creates a Realtime session
- Shows call status and session info
- Provides UI for starting/ending calls

### 3. Dashboard Integration
Updated `app/page.tsx` to use the VoiceCall component instead of the simple button.

## Setup

### 1. Environment Variables
Create a `.env.local` file in the root directory:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 2. Start Backend
Make sure your FastAPI backend is running:

```bash
cd backend
source voicenv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend
```bash
npm run dev
```

## How It Works

1. **User clicks "Start Call"** in the dashboard
2. **Frontend calls** `/api/call/start` → Backend creates call record
3. **Frontend calls** `/api/realtime/session` → Backend creates OpenAI Realtime session
4. **Frontend receives** session credentials (session_id, client_secret)
5. **Frontend can connect** to OpenAI Realtime API using these credentials

## Current Status

✅ Backend integration complete
✅ API routes proxying correctly
✅ Voice call component created
✅ Session creation working

⚠️ **Note**: The full WebSocket connection to OpenAI Realtime API is simplified in the current implementation. For production, you'll need to:
- Use the official OpenAI Realtime SDK or implement full WebSocket protocol
- Handle audio encoding/decoding properly
- Implement proper event handling for transcripts and tool calls

## Next Steps

1. **Full WebSocket Implementation**: Complete the OpenAI Realtime WebSocket connection
2. **Audio Handling**: Implement proper audio input/output streaming
3. **Transcript Display**: Show real-time transcripts in the UI
4. **Tool Call Handling**: Process escalation, intake completion, etc.
5. **Error Handling**: Add better error messages and retry logic

## Testing

1. Start the backend: `uvicorn main:app --reload`
2. Start the frontend: `npm run dev`
3. Go to http://localhost:3000
4. Click "Start Call" in the Voice Call card
5. You should see:
   - Call ID
   - Session ID and Client Secret
   - Connection status

The session credentials are now available for connecting to OpenAI's Realtime API!

