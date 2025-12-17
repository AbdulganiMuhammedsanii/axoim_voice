"""
Organization service for fetching and managing organization data.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organization import Organization
from typing import Dict, Any, Optional


async def get_org_config(org_id: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Get organization configuration.
    
    Args:
        org_id: Organization ID
        db: Optional database session (if None, will need to be provided by caller)
        
    Returns:
        Dictionary with organization configuration
    """
    # If db is None, this function should be called from within a route that has db dependency
    if db is None:
        raise ValueError("Database session is required")
    
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise ValueError(f"Organization {org_id} not found")
    
    return {
        "id": org.id,
        "name": org.name,
        "business_hours": org.business_hours,
        "after_hours_policy": org.after_hours_policy,
        "services_offered": org.services_offered,
        "escalation_phone": org.escalation_phone,
        "config": org.config or {},
    }

