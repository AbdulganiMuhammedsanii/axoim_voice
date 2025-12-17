"""
Call management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.call import Call, CallTranscript, CallIntake
from app.schemas.call import (
    CallStartRequest,
    CallStartResponse,
    CallEndRequest,
    CallResponse,
    CallListResponse,
    CallDetailResponse,
    TranscriptItem,
    IntakeData,
)
from app.services.state_service import state_service, ConversationPhase
from app.services.org_service import get_org_config

router = APIRouter()


@router.post("/start", response_model=CallStartResponse)
async def start_call(
    request: CallStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new call (browser demo or phone).
    
    Creates a call record and initializes conversation state.
    """
    try:
        # Verify organization exists
        await get_org_config(request.org_id, db)
        
        # Create call record
        call = Call(
            org_id=request.org_id,
            status="in_progress",
            escalated=False,
        )
        db.add(call)
        await db.flush()  # Get the call ID
        
        # Initialize call state
        await state_service.set_state(call.id, {
            "call_id": call.id,
            "org_id": request.org_id,
            "phase": ConversationPhase.GREETING.value,
            "transcripts": [],
            "escalated": False,
        })
        await state_service.update_phase(call.id, ConversationPhase.GREETING)
        
        await db.commit()
        
        return CallStartResponse(call_id=call.id, status="in_progress")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start call: {str(e)}")


@router.post("/transcript")
async def save_transcript(
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Save a transcript item in real-time.
    
    This endpoint is called by the frontend as transcripts come in.
    """
    try:
        call_id = request.get("call_id")
        speaker = request.get("speaker")
        text = request.get("text")
        
        if not all([call_id, speaker, text]):
            raise HTTPException(status_code=400, detail="Missing required fields: call_id, speaker, text")
        
        # Verify call exists
        result = await db.execute(select(Call).where(Call.id == call_id))
        call = result.scalar_one_or_none()
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Create and save transcript
        transcript = CallTranscript(
            call_id=call_id,
            speaker=speaker,
            text=text,
        )
        db.add(transcript)
        await db.commit()
        
        return {"id": transcript.id, "status": "saved"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save transcript: {str(e)}")


@router.post("/end")
async def end_call(
    request: CallEndRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    End a call and finalize the conversation.
    
    Persists any remaining transcripts and structured intake data to the database.
    """
    try:
        # Get call
        result = await db.execute(select(Call).where(Call.id == request.call_id))
        call = result.scalar_one_or_none()
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get call state
        state = await state_service.get_state(request.call_id)
        
        # Persist any remaining transcripts from state to database (backup)
        if state and "transcripts" in state:
            for transcript_item in state["transcripts"]:
                # Check if transcript already exists
                existing = await db.execute(
                    select(CallTranscript).where(
                        CallTranscript.call_id == call.id,
                        CallTranscript.speaker == transcript_item["speaker"],
                        CallTranscript.text == transcript_item["text"],
                    )
                )
                if not existing.scalar_one_or_none():
                    transcript = CallTranscript(
                        call_id=call.id,
                        speaker=transcript_item["speaker"],
                        text=transcript_item["text"],
                        timestamp=datetime.fromisoformat(transcript_item["timestamp"].replace("Z", "+00:00")),
                    )
                    db.add(transcript)
        
        # Update call status
        call.ended_at = datetime.utcnow()
        call.status = "completed"
        
        # If intake data exists in state, persist it
        if state and "intake_data" in state:
            intake_data = state["intake_data"]
            # Check if intake already exists
            intake_result = await db.execute(
                select(CallIntake).where(CallIntake.call_id == call.id)
            )
            existing_intake = intake_result.scalar_one_or_none()
            
            if existing_intake:
                existing_intake.structured_json = intake_data.get("structured_json", {})
                existing_intake.urgency_level = intake_data.get("urgency_level")
                existing_intake.completed = intake_data.get("completed", False)
            else:
                intake = CallIntake(
                    call_id=call.id,
                    structured_json=intake_data.get("structured_json", {}),
                    urgency_level=intake_data.get("urgency_level"),
                    completed=intake_data.get("completed", False),
                )
                db.add(intake)
        
        # Clean up state
        await state_service.delete_state(request.call_id)
        
        await db.commit()
        
        return {"success": True, "message": "Call ended successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to end call: {str(e)}")


@router.get("", response_model=CallListResponse)
async def list_calls(
    org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of calls to return"),
    offset: int = Query(0, ge=0, description="Number of calls to skip"),
    db: AsyncSession = Depends(get_db),
):
    """
    List recent calls for an organization.
    """
    try:
        query = select(Call)
        
        if org_id:
            query = query.where(Call.org_id == org_id)
        
        query = query.order_by(desc(Call.started_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        calls = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Call.id))
        if org_id:
            count_query = count_query.where(Call.org_id == org_id)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return CallListResponse(
            calls=[CallResponse.model_validate(call) for call in calls],
            total=total,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list calls: {str(e)}")


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_detail(
    call_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve detailed call information including transcript and intake data.
    """
    try:
        # Get call
        result = await db.execute(select(Call).where(Call.id == call_id))
        call = result.scalar_one_or_none()
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get transcripts
        transcript_result = await db.execute(
            select(CallTranscript)
            .where(CallTranscript.call_id == call_id)
            .order_by(CallTranscript.timestamp)
        )
        transcripts = transcript_result.scalars().all()
        
        # Get intake
        intake_result = await db.execute(
            select(CallIntake).where(CallIntake.call_id == call_id)
        )
        intake = intake_result.scalar_one_or_none()
        
        return CallDetailResponse(
            id=call.id,
            org_id=call.org_id,
            started_at=call.started_at,
            ended_at=call.ended_at,
            status=call.status,
            escalated=call.escalated,
            transcripts=[
                TranscriptItem(
                    speaker=t.speaker,
                    text=t.text,
                    timestamp=t.timestamp,
                )
                for t in transcripts
            ],
            intake=IntakeData(
                structured_json=intake.structured_json if intake else {},
                urgency_level=intake.urgency_level if intake else None,
                completed=intake.completed if intake else False,
            ) if intake else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get call detail: {str(e)}")

