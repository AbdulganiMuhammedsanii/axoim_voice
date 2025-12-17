"""
Intent Execution API Endpoint

This is the server-side endpoint that bridges OpenAI Realtime tool calls to Zapier.

WHY THIS ENDPOINT EXISTS:
1. Zapier webhooks MUST be called server-side (CORS blocks browser calls)
2. Validation must happen server-side (client can't be trusted)
3. Idempotency tracking requires server-side state
4. Logging and debugging require server access

FLOW:
  Frontend receives tool_call from Realtime
      ↓
  POST /api/execute-intent
      ↓
  RealtimeHandler.handle_tool_call()
      ↓
  IntentService.validate() → ExecutionService.execute()
      ↓
  Return result to frontend
      ↓
  Frontend sends result back to Realtime
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.realtime_handler import realtime_handler

logger = logging.getLogger(__name__)

router = APIRouter()


class ExecuteIntentRequest(BaseModel):
    """Request body for intent execution."""
    
    tool_name: str = Field(..., description="Name of the tool (e.g., 'create_appointment')")
    tool_args: Dict[str, Any] = Field(..., description="Arguments from Realtime tool call")
    call_id: Optional[str] = Field(None, description="Associated call ID for tracking")
    org_id: Optional[str] = Field(None, description="Organization ID")
    item_id: Optional[str] = Field(None, description="OpenAI Realtime item ID for correlation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "create_appointment",
                "tool_args": {
                    "title": "Consultation with John",
                    "start_time": "2024-12-20T14:00:00Z",
                    "end_time": "2024-12-20T15:00:00Z",
                    "attendee_email": "john@example.com",
                    "attendee_name": "John Doe",
                    "timezone": "UTC"
                },
                "call_id": "call_abc123",
                "org_id": "org_demo_001",
                "item_id": "item_xyz789"
            }
        }


class ExecuteIntentResponse(BaseModel):
    """Response from intent execution."""
    
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    should_retry: bool = False
    is_duplicate: bool = False
    appointment_id: Optional[str] = None
    calendar_link: Optional[str] = None
    email_sent: bool = False
    clarification: Optional[str] = None
    missing_fields: Optional[list] = None
    
    # Additional result data
    result_data: Optional[Dict[str, Any]] = None


@router.post("", response_model=ExecuteIntentResponse)
async def execute_intent(request: ExecuteIntentRequest) -> ExecuteIntentResponse:
    """
    Execute a validated intent via the appropriate service (e.g., Zapier).
    
    This endpoint is called by the frontend when it receives a tool_call
    from OpenAI Realtime. It:
    
    1. Validates the tool arguments strictly
    2. Checks for duplicate executions
    3. Executes via Zapier webhook (server-side only)
    4. Returns structured result for Realtime
    
    The frontend should:
    1. Call this endpoint when receiving a tool_call
    2. Send the result back to Realtime via conversation.item.create
    3. Display appropriate UI feedback
    """
    logger.info(f"📥 Execute intent request: {request.tool_name}")
    logger.info(f"   Call ID: {request.call_id}")
    logger.info(f"   Org ID: {request.org_id}")
    
    try:
        # Delegate to RealtimeHandler for full pipeline
        result = await realtime_handler.handle_tool_call(
            tool_name=request.tool_name,
            tool_args=request.tool_args,
            call_id=request.call_id,
            org_id=request.org_id,
            item_id=request.item_id,
        )
        
        # Map result to response model
        return ExecuteIntentResponse(
            success=result.get("success", False),
            message=result.get("message"),
            error=result.get("error"),
            should_retry=result.get("should_retry", False),
            is_duplicate=result.get("is_duplicate", False),
            appointment_id=result.get("appointment_id"),
            calendar_link=result.get("calendar_link"),
            email_sent=result.get("email_sent", False),
            clarification=result.get("clarification"),
            missing_fields=result.get("missing_fields"),
            result_data=result,
        )
        
    except Exception as e:
        logger.error(f"❌ Execute intent failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute intent: {str(e)}"
        )


@router.get("/stats")
async def get_pipeline_stats():
    """
    Get pipeline statistics for debugging.
    
    Returns validation and execution stats to help debug issues.
    """
    return realtime_handler.get_pipeline_stats()


@router.post("/reset/{intent_id}")
async def reset_execution(intent_id: str):
    """
    Reset execution status for an intent (allows retry).
    
    USE WITH CAUTION: This allows the same intent to be executed again,
    potentially creating duplicate calendar events.
    """
    from app.services.execution_service import execution_service
    
    success = execution_service.reset_execution(intent_id)
    
    if success:
        logger.info(f"🔄 Reset execution for: {intent_id}")
        return {"success": True, "message": f"Execution reset for {intent_id}"}
    else:
        return {"success": False, "message": f"No execution found for {intent_id}"}

