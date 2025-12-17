"""
Zapier integration service for appointment scheduling.

This service sends appointment data to Zapier webhooks which then:
1. Creates Google Calendar events
2. Sends confirmation emails

No manual OAuth setup required - Zapier handles all authentication.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZapierService:
    """Service for sending appointment data to Zapier webhooks."""
    
    def __init__(self):
        self.api_key = settings.ZAPIER_API_KEY
        self.webhook_url = settings.ZAPIER_WEBHOOK_URL
        self.base_url = "https://hooks.zapier.com/hooks/catch"
    
    def is_configured(self) -> bool:
        """Check if Zapier service is configured."""
        return bool(self.webhook_url or self.api_key)
    
    async def create_appointment_via_zapier(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendee_email: str,
        attendee_name: Optional[str] = None,
        description: Optional[str] = None,
        timezone: str = "UTC",
        appointment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send appointment data to Zapier webhook.
        
        Zapier will handle:
        1. Creating Google Calendar event
        2. Sending confirmation email
        
        Args:
            title: Appointment title
            start_time: Start time in ISO 8601 format
            end_time: End time in ISO 8601 format
            attendee_email: Email address of attendee
            attendee_name: Name of attendee (optional)
            description: Appointment description (optional)
            timezone: Timezone (default: UTC)
            appointment_id: Internal appointment ID for tracking
            
        Returns:
            Dict with success status and any returned data from Zapier
        """
        if not self.is_configured():
            raise ValueError("Zapier webhook URL not configured")
        
        # Prepare payload for Zapier webhook
        payload = {
            "appointment_id": appointment_id,
            "title": title,
            "description": description or "",
            "start_time": start_time,
            "end_time": end_time,
            "timezone": timezone,
            "attendee_email": attendee_email,
            "attendee_name": attendee_name or "",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"📤 Sending appointment to Zapier webhook: {title} for {attendee_email}")
        logger.debug(f"   Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Determine webhook URL
            webhook_url = self.webhook_url
            if not webhook_url and self.api_key:
                # If only API key provided, construct webhook URL
                # Format: https://hooks.zapier.com/hooks/catch/{webhook_id}/
                # For now, we'll require the full webhook URL in config
                raise ValueError("ZAPIER_WEBHOOK_URL must be set in environment variables")
            
            # Headers for Zapier webhook
            headers = {
                "Content-Type": "application/json",
            }
            
            # If using Zapier API key authentication (for some webhook types)
            if self.api_key and not webhook_url.startswith("http"):
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                result = response.json() if response.content else {}
                
                logger.info(f"✅ Zapier webhook called successfully")
                logger.debug(f"   Response: {json.dumps(result, indent=2)}")
                
                return {
                    "success": True,
                    "webhook_response": result,
                    "status_code": response.status_code,
                }
                
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"❌ Zapier webhook failed with status {e.response.status_code}: {error_text}")
            raise Exception(f"Zapier webhook failed: {error_text}")
        except httpx.RequestError as e:
            logger.error(f"❌ Zapier webhook request failed: {str(e)}")
            raise Exception(f"Failed to call Zapier webhook: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error calling Zapier webhook: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")


# Singleton instance
zapier_service = ZapierService()

