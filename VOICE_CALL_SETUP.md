# Voice Call Setup

## Prerequisites

To use the voice call feature, you need:

1. **Backend running** on `http://localhost:8000`
2. **OpenAI API Key** with Realtime API access

## Environment Variables

Create a `.env.local` file in the root directory:

```bash
# Backend URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# OpenAI API Key (required for WebSocket connection)
NEXT_PUBLIC_OPENAI_API_KEY=sk-your-openai-api-key-here
```

## How It Works

1. **Click "Start Call"** - Creates a call record in the backend
2. **Session Creation** - Backend creates an OpenAI Realtime session
3. **WebSocket Connection** - Frontend connects directly to OpenAI Realtime API
4. **Audio Streaming** - Microphone input and speaker output are streamed in real-time
5. **Transcripts** - Conversation is transcribed and displayed

## Audio Requirements

- **Microphone access** - Browser will prompt for permission
- **Speaker/Headphones** - For hearing the AI agent's voice
- **Chrome/Edge recommended** - Best WebSocket and audio support

## Troubleshooting

### "OpenAI API key not found"
- Make sure `NEXT_PUBLIC_OPENAI_API_KEY` is set in `.env.local`
- Restart the Next.js dev server after adding the env variable

### "Connection error"
- Check that your OpenAI API key has Realtime API access
- Verify the backend is running on port 8000
- Check browser console for detailed error messages

### No audio output
- Check browser audio permissions
- Make sure your speakers/headphones are working
- Try refreshing the page and starting a new call

### Microphone not working
- Grant microphone permissions when prompted
- Check browser settings for microphone access
- Try a different browser

## Current Implementation

The voice call component:
- ✅ Connects to OpenAI Realtime API via WebSocket
- ✅ Streams audio input (microphone) to OpenAI
- ✅ Receives and plays audio output from AI
- ✅ Displays real-time transcripts
- ✅ Handles tool calls (escalation, intake, etc.)

## Next Steps

For production, consider:
- WebSocket proxy through backend (for API key security)
- Better error handling and reconnection logic
- Audio quality optimization
- Call recording functionality

