"""
Intent Validation Service - Strict Schema Enforcement for Realtime Tool Calls

This service is the CRITICAL validation layer between OpenAI Realtime API responses
and Zapier webhook execution.

WHY THIS EXISTS:
- OpenAI Realtime may emit partial/malformed JSON
- Natural language responses must NEVER trigger Zapier calls
- All fields must be strictly validated before execution
- This prevents the classic bug: "model thinks it did the thing"

ARCHITECTURE:
  OpenAI Realtime → Tool Call → IntentService (VALIDATE) → ExecutionService → Zapier
                                      ↓
                              (Reject if invalid)
"""

import re
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError

logger = logging.getLogger(__name__)


class IntentAction(str, Enum):
    """Supported intent actions - explicit enum prevents unknown actions."""
    CREATE_CALENDAR_EVENT = "create_calendar_event"
    ESCALATE_CALL = "escalate_call"
    COMPLETE_INTAKE = "complete_intake"
    END_CALL = "end_call"


class CalendarEventIntent(BaseModel):
    """
    Strict schema for calendar event creation.
    
    This is the ONLY accepted format for scheduling actions.
    The model MUST emit this exact structure - no variations allowed.
    """
    action: str = Field(..., description="Must be 'create_calendar_event'")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(default="", description="Event description")
    start_time: str = Field(..., description="ISO-8601 datetime string")
    end_time: str = Field(..., description="ISO-8601 datetime string")
    timezone: str = Field(default="UTC", description="IANA timezone string")
    attendees: List[str] = Field(..., min_length=1, description="List of attendee emails")
    send_email: bool = Field(default=True, description="Whether to send email invitations")
    
    # Optional fields for tracking
    intent_id: Optional[str] = Field(default=None, description="Unique intent ID for idempotency")
    call_id: Optional[str] = Field(default=None, description="Associated call ID")
    org_id: Optional[str] = Field(default=None, description="Organization ID")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v != IntentAction.CREATE_CALENDAR_EVENT.value:
            raise ValueError(f"Action must be '{IntentAction.CREATE_CALENDAR_EVENT.value}'")
        return v
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_iso8601(cls, v: str) -> str:
        """Validate ISO-8601 datetime format."""
        try:
            # Try parsing with timezone
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO-8601 datetime: {v}. Expected format: YYYY-MM-DDTHH:MM:SSZ")
    
    @field_validator('attendees')
    @classmethod
    def validate_attendees(cls, v: List[str]) -> List[str]:
        """Validate all attendee emails."""
        if not v:
            raise ValueError("At least one attendee email is required")
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        validated = []
        for email in v:
            email = email.strip().lower()
            if not re.match(email_regex, email):
                raise ValueError(f"Invalid email format: {email}")
            validated.append(email)
        return validated
    
    def to_zapier_payload(self) -> Dict[str, Any]:
        """
        Convert to Zapier webhook payload format.
        
        Returns exactly what Zapier expects - no extra fields.
        """
        return {
            "appointment_id": self.intent_id,
            "title": self.title,
            "description": self.description or "",
            "start_time": self.start_time,
            "end_time": self.end_time,
            "timezone": self.timezone,
            "attendee_email": self.attendees[0],  # Primary attendee
            "attendee_name": "",  # Can be enriched if available
            "additional_attendees": self.attendees[1:] if len(self.attendees) > 1 else [],
            "send_email": self.send_email,
            "created_at": datetime.utcnow().isoformat(),
        }


class ValidationResult(BaseModel):
    """Result of intent validation."""
    is_valid: bool
    intent: Optional[CalendarEventIntent] = None
    errors: List[str] = Field(default_factory=list)
    raw_input: Optional[Dict[str, Any]] = None


class IntentService:
    """
    Intent extraction and validation service.
    
    CRITICAL RESPONSIBILITIES:
    1. Parse tool call arguments safely (handles malformed JSON)
    2. Validate all required fields exist
    3. Validate field types and formats
    4. Reject anything that doesn't match strict schema
    5. Generate structured error messages for retry
    """
    
    def __init__(self):
        # Track validation failures for debugging
        self._validation_failures: List[Dict[str, Any]] = []
    
    def validate_calendar_intent(
        self,
        tool_args: Dict[str, Any],
        call_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate a calendar event intent from Realtime tool call.
        
        Args:
            tool_args: Raw arguments from OpenAI Realtime tool call
            call_id: Associated call ID for tracking
            org_id: Organization ID
            
        Returns:
            ValidationResult with validated intent or errors
        """
        logger.info(f"🔍 Validating calendar intent: {json.dumps(tool_args, default=str)}")
        
        errors: List[str] = []
        
        # STEP 1: Check required fields exist
        required_fields = ["title", "start_time", "end_time", "attendee_email"]
        missing_fields = []
        
        for field in required_fields:
            if field not in tool_args or not tool_args.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.warning(f"❌ {error_msg}")
            errors.append(error_msg)
            return ValidationResult(
                is_valid=False,
                errors=errors,
                raw_input=tool_args,
            )
        
        # STEP 2: Transform to strict schema format
        # Handle both "attendee_email" (single) and "attendees" (list) formats
        attendees = tool_args.get("attendees", [])
        if not attendees and tool_args.get("attendee_email"):
            attendees = [tool_args["attendee_email"]]
        
        # Generate DETERMINISTIC intent ID for idempotency
        # Same appointment details = same ID = duplicate prevention
        import hashlib
        idempotency_key = f"{tool_args.get('title')}|{tool_args.get('start_time')}|{tool_args.get('end_time')}|{attendees[0] if attendees else ''}"
        intent_id = tool_args.get("intent_id") or hashlib.sha256(idempotency_key.encode()).hexdigest()[:16]
        logger.info(f"🔑 Generated idempotency key: {intent_id} from {idempotency_key}")
        
        normalized_data = {
            "action": IntentAction.CREATE_CALENDAR_EVENT.value,
            "title": tool_args.get("title", ""),
            "description": tool_args.get("description", ""),
            "start_time": tool_args.get("start_time", ""),
            "end_time": tool_args.get("end_time", ""),
            "timezone": tool_args.get("timezone", "UTC"),
            "attendees": attendees,
            "send_email": tool_args.get("send_email", True),
            "intent_id": intent_id,
            "call_id": call_id,
            "org_id": org_id,
        }
        
        # STEP 3: Validate with Pydantic model (strict validation)
        try:
            intent = CalendarEventIntent(**normalized_data)
            logger.info(f"✅ Intent validated successfully: {intent.title} for {intent.attendees}")
            
            return ValidationResult(
                is_valid=True,
                intent=intent,
                errors=[],
                raw_input=tool_args,
            )
            
        except ValidationError as e:
            # Extract human-readable error messages
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                errors.append(f"{field}: {msg}")
            
            logger.warning(f"❌ Validation failed: {errors}")
            self._validation_failures.append({
                "timestamp": datetime.utcnow().isoformat(),
                "input": tool_args,
                "errors": errors,
            })
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                raw_input=tool_args,
            )
    
    def parse_tool_call_safely(self, raw_data: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Safely parse tool call data - handles string JSON or dict.
        
        WHY THIS EXISTS:
        - Realtime API sometimes sends JSON as string
        - Partial responses may be malformed
        - This prevents JSON parse errors from crashing the pipeline
        
        Returns:
            Tuple of (parsed_data, error_message)
        """
        if raw_data is None:
            return None, "Tool call data is None"
        
        if isinstance(raw_data, dict):
            return raw_data, None
        
        if isinstance(raw_data, str):
            try:
                # Handle potential escape issues
                cleaned = raw_data.strip()
                if not cleaned:
                    return None, "Empty tool call data"
                
                parsed = json.loads(cleaned)
                if not isinstance(parsed, dict):
                    return None, f"Expected object, got {type(parsed).__name__}"
                
                return parsed, None
                
            except json.JSONDecodeError as e:
                return None, f"Invalid JSON: {str(e)}"
        
        return None, f"Unexpected data type: {type(raw_data).__name__}"
    
    def generate_clarification_message(self, validation_result: ValidationResult) -> str:
        """
        Generate a message for the AI to ask for missing/invalid fields.
        
        This is sent back to OpenAI Realtime as a tool result, prompting
        the model to ask the user for the missing information.
        """
        if validation_result.is_valid:
            return ""
        
        error_summary = "; ".join(validation_result.errors)
        
        return (
            f"VALIDATION_FAILED: Cannot create appointment. {error_summary}. "
            "Please ask the user to provide the missing or correct information."
        )
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics for debugging."""
        return {
            "total_failures": len(self._validation_failures),
            "recent_failures": self._validation_failures[-10:],  # Last 10 failures
        }


# Singleton instance
intent_service = IntentService()

