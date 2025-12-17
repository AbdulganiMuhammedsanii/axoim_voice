"""Schemas for Organization API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class OrgConfigResponse(BaseModel):
    """Response schema for organization configuration."""
    id: str
    name: str
    business_hours: Optional[str]
    after_hours_policy: Optional[str]
    services_offered: Optional[str]
    escalation_phone: Optional[str]
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class OrgConfigUpdate(BaseModel):
    """Request schema for updating organization configuration."""
    name: Optional[str] = None
    business_hours: Optional[str] = None
    after_hours_policy: Optional[str] = None
    services_offered: Optional[str] = None
    escalation_phone: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

