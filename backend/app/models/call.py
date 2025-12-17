"""
Call-related models: Call, CallTranscript, CallIntake
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Call(Base):
    """Call table schema."""
    
    __tablename__ = "calls"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="in_progress")  # in_progress, completed, failed, escalated
    escalated = Column(Boolean, default=False, nullable=False)
    # Store call metadata
    meta_data = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    transcripts = relationship("CallTranscript", back_populates="call", cascade="all, delete-orphan")
    intake = relationship("CallIntake", back_populates="call", uselist=False, cascade="all, delete-orphan")


class CallTranscript(Base):
    """Call transcript table for storing conversation messages."""
    
    __tablename__ = "call_transcripts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("calls.id"), nullable=False, index=True)
    speaker = Column(String(20), nullable=False)  # "user" or "agent"
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Store additional metadata (e.g., audio timestamps, confidence scores)
    meta_data = Column(JSONB, nullable=True, default=dict)
    
    # Relationship
    call = relationship("Call", back_populates="transcripts")


class CallIntake(Base):
    """Structured intake data extracted from the call."""
    
    __tablename__ = "call_intakes"
    
    call_id = Column(String, ForeignKey("calls.id"), primary_key=True)
    structured_json = Column(JSONB, nullable=False, default=dict)
    urgency_level = Column(String(20), nullable=True)  # low, medium, high, emergency
    completed = Column(Boolean, default=False, nullable=False)
    # Store raw intake data and any validation results
    meta_data = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    call = relationship("Call", back_populates="intake")

