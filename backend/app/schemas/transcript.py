"""Schemas for transcript API endpoints."""

from pydantic import BaseModel
from datetime import datetime


class TranscriptCreateRequest(BaseModel):
    """Request schema for creating a transcript."""
    call_id: str
    speaker: str  # "user", "agent", or "system"
    text: str


class TranscriptResponse(BaseModel):
    """Response schema for transcript."""
    id: str
    call_id: str
    speaker: str
    text: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

