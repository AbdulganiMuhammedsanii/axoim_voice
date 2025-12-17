"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/voice_agent_db"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Zapier Integration (handles Google Calendar and Email via webhooks)
    ZAPIER_API_KEY: str = ""
    ZAPIER_WEBHOOK_URL: str = ""  # Full webhook URL from Zapier
    
    # Redis (optional, for state management)
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False  # Set to True to use Redis instead of in-memory state
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

