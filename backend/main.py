"""
FastAPI Backend for AI Voice Agent Platform

This is the main entry point for the backend API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import realtime, calls, org, websocket, appointments, execute
from app.core.config import settings
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="AI Voice Agent API",
    description="Backend API for AI voice agent platform with OpenAI Realtime integration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - configure for your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(realtime.router, prefix="/api/realtime", tags=["realtime"])
app.include_router(calls.router, prefix="/api/call", tags=["calls"])
app.include_router(calls.router, prefix="/api/calls", tags=["calls"])
app.include_router(org.router, prefix="/api/org", tags=["organization"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])
app.include_router(execute.router, prefix="/api/execute-intent", tags=["execute"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Voice Agent API is running"}


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "ai-voice-agent-api",
        "version": "1.0.0",
    }

