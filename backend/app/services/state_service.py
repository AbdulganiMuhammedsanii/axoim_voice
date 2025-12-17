"""
State management service for call state and conversation phases.

Supports both in-memory (default) and Redis-based state storage.
"""

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from app.core.config import settings
import json


class ConversationPhase(str, Enum):
    """Conversation phase tracking."""
    GREETING = "greeting"
    INTAKE = "intake"
    CLARIFICATION = "clarification"
    ESCALATION = "escalation"
    COMPLETED = "completed"


class CallState:
    """In-memory call state storage."""
    
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
        self._cleanup_interval = timedelta(hours=24)  # Clean up states older than 24h
    
    def set_state(self, call_id: str, state: Dict[str, Any]) -> None:
        """Set call state."""
        state["updated_at"] = datetime.utcnow().isoformat()
        self._states[call_id] = state
    
    def get_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call state."""
        return self._states.get(call_id)
    
    def update_phase(self, call_id: str, phase: ConversationPhase) -> None:
        """Update conversation phase."""
        if call_id not in self._states:
            self._states[call_id] = {}
        self._states[call_id]["phase"] = phase.value
        self._states[call_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def get_phase(self, call_id: str) -> Optional[str]:
        """Get current conversation phase."""
        state = self.get_state(call_id)
        return state.get("phase") if state else None
    
    def add_transcript_item(self, call_id: str, speaker: str, text: str) -> None:
        """Add a transcript item to state (before persisting to DB)."""
        if call_id not in self._states:
            self._states[call_id] = {"transcripts": []}
        elif "transcripts" not in self._states[call_id]:
            self._states[call_id]["transcripts"] = []
        
        self._states[call_id]["transcripts"].append({
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def set_appointment_state(self, call_id: str, state: Dict[str, Any]) -> None:
        """Set appointment-related state for a call."""
        if call_id not in self._states:
            self._states[call_id] = {}
        self._states[call_id]["appointment"] = state
        self._states[call_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def get_appointment_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment state for a call."""
        state = self.get_state(call_id)
        return state.get("appointment") if state else None
    
    def update_appointment_field(self, call_id: str, field: str, value: Any) -> None:
        """Update a specific field in appointment state."""
        if call_id not in self._states:
            self._states[call_id] = {}
        if "appointment" not in self._states[call_id]:
            self._states[call_id]["appointment"] = {}
        self._states[call_id]["appointment"][field] = value
        self._states[call_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def mark_escalated(self, call_id: str, reason: str, urgency: str) -> None:
        """Mark call as escalated."""
        if call_id not in self._states:
            self._states[call_id] = {}
        self._states[call_id]["escalated"] = True
        self._states[call_id]["escalation_reason"] = reason
        self._states[call_id]["escalation_urgency"] = urgency
        self._states[call_id]["phase"] = ConversationPhase.ESCALATION.value
        self._states[call_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def delete_state(self, call_id: str) -> None:
        """Delete call state."""
        self._states.pop(call_id, None)
    
    def cleanup_old_states(self) -> None:
        """Clean up states older than cleanup_interval."""
        cutoff = datetime.utcnow() - self._cleanup_interval
        to_delete = []
        for call_id, state in self._states.items():
            updated_at_str = state.get("updated_at")
            if updated_at_str:
                updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                if updated_at < cutoff:
                    to_delete.append(call_id)
        for call_id in to_delete:
            self.delete_state(call_id)


# Global in-memory state (singleton)
_in_memory_state = CallState()


class StateService:
    """State management service with Redis support (optional)."""
    
    def __init__(self):
        self.use_redis = settings.USE_REDIS
        self.redis_client = None
        
        if self.use_redis:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except ImportError:
                print("Warning: redis not installed, falling back to in-memory state")
                self.use_redis = False
    
    async def set_state(self, call_id: str, state: Dict[str, Any]) -> None:
        """Set call state."""
        if self.use_redis and self.redis_client:
            await self.redis_client.setex(
                f"call_state:{call_id}",
                86400,  # 24 hours TTL
                json.dumps(state),
            )
        else:
            _in_memory_state.set_state(call_id, state)
    
    async def get_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call state."""
        if self.use_redis and self.redis_client:
            data = await self.redis_client.get(f"call_state:{call_id}")
            return json.loads(data) if data else None
        else:
            return _in_memory_state.get_state(call_id)
    
    async def update_phase(self, call_id: str, phase: ConversationPhase) -> None:
        """Update conversation phase."""
        state = await self.get_state(call_id) or {}
        state["phase"] = phase.value
        state["updated_at"] = datetime.utcnow().isoformat()
        await self.set_state(call_id, state)
    
    async def get_phase(self, call_id: str) -> Optional[str]:
        """Get current conversation phase."""
        state = await self.get_state(call_id)
        return state.get("phase") if state else None
    
    async def mark_escalated(self, call_id: str, reason: str, urgency: str) -> None:
        """Mark call as escalated."""
        state = await self.get_state(call_id) or {}
        state["escalated"] = True
        state["escalation_reason"] = reason
        state["escalation_urgency"] = urgency
        state["phase"] = ConversationPhase.ESCALATION.value
        state["updated_at"] = datetime.utcnow().isoformat()
        await self.set_state(call_id, state)
    
    async def delete_state(self, call_id: str) -> None:
        """Delete call state."""
        if self.use_redis and self.redis_client:
            await self.redis_client.delete(f"call_state:{call_id}")
        else:
            _in_memory_state.delete_state(call_id)


# Singleton instance
state_service = StateService()

