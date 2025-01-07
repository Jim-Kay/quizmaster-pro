"""Application configuration"""

import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "quizmaster"
    TEST_DB_NAME: str = "quizmaster_test"
    
    # API
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    NEXTAUTH_SECRET: str
    ENCRYPTION_KEY: str
    
    # Feature flags
    MOCK_AUTH: bool = False
    
    # External APIs
    SERPER_API_KEY: Optional[str] = None
    
    # Python settings
    PYTHONIOENCODING: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        # Allow extra fields from environment variables
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    # Check if we're in test mode
    env_file = ".env"
    if os.getenv("TEST_MODE") == "true":
        env_file = ".env.test"
    
    return Settings(_env_file=env_file)

# Export get_settings function
__all__ = ["get_settings"]
