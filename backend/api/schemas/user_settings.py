from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum

class LLMProvider(str, Enum):
    openai = "openai"
    anthropic = "anthropic"

class UserSettingsUpdate(BaseModel):
    llm_provider: Optional[LLMProvider] = None
    openai_key: Optional[str] = Field(None, min_length=1)
    anthropic_key: Optional[str] = Field(None, min_length=1)

class UserSettingsResponse(BaseModel):
    llm_provider: LLMProvider
    has_openai_key: bool
    has_anthropic_key: bool

    model_config = ConfigDict(from_attributes=True)
