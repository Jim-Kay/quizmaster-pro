import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # JWT configuration
    jwt_secret: str = os.getenv("NEXTAUTH_SECRET", "development-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database configuration
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = os.getenv("POSTGRES_DB", "quizmaster")

    # Test database configuration
    test_db_name: str = os.getenv("TEST_DB_NAME", "test_db")

    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()
