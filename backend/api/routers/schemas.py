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

class TopicBase(BaseModel):
    title: str
    description: str | None = None

class TopicCreate(TopicBase):
    topic_id: UUID4 | None = None
    created_by: UUID4 | None = None

class TopicUpdate(TopicBase):
    pass

class TopicResponse(TopicBase):
    topic_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    """User model for authentication and preferences."""
    user_id: UUID4 | None = Field(default=None)
    email: str = Field(..., max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    encrypted_openai_key: Optional[str] = None
    encrypted_anthropic_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EnablingObjective(BaseModel):
    enabling_objective_id: UUID4 | None = None
    number: EnablingObjectiveNumber
    description: str = Field(..., min_length=10)
    cognitive_level: CognitiveLevelEnum
    terminal_objective_id: UUID4 | None = None

    model_config = ConfigDict(from_attributes=True)

class TerminalObjective(BaseModel):
    terminal_objective_id: UUID4 | None = None
    number: int = Field(..., description="The terminal objective number (e.g., 1, 2).")
    description: str = Field(..., min_length=10)
    cognitive_level: CognitiveLevelEnum
    topic_id: UUID4 | None = None
    enabling_objectives: List[EnablingObjective] = []

    model_config = ConfigDict(from_attributes=True)

class Blueprint(BaseModel):
    """Source of truth for Blueprint schema across frontend and backend.
    This model is used to:
    1. Generate TypeScript types for frontend
    2. Validate API responses
    3. Validate inputs to the blueprint generation process
    """
    blueprint_id: UUID4 | None = None
    title: str
    description: str
    status: str = Field(default="draft")
    created_at: datetime | None = None
    generation_started_at: datetime | None = None
    error_details: str | None = None
    created_by: UUID4 | None = None
    topic_id: UUID4 | None = None
    content: dict | None = None
    output_folder: str | None = None
    updated_at: datetime | None = None
    terminal_objectives_count: int = Field(default=0)
    enabling_objectives_count: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_json_file(cls, file_path: str) -> "Blueprint":
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
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Blueprint file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in blueprint file: {str(e)}", e.doc, e.pos)
        except Exception as e:
            raise ValueError(f"Error loading blueprint from file: {str(e)}")

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
        try:
            # Use provided output_folder or fall back to self.output_folder
            target_folder = output_folder or self.output_folder
            if not target_folder:
                raise ValueError("No output folder specified")
            
            logger.info(f"Preparing to save blueprint to folder: {target_folder}")
            
            # Create directory if it doesn't exist
            try:
                os.makedirs(target_folder, exist_ok=True)
                logger.info(f"Ensured output directory exists: {target_folder}")
            except Exception as e:
                logger.error(f"Failed to create output directory: {str(e)}")
                raise OSError(f"Failed to create output directory: {str(e)}")
            
            # Create the output file path
            blueprint_file = os.path.join(target_folder, 'blueprint_final.json')
            logger.info(f"Writing blueprint to file: {blueprint_file}")
            
            try:
                # Set the file_path attribute before saving
                self.file_path = os.path.abspath(blueprint_file)
                logger.debug(f"Set blueprint file_path to: {self.file_path}")
                
                # Generate JSON content
                json_content = self.model_dump_json(indent=2)
                logger.debug(f"Generated JSON content length: {len(json_content)} characters")
                
                # Write to file
                with open(blueprint_file, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                    logger.debug(f"Successfully wrote content to file")
                    f.flush()  # Ensure content is written to disk
                    os.fsync(f.fileno())  # Force write to disk
                
                # Verify file was written
                if os.path.exists(blueprint_file):
                    file_size = os.path.getsize(blueprint_file)
                    logger.info(f"Successfully wrote blueprint to file. Size: {file_size} bytes")
                    return blueprint_file
                else:
                    raise FileNotFoundError(f"Failed to verify blueprint file creation: {blueprint_file}")
                    
            except Exception as e:
                logger.error(f"Failed to write blueprint file: {str(e)}")
                raise OSError(f"Failed to write blueprint file: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in save_to_file: {str(e)}")
            raise

    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization that handles UUID fields."""
        data = self.model_dump()
        # Convert UUIDs to strings
        if data.get('blueprint_id'):
            data['blueprint_id'] = str(data['blueprint_id'])
        if data.get('topic_id'):
            data['topic_id'] = str(data['topic_id'])
        if data.get('created_by'):
            data['created_by'] = str(data['created_by'])

        # Handle UUIDs in terminal objectives
        for obj in data.get('terminal_objectives', []):
            if obj.get('terminal_objective_id'):
                obj['terminal_objective_id'] = str(obj['terminal_objective_id'])
            if obj.get('topic_id'):
                obj['topic_id'] = str(obj['topic_id'])
            # Handle UUIDs in enabling objectives
            for eo in obj.get('enabling_objectives', []):
                if eo.get('enabling_objective_id'):
                    eo['enabling_objective_id'] = str(eo['enabling_objective_id'])
                if eo.get('terminal_objective_id'):
                    eo['terminal_objective_id'] = str(eo['terminal_objective_id'])

        return json.dumps(data, **kwargs)

class BlueprintStatus(BaseModel):
    """Status of a blueprint generation process."""
    blueprint_id: UUID4
    status: str = Field(description="Current status of the blueprint (generating, completed, error)")
    title: str
    description: str
    terminal_objectives_count: int = Field(default=0)
    enabling_objectives_count: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)
