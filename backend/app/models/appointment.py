"""
Appointment model for storing calendar appointments.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Appointment(Base):
    """Appointment table schema."""
    
    __tablename__ = "appointments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("calls.id"), nullable=True, index=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    attendee_email = Column(String(255), nullable=False)
    attendee_name = Column(String(255), nullable=True)
    google_calendar_event_id = Column(String(255), nullable=True)
    google_calendar_link = Column(String(500), nullable=True)
    calendar_invite_sent = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="scheduled", nullable=False)  # scheduled, confirmed, cancelled, completed
    cancelled = Column(Boolean, default=False, nullable=False)
    meta_data = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
