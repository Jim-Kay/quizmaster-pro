from datetime import datetime
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, constr, UUID4
from enum import Enum
import json
import os
import logging
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class CognitiveLevelEnum(str, Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

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

class EnablingObjectivePydantic(BaseModel):
    enabling_objective_id: UUID4 | None = None
    title: str = Field(..., min_length=3, max_length=255)
    number: EnablingObjectiveNumber
    description: str = Field(..., min_length=10)
    cognitive_level: CognitiveLevelEnum
    terminal_objective_id: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)

class TerminalObjectivePydantic(BaseModel):
    terminal_objective_id: UUID4 | None = None
    title: str = Field(..., min_length=3, max_length=255)
    number: int = Field(..., description="The terminal objective number (e.g., 1, 2).")
    description: str = Field(..., min_length=10)
    cognitive_level: CognitiveLevelEnum
    topic_id: UUID4 | None = None
    enabling_objectives: List[EnablingObjectivePydantic] = []
    model_config = ConfigDict(from_attributes=True)

class BlueprintPydantic(BaseModel):
    """Source of truth for Blueprint schema across frontend and backend.
    This model is used to:
    1. Generate TypeScript types for frontend
    2. Validate API responses
    3. Save blueprint data to files
    """
    blueprint_id: UUID4 | None = None
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    topic_id: UUID4 | None = None
    created_by: UUID4 | None = None
    terminal_objectives: List[TerminalObjectivePydantic] = []
    output_folder: Optional[str] = None
    file_path: Optional[str] = Field(None, description="Full path to the saved JSON file")
    terminal_objectives_count: Optional[int] = Field(default=0)
    enabling_objectives_count: Optional[int] = Field(default=0)
    status: str = Field(default="draft")
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "blueprint_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Next.js Fundamentals",
                "description": "Core concepts and features of Next.js",
                "topic_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_by": "123e4567-e89b-12d3-a456-426614174002",
                "terminal_objectives": [],
                "terminal_objectives_count": 0,
                "enabling_objectives_count": 0,
                "status": "draft"
            }
        }
    )

    @classmethod
    def from_json_file(cls, file_path: str) -> "BlueprintPydantic":
        """Load a Blueprint instance from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing blueprint data
            
        Returns:
            Blueprint: A new Blueprint instance created from the JSON data
            
        Raises:
            FileNotFoundError: If the specified file does not exist
            JSONDecodeError: If the file contains invalid JSON
            ValidationError: If the JSON data does not match the Blueprint schema
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Blueprint file not found: {file_path}")
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating Blueprint from {file_path}: {str(e)}")
            raise

    def save_to_file(self, output_folder: str | None = None) -> str:
        """Save the blueprint to a JSON file.
        
        Args:
            output_folder: Optional output folder path. If not provided, uses self.output_folder.
            
        Returns:
            str: Path to the saved file
            
        Raises:
            ValueError: If no output folder is specified or if it's empty
            OSError: If there's an error creating the directory or writing the file
        """
        # Use provided output_folder or fall back to instance attribute
        folder = output_folder or self.output_folder
        if not folder:
            raise ValueError("No output folder specified")
            
        # Create output directory if it doesn't exist
        os.makedirs(folder, exist_ok=True)
            
        # Generate filename using blueprint_id
        filename = f"blueprint_{self.blueprint_id}.json"
        file_path = os.path.join(folder, filename)
            
        try:
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(self.model_dump(), f, indent=2, default=str)
                
            # Update file_path attribute
            self.file_path = file_path
            logger.info(f"Saved blueprint to {file_path}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving blueprint to {file_path}: {str(e)}")
            raise

    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization that handles UUID fields."""
        def handle_uuid(obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
        return json.dumps(self.model_dump(), default=handle_uuid, **kwargs)

class BlueprintStatusResponse(BaseModel):
    """Response model for blueprint status endpoint."""
    id: UUID4
    status: str = Field(..., description="Current status of the blueprint (draft, generating, completed, error)")
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    terminal_objectives_count: int = Field(default=0)
    enabling_objectives_count: int = Field(default=0)
    error_details: Optional[str] = Field(None, description="Detailed error information if status is 'error'")
    model_config = ConfigDict(from_attributes=True)

class QuestionOption(BaseModel):
    text: str
    is_correct: bool
    explanation: str
    references: Optional[List[str]] = Field(default_factory=list)

class Question(BaseModel):
    id: Optional[UUID4] = Field(default=None)
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

class Assessment(BaseModel):
    id: Optional[UUID4] = Field(default=None)
    topic_id: UUID4
    questions: List[Question] = []
    model_config = ConfigDict(from_attributes=True)

class AssessmentSession(BaseModel):
    id: Optional[UUID4] = Field(default=None)
    user_id: UUID4
    assessment_id: UUID4
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    score: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: Optional[UUID4] = Field(default=None)
    assessment_session_id: UUID4
    question_id: UUID4
    selected_option_index: int
    is_correct: bool
    time_taken_seconds: float
    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    """User model for authentication and preferences."""
    id: Optional[UUID4] = Field(default=None)
    email: str = Field(..., max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    encrypted_openai_key: Optional[str] = None
    encrypted_anthropic_key: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Request/Response Models
class TopicCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)

class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)

class AssessmentBlueprintCreate(BaseModel):
    topic_id: UUID4
    terminal_objectives: List[UUID4] = Field(..., min_length=1, max_length=10)
    enabling_objectives_per_terminal: int = Field(..., ge=5, le=8)

class AssessmentSessionCreate(BaseModel):
    assessment_id: UUID4

class UserResponseCreate(BaseModel):
    question_id: UUID4
    selected_option_index: int
    time_taken_seconds: float

class Topic(BaseModel):
    id: Optional[UUID4] = Field(default=None)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    user_id: Optional[UUID4] = None
    model_config = ConfigDict(from_attributes=True)
