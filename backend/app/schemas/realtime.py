"""Schemas for Realtime API endpoints."""

from pydantic import BaseModel, Field


class RealtimeSessionCreate(BaseModel):
    """Request schema for creating a Realtime session."""
    org_id: str = Field(..., description="Organization ID")


class RealtimeSessionResponse(BaseModel):
    """Response schema for Realtime session creation."""
    session_id: str = Field(..., description="OpenAI Realtime session ID")
    client_secret: str = Field(..., description="Client secret for connecting to Realtime API")
    expires_at: str = Field(..., description="Session expiration timestamp")
    session_config: dict = Field(default_factory=dict, description="Full session config to send via session.update")

