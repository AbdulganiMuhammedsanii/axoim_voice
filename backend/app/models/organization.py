"""
Organization model for storing organization configuration.
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Organization(Base):
    """Organization table schema."""
    
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    business_hours = Column(Text, nullable=True)
    after_hours_policy = Column(String(100), nullable=True)  # e.g., "voicemail", "escalate", "closed"
    services_offered = Column(Text, nullable=True)
    escalation_phone = Column(String(50), nullable=True)
    # Store additional config as JSON for flexibility
    config = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

