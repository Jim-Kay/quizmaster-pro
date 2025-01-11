"""Application configuration."""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Import environment configuration
environment = os.getenv("QUIZMASTER_ENVIRONMENT", "development")

# Define database name based on environment
DATABASE_NAMES = {
    "development": "quizmaster_dev",
    "test": "quizmaster_test",
    "production": "quizmaster"
}

# Define environment colors for UI
ENVIRONMENT_COLORS = {
    "development": "#2196F3",  # Blue
    "test": "#FF9800",        # Orange
    "production": "#4CAF50"   # Green
}

# Define environment descriptions
ENVIRONMENT_DESCRIPTIONS = {
    "development": "Development Environment - For local development and testing",
    "test": "Test Environment - For QA and integration testing",
    "production": "Production Environment - Live system"
}

class Settings(BaseSettings):
    """Application settings."""
    # Environment settings
    environment: str = environment
    
    # Database settings
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = DATABASE_NAMES.get(environment, "quizmaster")
    
    # API settings
    api_host: str = "localhost"
    api_port: int = 8000
    
    # Auth settings
    auth_secret: str = os.getenv("AUTH_SECRET", "your-secret-key")
    auth_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 30
    
    # Python settings
    pythonioencoding: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def environment_name(self) -> str:
        """Get environment name."""
        return self.environment

    @property
    def environment_description(self) -> str:
        """Get environment description."""
        return ENVIRONMENT_DESCRIPTIONS.get(self.environment, "Unknown Environment")

    @property
    def environment_color(self) -> str:
        """Get environment color."""
        return ENVIRONMENT_COLORS.get(self.environment, "#9E9E9E")  # Default to gray

    class Config:
        """Pydantic config."""
        env_prefix="quizmaster_"
        case_sensitive=False
        env_file = ".env"
        env_file_encoding='utf-8'
        extra="allow"

@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()

# Export get_settings function and Settings class
__all__ = ["get_settings", "Settings"]
