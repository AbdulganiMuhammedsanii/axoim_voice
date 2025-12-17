"""
Organization configuration API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.organization import Organization
from app.schemas.org import OrgConfigResponse, OrgConfigUpdate

router = APIRouter()


@router.get("/config/{org_id}", response_model=OrgConfigResponse)
async def get_org_config(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve organization configuration.
    """
    try:
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return OrgConfigResponse(
            id=org.id,
            name=org.name,
            business_hours=org.business_hours,
            after_hours_policy=org.after_hours_policy,
            services_offered=org.services_offered,
            escalation_phone=org.escalation_phone,
            config=org.config or {},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get org config: {str(e)}")


@router.post("/config/{org_id}")
async def update_org_config(
    org_id: str,
    update: OrgConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update organization configuration.
    """
    try:
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Update fields
        if update.name is not None:
            org.name = update.name
        if update.business_hours is not None:
            org.business_hours = update.business_hours
        if update.after_hours_policy is not None:
            org.after_hours_policy = update.after_hours_policy
        if update.services_offered is not None:
            org.services_offered = update.services_offered
        if update.escalation_phone is not None:
            org.escalation_phone = update.escalation_phone
        if update.config is not None:
            org.config = update.config
        
        await db.commit()
        
        return {"success": True, "message": "Configuration updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update org config: {str(e)}")

