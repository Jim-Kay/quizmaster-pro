"""Environment configuration for QuizMasterPro."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class Environment(str, Enum):
    """Available environments."""
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"

class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    name: Environment
    database_name: str
    description: str
    color: str  # For UI indication

# Environment configurations
ENVIRONMENTS = {
    Environment.DEVELOPMENT: EnvironmentConfig(
        name=Environment.DEVELOPMENT,
        database_name="quizmaster",
        description="Development Environment",
        color="#2196F3"  # Blue
    ),
    Environment.TEST: EnvironmentConfig(
        name=Environment.TEST,
        database_name="quizmaster_test",
        description="Test Environment",
        color="#FF9800"  # Orange
    ),
    Environment.PRODUCTION: EnvironmentConfig(
        name=Environment.PRODUCTION,
        database_name="quizmaster",
        description="Production Environment",
        color="#4CAF50"  # Green
    )
}

def get_environment_config(env: Optional[str] = None) -> EnvironmentConfig:
    """Get environment configuration."""
    if not env:
        return ENVIRONMENTS[Environment.DEVELOPMENT]
    try:
        return ENVIRONMENTS[Environment(env.lower())]
    except (KeyError, ValueError):
        return ENVIRONMENTS[Environment.DEVELOPMENT]
