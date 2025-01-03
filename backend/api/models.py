from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SQLAEnum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime
from .database import Base

class LLMProvider(enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class CognitiveLevelEnum(enum.Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    llm_provider = Column(SQLAEnum(LLMProvider), default=LLMProvider.OPENAI)
    encrypted_openai_key = Column(String)  # Will store encrypted key as base64
    encrypted_anthropic_key = Column(String)  # Will store encrypted key as base64
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topics = relationship("Topic", back_populates="user")
    blueprints = relationship("Blueprint", back_populates="user")

class Topic(Base):
    __tablename__ = "topics"
    
    topic_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="topics")
    blueprints = relationship("Blueprint", back_populates="topic")
    terminal_objectives = relationship("TerminalObjective", back_populates="topic", cascade="all, delete-orphan")

class TerminalObjective(Base):
    __tablename__ = "terminal_objectives"
    
    terminal_objective_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    cognitive_level = Column(SQLAEnum(CognitiveLevelEnum), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.topic_id"))
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("blueprints.blueprint_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    enabling_objectives = relationship("EnablingObjective", back_populates="terminal_objective", cascade="all, delete-orphan")
    topic = relationship("Topic", back_populates="terminal_objectives")
    blueprint = relationship("Blueprint", back_populates="terminal_objectives")

class EnablingObjective(Base):
    __tablename__ = "enabling_objectives"
    
    enabling_objective_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    number = Column(String(10), nullable=False)  # e.g., "1.1", "2.3"
    description = Column(Text, nullable=False)
    cognitive_level = Column(SQLAEnum(CognitiveLevelEnum), nullable=False)
    terminal_objective_id = Column(UUID(as_uuid=True), ForeignKey("terminal_objectives.terminal_objective_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    terminal_objective = relationship("TerminalObjective", back_populates="enabling_objectives")

class Blueprint(Base):
    """
    SQLAlchemy model for Blueprint that matches the Pydantic schema in models.schemas.
    """
    __tablename__ = "blueprints"
    
    blueprint_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.topic_id"), nullable=False)
    content = Column(JSON, nullable=True)
    output_folder = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    terminal_objectives_count = Column(Integer, nullable=False, default=0)
    enabling_objectives_count = Column(Integer, nullable=False, default=0)

    # Relationships
    user = relationship("User", back_populates="blueprints")
    topic = relationship("Topic", back_populates="blueprints")
    terminal_objectives = relationship("TerminalObjective", back_populates="blueprint", cascade="all, delete-orphan")

    def update_objective_counts(self):
        """Update the counts of terminal and enabling objectives."""
        self.terminal_objectives_count = len(self.terminal_objectives)
        self.enabling_objectives_count = sum(len(to.enabling_objectives) for to in self.terminal_objectives)
