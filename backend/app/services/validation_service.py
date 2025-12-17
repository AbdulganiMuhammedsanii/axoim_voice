"""
Validation service for user inputs.
"""

import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating user inputs."""
    
    # RFC 5322 compliant email regex (simplified but practical)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email address is required"
        
        email = email.strip().lower()
        
        # Basic length check
        if len(email) > 254:  # RFC 5321 limit
            return False, "Email address is too long"
        
        # Regex validation
        if not ValidationService.EMAIL_REGEX.match(email):
            return False, "Invalid email address format. Please provide a valid email like example@email.com"
        
        # Additional checks
        if email.startswith('.') or email.startswith('@'):
            return False, "Email address cannot start with . or @"
        
        if '..' in email:
            return False, "Email address cannot contain consecutive dots"
        
        return True, None
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email address (trim and lowercase)."""
        return email.strip().lower()


# Singleton instance
validation_service = ValidationService()

