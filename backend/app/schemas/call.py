"""Schemas for Call API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CallStartRequest(BaseModel):
    """Request schema for starting a call."""
    org_id: str = Field(..., description="Organization ID")


class CallStartResponse(BaseModel):
    """Response schema for call start."""
    call_id: str = Field(..., description="Unique call identifier")
    status: str = Field(default="in_progress", description="Call status")


class CallEndRequest(BaseModel):
    """Request schema for ending a call."""
    call_id: str = Field(..., description="Call ID to end")


class CallResponse(BaseModel):
    """Basic call information."""
    id: str
    org_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    escalated: bool
    
    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    """Response schema for listing calls."""
    calls: List[CallResponse]
    total: int


class TranscriptItem(BaseModel):
    """Individual transcript entry."""
    speaker: str
    text: str
    timestamp: datetime


class IntakeData(BaseModel):
    """Structured intake data."""
    structured_json: Dict[str, Any]
    urgency_level: Optional[str]
    completed: bool


class CallDetailResponse(BaseModel):
    """Detailed call information with transcript and intake."""
    id: str
    org_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    escalated: bool
    transcripts: List[TranscriptItem]
    intake: Optional[IntakeData]
    
    class Config:
        from_attributes = True

