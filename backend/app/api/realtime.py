"""
Realtime API endpoints for OpenAI Realtime session management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.realtime import RealtimeSessionCreate, RealtimeSessionResponse
from app.services.realtime_service import realtime_service
from app.services.org_service import get_org_config

router = APIRouter()


@router.post("/session", response_model=RealtimeSessionResponse)
async def create_realtime_session(
    request: RealtimeSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new OpenAI Realtime API session.
    
    This endpoint:
    - Validates the organization exists
    - Fetches organization configuration
    - Creates a Realtime session with org-specific system prompt
    - Returns session credentials for frontend connection
    """
    try:
        # Verify organization exists and get config
        org_config = await get_org_config(request.org_id, db)
        
        # Create Realtime session with org config
        session_data = await realtime_service.create_session(org_config)
        
        return RealtimeSessionResponse(
            session_id=session_data["session_id"],
            client_secret=session_data["client_secret"],
            expires_at=session_data["expires_at"],
            session_config=session_data.get("session_config", {}),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

