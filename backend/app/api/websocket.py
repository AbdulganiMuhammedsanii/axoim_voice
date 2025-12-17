"""
WebSocket proxy endpoint for OpenAI Realtime API.

This proxy handles authentication server-side since browsers
can't set custom headers on WebSocket connections.
"""

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import httpx
import json
import asyncio
from app.core.config import settings

router = APIRouter()


@router.websocket("/realtime/ws")
async def websocket_proxy(websocket: WebSocket):
    """
    WebSocket proxy that connects to OpenAI Realtime API with proper authentication.
    
    The frontend connects to this endpoint, and this endpoint forwards
    messages to/from OpenAI Realtime API with the API key in headers.
    """
    # Accept the WebSocket connection
    # This must be called before any other operations
    # Check origin for CORS (WebSockets need explicit origin checking)
    origin = websocket.headers.get("origin")
    allowed_origins = settings.CORS_ORIGINS
    
    print(f"WebSocket connection attempt from origin: {origin}")
    print(f"Allowed origins: {allowed_origins}")
    
    # Allow connection if origin is in allowed list or if no origin (same-origin)
    if origin and origin not in allowed_origins:
        print(f"Rejecting WebSocket: origin {origin} not in allowed list")
        await websocket.close(code=1008, reason="Origin not allowed")
        return
    
    try:
        await websocket.accept()
        print("WebSocket connection accepted successfully")
    except Exception as e:
        print(f"Error accepting WebSocket: {e}")
        print(f"WebSocket headers: {websocket.headers}")
        return
    
    # OpenAI Realtime API WebSocket URL (GA format)
    # Model is specified in session.update, not in URL
    openai_ws_url = "wss://api.openai.com/v1/realtime?model=gpt-realtime"
    
    # Get ephemeral key from query params
    # The frontend should pass the client_secret (ephemeral key) when connecting
    ephemeral_key = None
    try:
        # FastAPI WebSocket query_params is a MultiDict-like object
        if hasattr(websocket, 'query_params') and "client_secret" in websocket.query_params:
            ephemeral_key = websocket.query_params["client_secret"]
    except Exception as e:
        print(f"Error getting query params: {e}")
        pass
    
    # Headers with ephemeral key for OpenAI (GA API - no beta header needed)
    if ephemeral_key:
        headers = {
            "Authorization": f"Bearer {ephemeral_key}",
        }
        print(f"Using ephemeral key: {ephemeral_key[:20]}...")
    else:
        # Fallback to API key if no ephemeral key provided (for backward compatibility)
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        }
        print("Using API key (no ephemeral key provided)")
    
    try:
        # Check if API key is set
        if not settings.OPENAI_API_KEY:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": {"message": "OpenAI API key not configured in backend"}
            }))
            await websocket.close(code=1008, reason="API key not configured")
            return
        
        # Connect to OpenAI Realtime API using websockets library
        import websockets
        
        try:
            # websockets library uses extra_headers parameter (not additional_headers)
            async with websockets.connect(
                openai_ws_url,
                extra_headers=headers,
            ) as openai_ws:
                # Create tasks for bidirectional message forwarding
                async def forward_to_openai():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await openai_ws.send(data)
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        print(f"Error forwarding to OpenAI: {e}")
                
                async def forward_to_client():
                    try:
                        while True:
                            data = await openai_ws.recv()
                            await websocket.send_text(data)
                    except websockets.exceptions.ConnectionClosed:
                        pass
                    except Exception as e:
                        print(f"Error forwarding to client: {e}")
                
                # Run both forwarding tasks concurrently
                await asyncio.gather(
                    forward_to_openai(),
                    forward_to_client(),
                    return_exceptions=True,
                )
        except websockets.exceptions.InvalidStatusCode as e:
            error_msg = f"Failed to connect to OpenAI: {e.status_code}"
            if e.status_code == 401:
                error_msg = "Invalid OpenAI API key"
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": {"message": error_msg}
            }))
            await websocket.close(code=1008, reason=error_msg)
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"WebSocket proxy error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": {"message": error_msg}
            }))
            await websocket.close(code=1011, reason=error_msg)
    except Exception as e:
        print(f"WebSocket proxy error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": {"message": str(e)}
            }))
            await websocket.close(code=1011, reason=str(e))
        except:
            pass

