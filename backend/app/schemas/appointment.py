"""Schemas for Appointment API endpoints."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class AppointmentCreateRequest(BaseModel):
    """Request schema for creating an appointment."""
    call_id: Optional[str] = Field(None, description="Associated call ID")
    org_id: str = Field(..., description="Organization ID")
    title: str = Field(..., description="Appointment title")
    description: Optional[str] = Field(None, description="Appointment description")
    start_time: str = Field(..., description="Start time in ISO 8601 format")
    end_time: str = Field(..., description="End time in ISO 8601 format")
    timezone: str = Field(default="UTC", description="Timezone")
    attendee_email: EmailStr = Field(..., description="Attendee email address")
    attendee_name: Optional[str] = Field(None, description="Attendee name")


class AppointmentResponse(BaseModel):
    """Response schema for appointment."""
    id: str
    call_id: Optional[str]
    org_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    timezone: str
    attendee_email: str
    attendee_name: Optional[str]
    google_calendar_event_id: Optional[str]
    google_calendar_link: Optional[str]
    calendar_invite_sent: bool
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
