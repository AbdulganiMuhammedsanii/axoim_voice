"""
Execution Service - Zapier Webhook Execution with Idempotency

This service is the CRITICAL execution layer that makes the actual Zapier webhook calls.

WHY ZAPIER MUST BE CALLED SERVER-SIDE:
1. CORS - Browsers block cross-origin requests to Zapier webhooks
2. Security - API keys should never be exposed in browser
3. Logging - Server can log all executions for debugging
4. Idempotency - Server can track and prevent duplicate calls

WHY IDEMPOTENCY IS CRITICAL:
- OpenAI Realtime reconnects frequently
- Same intent can be received multiple times
- Without tracking, Zapier would create duplicate events
- We use intent_id as idempotency key

ARCHITECTURE:
  IntentService (validated) → ExecutionService → Zapier Webhook
                                    ↓
                           Track in state store
                                    ↓
                           Prevent duplicates
"""

import httpx
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
from app.core.config import settings
from app.services.intent_service import CalendarEventIntent, ValidationResult

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status tracking."""
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class ExecutionResult:
    """Result of Zapier webhook execution."""
    
    def __init__(
        self,
        success: bool,
        status: ExecutionStatus,
        intent_id: str,
        zapier_response: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        is_duplicate: bool = False,
    ):
        self.success = success
        self.status = status
        self.intent_id = intent_id
        self.zapier_response = zapier_response or {}
        self.error = error
        self.is_duplicate = is_duplicate
        self.executed_at = datetime.utcnow().isoformat() if success else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "status": self.status.value,
            "intent_id": self.intent_id,
            "zapier_response": self.zapier_response,
            "error": self.error,
            "is_duplicate": self.is_duplicate,
            "executed_at": self.executed_at,
        }
    
    def to_tool_result(self) -> Dict[str, Any]:
        """
        Convert to OpenAI Realtime tool result format.
        
        This is sent back to the model so it knows the outcome.
        """
        if self.success:
            return {
                "success": True,
                "message": "Appointment created and confirmation email sent successfully.",
                "appointment_id": self.intent_id,
                "calendar_link": self.zapier_response.get("calendar_link"),
                "email_sent": True,
            }
        elif self.is_duplicate:
            return {
                "success": True,
                "message": "This appointment was already created.",
                "appointment_id": self.intent_id,
                "is_duplicate": True,
            }
        else:
            return {
                "success": False,
                "error": self.error or "Failed to create appointment",
                "retry_allowed": True,
            }


class ExecutionService:
    """
    Zapier webhook execution service with idempotency.
    
    CRITICAL RESPONSIBILITIES:
    1. Check if intent was already executed (prevent duplicates)
    2. Execute Zapier webhook call server-side
    3. Track execution status
    4. Handle failures with proper logging
    5. Return structured result for OpenAI Realtime
    """
    
    def __init__(self):
        # In-memory execution tracking (use Redis in production)
        # Key: intent_id, Value: ExecutionResult
        self._executions: Dict[str, ExecutionResult] = {}
        
        # Lock to prevent race conditions
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Zapier configuration
        self.webhook_url = settings.ZAPIER_WEBHOOK_URL
        self.api_key = settings.ZAPIER_API_KEY
        
        if not self.webhook_url:
            logger.warning("⚠️ ZAPIER_WEBHOOK_URL not configured")
    
    def _get_lock(self, intent_id: str) -> asyncio.Lock:
        """Get or create a lock for an intent ID."""
        if intent_id not in self._locks:
            self._locks[intent_id] = asyncio.Lock()
        return self._locks[intent_id]
    
    async def execute_calendar_intent(
        self,
        intent: CalendarEventIntent,
    ) -> ExecutionResult:
        """
        Execute a validated calendar intent via Zapier webhook.
        
        WHY WE USE LOCKS:
        - Realtime can send rapid-fire messages
        - Same intent might arrive twice before first finishes
        - Lock ensures one execution at a time per intent_id
        
        Args:
            intent: Validated CalendarEventIntent from IntentService
            
        Returns:
            ExecutionResult with success/failure status
        """
        intent_id = intent.intent_id or "unknown"
        
        # Get lock for this intent to prevent race conditions
        lock = self._get_lock(intent_id)
        
        async with lock:
            # STEP 1: Check for duplicate
            if intent_id in self._executions:
                existing = self._executions[intent_id]
                if existing.status in [ExecutionStatus.EXECUTED, ExecutionStatus.EXECUTING]:
                    logger.info(f"🔄 Duplicate intent detected, skipping: {intent_id}")
                    return ExecutionResult(
                        success=True,
                        status=ExecutionStatus.DUPLICATE,
                        intent_id=intent_id,
                        is_duplicate=True,
                    )
            
            # STEP 2: Mark as executing
            self._executions[intent_id] = ExecutionResult(
                success=False,
                status=ExecutionStatus.EXECUTING,
                intent_id=intent_id,
            )
            
            # STEP 3: Execute Zapier webhook
            try:
                result = await self._call_zapier_webhook(intent)
                
                # STEP 4: Mark as executed and store result
                self._executions[intent_id] = result
                
                return result
                
            except Exception as e:
                # STEP 5: Handle failure
                error_msg = str(e)
                logger.error(f"❌ Zapier execution failed: {error_msg}")
                
                result = ExecutionResult(
                    success=False,
                    status=ExecutionStatus.FAILED,
                    intent_id=intent_id,
                    error=error_msg,
                )
                self._executions[intent_id] = result
                
                return result
    
    async def _call_zapier_webhook(
        self,
        intent: CalendarEventIntent,
    ) -> ExecutionResult:
        """
        Make the actual HTTP request to Zapier webhook.
        
        WHY THIS IS SERVER-SIDE ONLY:
        - Browsers cannot make cross-origin requests to Zapier
        - API keys must stay on server
        - Server can log all calls for debugging
        - Server can implement retry logic
        """
        if not self.webhook_url:
            raise ValueError("ZAPIER_WEBHOOK_URL not configured")
        
        # Convert intent to Zapier payload
        payload = intent.to_zapier_payload()
        
        logger.info(f"📤 Executing Zapier webhook for intent: {intent.intent_id}")
        logger.info(f"   Title: {intent.title}")
        logger.info(f"   Attendees: {intent.attendees}")
        logger.info(f"   Start: {intent.start_time}")
        logger.debug(f"   Full payload: {json.dumps(payload, indent=2)}")
        
        # Headers for Zapier
        headers = {
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.webhook_url,
                headers=headers,
                json=payload,
            )
            
            # Log response
            logger.info(f"📥 Zapier response status: {response.status_code}")
            
            # Check for success
            if response.status_code not in [200, 201, 202]:
                error_text = response.text
                logger.error(f"❌ Zapier returned non-2xx: {response.status_code}")
                logger.error(f"   Response: {error_text}")
                
                raise Exception(f"Zapier returned {response.status_code}: {error_text}")
            
            # Parse response
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                # Zapier sometimes returns non-JSON on success
                response_json = {"status": "accepted", "raw": response.text}
            
            logger.info(f"✅ Zapier webhook executed successfully")
            logger.debug(f"   Response: {json.dumps(response_json, indent=2)}")
            
            return ExecutionResult(
                success=True,
                status=ExecutionStatus.EXECUTED,
                intent_id=intent.intent_id or "unknown",
                zapier_response=response_json,
            )
    
    def get_execution_status(self, intent_id: str) -> Optional[ExecutionResult]:
        """Get the execution status of an intent."""
        return self._executions.get(intent_id)
    
    def was_executed(self, intent_id: str) -> bool:
        """Check if an intent was already executed."""
        result = self._executions.get(intent_id)
        if not result:
            return False
        return result.status in [ExecutionStatus.EXECUTED, ExecutionStatus.DUPLICATE]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for debugging."""
        total = len(self._executions)
        by_status = {}
        
        for result in self._executions.values():
            status = result.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_executions": total,
            "by_status": by_status,
            "recent_executions": [
                {
                    "intent_id": r.intent_id,
                    "status": r.status.value,
                    "success": r.success,
                    "executed_at": r.executed_at,
                }
                for r in list(self._executions.values())[-10:]
            ],
        }
    
    def reset_execution(self, intent_id: str) -> bool:
        """
        Reset execution status for an intent (allows retry).
        
        Use with caution - this allows duplicate Zapier calls.
        """
        if intent_id in self._executions:
            del self._executions[intent_id]
            if intent_id in self._locks:
                del self._locks[intent_id]
            logger.info(f"🔄 Reset execution status for: {intent_id}")
            return True
        return False


# Singleton instance
execution_service = ExecutionService()

