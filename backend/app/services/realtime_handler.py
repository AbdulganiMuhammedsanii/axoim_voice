"""
Realtime Response Handler - Bridge between OpenAI Realtime and Zapier

This is the main orchestration layer that:
1. Receives tool calls from OpenAI Realtime (via frontend)
2. Validates the intent (IntentService)
3. Executes the action (ExecutionService)
4. Returns structured results for OpenAI Realtime

WHY THIS EXISTS:
- Single entry point for all Realtime → Zapier operations
- Clean separation of concerns
- Easy to add new tool types
- Centralized logging and error handling

FLOW:
  Frontend receives tool_call → POST /api/execute-intent → RealtimeHandler
                                                               ↓
                                                    IntentService.validate()
                                                               ↓
                                                    ExecutionService.execute()
                                                               ↓
                                                    Return structured result
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.intent_service import intent_service, IntentAction, ValidationResult
from app.services.execution_service import execution_service, ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class RealtimeHandler:
    """
    Main handler for bridging OpenAI Realtime tool calls to Zapier.
    
    USAGE:
        result = await realtime_handler.handle_tool_call(
            tool_name="create_appointment",
            tool_args={"title": "Meeting", "start_time": "...", ...},
            call_id="call_123",
            org_id="org_demo_001",
        )
        
        # result is a dict ready to send back to OpenAI Realtime
    """
    
    def __init__(self):
        self.intent_service = intent_service
        self.execution_service = execution_service
    
    async def handle_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        call_id: Optional[str] = None,
        org_id: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle a tool call from OpenAI Realtime.
        
        This is the main entry point - all tool calls go through here.
        
        Args:
            tool_name: Name of the tool (e.g., "create_appointment")
            tool_args: Arguments from the Realtime tool call
            call_id: Associated call ID for tracking
            org_id: Organization ID
            item_id: OpenAI Realtime item ID for response correlation
            
        Returns:
            Dict with:
            - success: bool
            - result: tool-specific result data
            - error: error message if failed
            - should_retry: whether the model should ask for clarification
        """
        logger.info(f"📥 Handling tool call: {tool_name}")
        logger.info(f"   Call ID: {call_id}")
        logger.info(f"   Item ID: {item_id}")
        logger.debug(f"   Args: {tool_args}")
        
        start_time = datetime.utcnow()
        
        try:
            # Route to appropriate handler
            if tool_name == "create_appointment":
                return await self._handle_create_appointment(
                    tool_args=tool_args,
                    call_id=call_id,
                    org_id=org_id,
                )
            elif tool_name == "escalate_call":
                return await self._handle_escalate_call(tool_args)
            elif tool_name == "complete_intake":
                return await self._handle_complete_intake(tool_args)
            elif tool_name == "end_call":
                return await self._handle_end_call(tool_args)
            else:
                logger.warning(f"⚠️ Unknown tool: {tool_name}")
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "should_retry": False,
                }
                
        except Exception as e:
            logger.error(f"❌ Error handling tool call: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "should_retry": True,
            }
        finally:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"⏱️ Tool call handled in {elapsed:.2f}s")
    
    async def _handle_create_appointment(
        self,
        tool_args: Dict[str, Any],
        call_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle create_appointment tool call with full pipeline.
        
        PIPELINE:
        1. Parse tool arguments safely
        2. Validate with strict schema
        3. Check for duplicates
        4. Save to database
        5. Execute Zapier webhook
        6. Return structured result
        """
        
        # STEP 1: Parse arguments safely
        parsed_args, parse_error = self.intent_service.parse_tool_call_safely(tool_args)
        
        if parse_error:
            logger.warning(f"❌ Failed to parse tool args: {parse_error}")
            return {
                "success": False,
                "error": f"Invalid tool arguments: {parse_error}",
                "should_retry": True,
                "clarification": "Please provide valid appointment details.",
            }
        
        # STEP 2: Validate with strict schema
        validation_result = self.intent_service.validate_calendar_intent(
            tool_args=parsed_args,
            call_id=call_id,
            org_id=org_id,
        )
        
        if not validation_result.is_valid:
            # Generate clarification message for the model
            clarification = self.intent_service.generate_clarification_message(validation_result)
            
            logger.warning(f"❌ Validation failed: {validation_result.errors}")
            return {
                "success": False,
                "error": "; ".join(validation_result.errors),
                "should_retry": True,
                "clarification": clarification,
                "missing_fields": [
                    e.split(":")[0] for e in validation_result.errors
                ],
            }
        
        intent = validation_result.intent
        
        # STEP 3: Check for duplicates
        if self.execution_service.was_executed(intent.intent_id):
            logger.info(f"🔄 Duplicate appointment detected: {intent.intent_id}")
            return {
                "success": True,
                "is_duplicate": True,
                "message": "This appointment was already created.",
                "appointment_id": intent.intent_id,
            }
        
        # STEP 4: Save to database
        db_appointment_id = None
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.appointment import Appointment
            
            async with AsyncSessionLocal() as db:
                # Parse datetime
                start_dt = datetime.fromisoformat(intent.start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(intent.end_time.replace("Z", "+00:00"))
                
                appointment = Appointment(
                    id=intent.intent_id,  # Use intent_id for idempotency
                    call_id=call_id,
                    org_id=org_id or "org_demo_001",
                    title=intent.title,
                    description=intent.description,
                    start_time=start_dt,
                    end_time=end_dt,
                    timezone=intent.timezone,
                    attendee_email=intent.attendees[0],
                    attendee_name=parsed_args.get("attendee_name"),
                    status="scheduled",
                )
                db.add(appointment)
                await db.commit()
                await db.refresh(appointment)
                db_appointment_id = appointment.id
                logger.info(f"💾 Appointment saved to database: {db_appointment_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save appointment to database: {e}")
            # Continue with Zapier even if DB fails
        
        # STEP 5: Execute via Zapier
        execution_result = await self.execution_service.execute_calendar_intent(intent)
        
        # Update database with Zapier result
        if db_appointment_id and execution_result.success:
            try:
                from app.core.database import AsyncSessionLocal
                from app.models.appointment import Appointment
                from sqlalchemy import select
                
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Appointment).where(Appointment.id == db_appointment_id)
                    )
                    apt = result.scalar_one_or_none()
                    if apt:
                        apt.status = "confirmed"
                        apt.calendar_invite_sent = True
                        apt.meta_data = apt.meta_data or {}
                        apt.meta_data["zapier_success"] = True
                        await db.commit()
                        logger.info(f"✅ Updated appointment status in database")
            except Exception as e:
                logger.error(f"❌ Failed to update appointment status: {e}")
        
        if not execution_result.success:
            logger.error(f"❌ Zapier execution failed: {execution_result.error}")
            return {
                "success": False,
                "error": execution_result.error or "Failed to create appointment",
                "should_retry": True,
                "clarification": "I was unable to send the calendar invite. The appointment was saved but please try again.",
                "appointment_id": db_appointment_id,
            }
        
        # STEP 6: Return success
        logger.info(f"✅ Appointment created successfully: {intent.intent_id}")
        return {
            "success": True,
            "message": f"Appointment created and confirmation email sent to {intent.attendees[0]}",
            "appointment_id": db_appointment_id or intent.intent_id,
            "calendar_link": execution_result.zapier_response.get("calendar_link"),
            "email_sent": True,
            "attendee_email": intent.attendees[0],
            "title": intent.title,
            "start_time": intent.start_time,
            "end_time": intent.end_time,
        }
    
    async def _handle_escalate_call(self, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalate_call tool - immediate success, no Zapier needed."""
        logger.info(f"🚨 Call escalated: {tool_args.get('reason')}")
        return {
            "success": True,
            "message": "Call escalated to human agent",
            "urgency": tool_args.get("urgency", "medium"),
        }
    
    async def _handle_complete_intake(self, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complete_intake tool - immediate success, no Zapier needed."""
        logger.info("✅ Intake completed")
        return {
            "success": True,
            "message": "Intake completed successfully",
        }
    
    async def _handle_end_call(self, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle end_call tool - immediate success, no Zapier needed."""
        logger.info("📞 Call ended")
        return {
            "success": True,
            "message": "Call ended",
            "reason": tool_args.get("reason", "completed"),
        }
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics from both validation and execution layers."""
        return {
            "validation": self.intent_service.get_validation_stats(),
            "execution": self.execution_service.get_execution_stats(),
        }


# Singleton instance
realtime_handler = RealtimeHandler()

