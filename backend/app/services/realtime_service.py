"""
OpenAI Realtime API integration service.

This service handles creating Realtime sessions, configuring them with
system prompts and tools, and managing session lifecycle.
"""

import httpx
import json
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.prompt_service import get_system_prompt


class RealtimeService:
    """Service for managing OpenAI Realtime API sessions."""
    
    def __init__(self):
        # Strip whitespace/newlines from API key (common issue with env vars)
        self.api_key = settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""
        self.base_url = "https://api.openai.com/v1"  # GA API base URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Note: No OpenAI-Beta header needed for GA API
        }
    
    async def create_session(self, org_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an ephemeral client secret for OpenAI Realtime API (GA version).
        
        Args:
            org_config: Organization configuration dictionary
            
        Returns:
            Dictionary containing client_secret (ephemeral key starting with "ek_")
        """
        # Build system prompt with org-specific rules
        system_prompt = get_system_prompt(org_config)
        
        # Configure Realtime session using GA API format
        # The client_secrets endpoint only accepts minimal config
        # Instructions and tools will be sent via session.update after WebSocket connection
        minimal_session_config = {
            "session": {
                "type": "realtime",
                "model": "gpt-realtime",
                "audio": {
                    "output": {
                        "voice": "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer, marin, etc.
                    }
                }
            }
        }
        
        # Build full session config (instructions + tools) for session.update
        # Frontend will send this via session.update after WebSocket connection
        tools = [
                {
                    "type": "function",
                    "name": "escalate_call",
                    "description": "Escalate the call to a human agent. Use this when the caller needs immediate human assistance, mentions emergency keywords, or when you're uncertain about how to proceed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Reason for escalation (e.g., 'emergency', 'complex_issue', 'uncertainty')"
                            },
                            "urgency": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "emergency"],
                                "description": "Urgency level of the escalation"
                            },
                            "summary": {
                                "type": "string",
                                "description": "Brief summary of why escalation is needed"
                            }
                        },
                        "required": ["reason", "urgency", "summary"]
                    }
                },
                {
                    "type": "function",
                    "name": "complete_intake",
                    "description": "Mark the intake process as complete when all required information has been collected.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "structured_data": {
                                "type": "object",
                                "description": "Structured intake data in JSON format"
                            },
                            "urgency_level": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Urgency level based on collected information"
                            }
                        },
                        "required": ["structured_data", "urgency_level"]
                    }
                },
                {
                    "type": "function",
                    "name": "end_call",
                    "description": "End the call when the conversation is complete and no further action is needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Reason for ending the call"
                            }
                        },
                        "required": ["reason"]
                    }
                },
                {
                    "type": "function",
                    "name": "create_appointment",
                    "description": "Create an appointment, add it to Google Calendar, and send a confirmation email to the attendee. This tool performs three actions: 1) Saves the appointment to the database, 2) Creates a Google Calendar event with the attendee as a guest, 3) Sends a confirmation email via Zapier with meeting details and calendar link. You MUST call this tool when the caller wants to schedule an appointment. The tool validates the email address automatically. Required fields: title, start_time (ISO 8601), end_time (ISO 8601), and attendee_email.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Appointment title (e.g., 'Consultation with John Doe', 'Follow-up Appointment', 'Initial Assessment')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description or notes about the appointment"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO 8601 format with timezone (e.g., '2024-12-20T14:00:00Z' for UTC or '2024-12-20T14:00:00-05:00' for EST). Must include timezone."
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time in ISO 8601 format with timezone (e.g., '2024-12-20T15:00:00Z' for UTC or '2024-12-20T15:00:00-05:00' for EST). Must include timezone."
                            },
                            "attendee_email": {
                                "type": "string",
                                "description": "Email address of the attendee. This will be validated automatically. The calendar invitation and confirmation email will be sent to this address."
                            },
                            "attendee_name": {
                                "type": "string",
                                "description": "Name of the attendee (optional, but recommended for personalization)"
                            },
                            "timezone": {
                                "type": "string",
                                "description": "Timezone for the appointment (e.g., 'America/New_York', 'America/Los_Angeles', 'UTC'). Defaults to UTC if not specified. This is used for display purposes."
                            }
                        },
                        "required": ["title", "start_time", "end_time", "attendee_email"]
                    }
                }
        ]
        
        # Log tools being sent (for debugging)
        import logging
        logger = logging.getLogger(__name__)
        tool_names = [tool.get("name") for tool in tools if tool.get("type") == "function"]
        logger.info(f"🔧 Generating ephemeral key. Full config will include {len(tool_names)} tools: {tool_names}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Generate ephemeral client secret using GA API endpoint (minimal config only)
                response = await client.post(
                    f"{self.base_url}/realtime/client_secrets",
                    headers=self.headers,
                    json=minimal_session_config,
                )
                response.raise_for_status()
                result = response.json()
                
                # GA API returns ephemeral key in "value" field (starts with "ek_")
                client_secret = result.get("value", "")
                if not client_secret:
                    raise Exception("No ephemeral key returned from API")
                
                logger.info(f"✅ Ephemeral key generated: {client_secret[:20]}...")
                
                # Calculate expires_at (ephemeral keys typically expire in 1 hour)
                from datetime import datetime, timezone, timedelta
                expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                
                # Build full session config for frontend to send via session.update
                full_session_config = {
                    "instructions": system_prompt,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.8,
                    "max_response_output_tokens": 4096,
                }
                
                return {
                    "session_id": "",  # Not used in GA API - session is created on WebSocket connection
                    "client_secret": client_secret,
                    "expires_at": expires_at,
                    "session_config": full_session_config,  # Full config for session.update
                }
            except httpx.HTTPStatusError as e:
                error_text = e.response.text if hasattr(e.response, 'text') else str(e)
                logger.error(f"❌ Failed to generate ephemeral key: {error_text}")
                raise Exception(f"Failed to generate ephemeral key: {error_text}")
            except Exception as e:
                logger.error(f"❌ Error generating ephemeral key: {str(e)}")
                raise Exception(f"Error generating ephemeral key: {str(e)}")
    
# Singleton instance
realtime_service = RealtimeService()

