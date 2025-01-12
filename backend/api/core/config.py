"""Application configuration."""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

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
    environment_name: str = "development"
    environment_color: str = ENVIRONMENT_COLORS["development"]
    environment_description: str = ENVIRONMENT_DESCRIPTIONS["development"]
    
    # Database settings
    postgres_user: str = os.getenv("QUIZMASTER_POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("QUIZMASTER_POSTGRES_PASSWORD", "postgres")
    postgres_host: str = os.getenv("QUIZMASTER_POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("QUIZMASTER_POSTGRES_PORT", "5432")
    postgres_db: str = "quizmaster_dev"  # Will be set in model_config
    
    # API settings
    api_host: str = "localhost"
    api_port: int = 8000
    
    # Auth settings
    auth_secret: str = os.getenv("QUIZMASTER_AUTH_SECRET", "your-secret-key")
    auth_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 30
    
    # Python encoding
    pythonioencoding: Optional[str] = None
    
    model_config = ConfigDict(
        env_prefix="quizmaster_",
        case_sensitive=False,
        env_file=f".env.{os.getenv('QUIZMASTER_ENVIRONMENT', 'development')}",
        env_file_encoding='utf-8',
        extra="allow"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set environment-specific values
        env = os.getenv("QUIZMASTER_ENVIRONMENT", "development")
        self.environment_name = env
        self.environment_color = ENVIRONMENT_COLORS[env]
        self.environment_description = ENVIRONMENT_DESCRIPTIONS[env]
        self.postgres_db = DATABASE_NAMES[env]

    @property
    def database_url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

# Track the last environment used
_last_environment = None

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    global _last_environment
    current_env = os.getenv("QUIZMASTER_ENVIRONMENT", "development")
    
    # Clear cache if environment has changed
    if _last_environment is not None and _last_environment != current_env:
        get_settings.cache_clear()
    
    _last_environment = current_env
    return Settings()

# Export get_settings function and Settings class
__all__ = ["get_settings", "Settings"]
