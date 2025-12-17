"""
Appointment management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreateRequest, AppointmentResponse
from app.services.zapier_service import zapier_service
from app.services.validation_service import validation_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=AppointmentResponse)
async def create_appointment(
    request: AppointmentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a calendar appointment and send email invitation.
    
    This endpoint:
    - Validates email address
    - Creates an appointment record in the database
    - Creates a Google Calendar event
    - Sends confirmation email to the attendee
    - Returns appointment details with calendar link
    """
    try:
        # STEP 1: Validate email address (CRITICAL)
        logger.info(f"📧 Validating email: {request.attendee_email}")
        is_valid, error_msg = validation_service.validate_email(request.attendee_email)
        
        if not is_valid:
            logger.error(f"❌ Email validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid email address: {error_msg}. Please provide a valid email address."
            )
        
        # Normalize email
        normalized_email = validation_service.normalize_email(request.attendee_email)
        logger.info(f"✅ Email validated: {normalized_email}")
        
        # Parse datetime strings
        start_dt = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))
        
        # STEP 2: Create appointment record in database
        logger.info(f"📅 Creating appointment: {request.title} for {normalized_email}")
        appointment = Appointment(
            call_id=request.call_id,
            org_id=request.org_id,
            title=request.title,
            description=request.description,
            start_time=start_dt,
            end_time=end_dt,
            timezone=request.timezone,
            attendee_email=normalized_email,  # Use normalized email
            attendee_name=request.attendee_name,
            status="scheduled",
        )
        db.add(appointment)
        await db.flush()  # Get the appointment ID
        logger.info(f"✅ Appointment record created in database: {appointment.id}")
        
        # STEP 3: Send to Zapier webhook (handles both calendar and email)
        zapier_success = False
        calendar_event_id = None
        calendar_link = None
        email_sent = False
        
        try:
            logger.info(f"🔗 Sending appointment to Zapier webhook for {normalized_email}")
            zapier_result = await zapier_service.create_appointment_via_zapier(
                title=request.title,
                start_time=request.start_time,
                end_time=request.end_time,
                attendee_email=normalized_email,
                attendee_name=request.attendee_name,
                description=request.description,
                timezone=request.timezone,
                appointment_id=appointment.id,
            )
            
            if zapier_result["success"]:
                zapier_success = True
                appointment.status = "confirmed"
                appointment.calendar_invite_sent = True
                
                # Extract any returned data from Zapier (if webhook returns calendar/email info)
                webhook_response = zapier_result.get("webhook_response", {})
                if isinstance(webhook_response, dict):
                    calendar_event_id = webhook_response.get("calendar_event_id") or webhook_response.get("event_id")
                    calendar_link = webhook_response.get("calendar_link") or webhook_response.get("html_link") or webhook_response.get("event_link")
                    email_sent = webhook_response.get("email_sent", True)  # Assume sent if Zapier succeeds
                    
                    if calendar_event_id:
                        appointment.google_calendar_event_id = calendar_event_id
                    if calendar_link:
                        appointment.google_calendar_link = calendar_link
                
                appointment.meta_data = appointment.meta_data or {}
                appointment.meta_data["zapier_success"] = True
                appointment.meta_data["zapier_response"] = webhook_response
                
                logger.info(f"✅ Zapier webhook processed successfully")
                if calendar_event_id:
                    logger.info(f"   Calendar Event ID: {calendar_event_id}")
                if calendar_link:
                    logger.info(f"   Calendar Link: {calendar_link}")
            else:
                raise Exception("Zapier webhook returned unsuccessful status")
                
        except Exception as e:
            # If Zapier fails, log but continue (appointment is still saved)
            error_msg = str(e)
            logger.error(f"❌ Failed to process via Zapier webhook: {error_msg}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            appointment.meta_data = appointment.meta_data or {}
            appointment.meta_data["zapier_error"] = error_msg
            appointment.status = "scheduled"  # Keep as scheduled, not confirmed
        
        await db.commit()
        
        # Log final status
        logger.info(f"📊 Appointment creation summary:")
        logger.info(f"   Appointment ID: {appointment.id}")
        logger.info(f"   Zapier processed: {zapier_success}")
        logger.info(f"   Calendar created: {bool(calendar_event_id)}")
        logger.info(f"   Email sent: {email_sent}")
        logger.info(f"   Status: {appointment.status}")
        
        return AppointmentResponse(
            id=appointment.id,
            call_id=appointment.call_id,
            org_id=appointment.org_id,
            title=appointment.title,
            description=appointment.description,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            timezone=appointment.timezone,
            attendee_email=appointment.attendee_email,
            attendee_name=appointment.attendee_name,
            google_calendar_event_id=appointment.google_calendar_event_id,
            google_calendar_link=appointment.google_calendar_link,
            calendar_invite_sent=appointment.calendar_invite_sent,
            status=appointment.status,
            created_at=appointment.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get appointment details."""
    try:
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return AppointmentResponse(
            id=appointment.id,
            call_id=appointment.call_id,
            org_id=appointment.org_id,
            title=appointment.title,
            description=appointment.description,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            timezone=appointment.timezone,
            attendee_email=appointment.attendee_email,
            attendee_name=appointment.attendee_name,
            google_calendar_event_id=appointment.google_calendar_event_id,
            google_calendar_link=appointment.google_calendar_link,
            calendar_invite_sent=appointment.calendar_invite_sent,
            status=appointment.status,
            created_at=appointment.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get appointment: {str(e)}")


@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(
    org_id: Optional[str] = None,
    call_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List appointments, optionally filtered by org_id or call_id."""
    try:
        query = select(Appointment)
        
        if org_id:
            query = query.where(Appointment.org_id == org_id)
        if call_id:
            query = query.where(Appointment.call_id == call_id)
        
        query = query.order_by(Appointment.start_time.desc())
        
        result = await db.execute(query)
        appointments = result.scalars().all()
        
        return [
            AppointmentResponse(
                id=apt.id,
                call_id=apt.call_id,
                org_id=apt.org_id,
                title=apt.title,
                description=apt.description,
                start_time=apt.start_time,
                end_time=apt.end_time,
                timezone=apt.timezone,
                attendee_email=apt.attendee_email,
                attendee_name=apt.attendee_name,
                google_calendar_event_id=apt.google_calendar_event_id,
                google_calendar_link=apt.google_calendar_link,
                calendar_invite_sent=apt.calendar_invite_sent,
                status=apt.status,
                created_at=apt.created_at,
            )
            for apt in appointments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list appointments: {str(e)}")
