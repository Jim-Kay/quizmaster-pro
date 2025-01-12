from datetime import datetime
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, constr
from enum import Enum
from .base import TimestampedModel

class CognitiveLevelEnum(str, Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

class LLMProvider(str, Enum):
    openai = "openai"
    anthropic = "anthropic"

# Custom field types
EnablingObjectiveNumber = Annotated[
    str,
    Field(description="The enabling objective number (e.g., '2.3')."),
    constr(pattern=r'^[0-9]+\.[0-9]+$')
]

ObjectiveNumber = Annotated[
    str,
    Field(description="Objective numbers (e.g., '2.3')."),
    constr(pattern=r'^[0-9]+(\.[0-9]+)?$')
]

DistractorsType = Annotated[
    List[str],
    Field(min_length=3, max_length=3)
]

DistractorExplanationsType = Annotated[
    List[str],
    Field(min_length=3, max_length=3)
]

class Topic(TimestampedModel):
    id: Optional[str] = Field(default=None)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EnablingObjective(TimestampedModel):
    id: Optional[str] = Field(default=None)
    number: EnablingObjectiveNumber
    description: str = Field(..., min_length=10)
    cognitive_level: CognitiveLevelEnum
    terminal_objective_id: str

    model_config = ConfigDict(from_attributes=True)

class TerminalObjective(TimestampedModel):
    id: Optional[str] = Field(default=None)
    number: int = Field(..., description="The terminal objective number (e.g., 1, 2).")
    description: str = Field(..., min_length=10)
    cognitive_level: CognitiveLevelEnum
    topic_id: str
    enabling_objectives: List[EnablingObjective] = []

    model_config = ConfigDict(from_attributes=True)

class QuestionOption(BaseModel):
    text: str
    is_correct: bool
    explanation: str
    references: Optional[List[str]] = Field(default_factory=list)

class Question(TimestampedModel):
    id: Optional[str] = Field(default=None)
    question_number: int
    stem: str = Field(..., min_length=10)
    correct_answer: str
    distractors: DistractorsType
    objective_numbers: List[ObjectiveNumber]
    cognitive_level: CognitiveLevelEnum
    correct_answer_explanation: str
    distractor_explanations: DistractorExplanationsType
    references: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class Assessment(TimestampedModel):
    id: Optional[str] = Field(default=None)
    topic_id: str
    questions: List[Question] = []

    model_config = ConfigDict(from_attributes=True)

class AssessmentSession(TimestampedModel):
    id: Optional[str] = Field(default=None)
    user_id: str
    assessment_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class UserResponse(TimestampedModel):
    id: Optional[str] = Field(default=None)
    assessment_session_id: str
    question_id: str
    selected_option_index: int
    is_correct: bool
    time_taken_seconds: float

    model_config = ConfigDict(from_attributes=True)

class User(TimestampedModel):
    """User model for authentication and preferences."""
    id: Optional[str] = Field(default=None)
    email: str = Field(..., max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    llm_provider: LLMProvider = Field(default=LLMProvider.openai)
    encrypted_openai_key: Optional[str] = None
    encrypted_anthropic_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class Blueprint(TimestampedModel):
    """
    Source of truth for Blueprint schema across frontend and backend.
    This model is used to:
    1. Generate TypeScript types for frontend
    2. Validate API responses
    3. Integrate with SQLAlchemy ORM
    """
    id: Optional[str] = Field(default=None)
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    topic_id: str
    created_by: str
    terminal_objectives: List[TerminalObjective] = []
    output_folder: Optional[str] = None
    terminal_objectives_count: Optional[int] = Field(default=0)
    enabling_objectives_count: Optional[int] = Field(default=0)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Next.js Fundamentals",
                "description": "Core concepts and features of Next.js",
                "topic_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_by": "123e4567-e89b-12d3-a456-426614174002",
                "terminal_objectives": [],
                "terminal_objectives_count": 0,
                "enabling_objectives_count": 0
            }
        }
    )

# Request/Response Models
class TopicCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)

class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)

class AssessmentBlueprintCreate(BaseModel):
    topic_id: str
    terminal_objectives: List[str] = Field(..., min_length=1, max_length=10)
    enabling_objectives_per_terminal: int = Field(..., ge=5, le=8)

class AssessmentSessionCreate(BaseModel):
    assessment_id: str

class UserResponseCreate(BaseModel):
    question_id: str
    selected_option_index: int
    time_taken_seconds: float
