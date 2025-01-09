"""Application settings and configuration."""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # 30 minutes
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = "quizmaster"
    TEST_DB_NAME: str = "quizmaster_test"
    
    # Test Settings
    TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"
    MOCK_AUTH: bool = os.getenv("MOCK_AUTH", "false").lower() == "true"
    
    # Security Settings
    NEXTAUTH_SECRET: str = os.getenv("NEXTAUTH_SECRET", "")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # API Keys
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        extra = "allow"

# Create settings instance
settings = Settings()