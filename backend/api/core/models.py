"""SQLAlchemy models"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, ForeignKey, DateTime, 
    Enum as SQLAEnum, JSON, Integer, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, TimestampMixin

# Enums
class LLMProvider(str, Enum):
    """LLM provider enum"""
    openai = "openai"
    anthropic = "anthropic"

    @classmethod
    def _get_enum_name(cls):
        return 'llmprovider'  # Match the enum type name in the database

    def __str__(self):
        return self.value

class CognitiveLevelEnum(str, Enum):
    """Cognitive level enum"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

class FlowExecutionStatus(str, Enum):
    """Flow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

# Models
class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    
    # Settings
    llm_provider = Column(SQLAEnum(LLMProvider, native_enum=False), default=LLMProvider.openai)
    encrypted_openai_key = Column(String)  # Will store encrypted key as base64
    encrypted_anthropic_key = Column(String)  # Will store encrypted key as base64
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topics = relationship("Topic", back_populates="user")
    blueprints = relationship("Blueprint", back_populates="user")
    flow_executions = relationship("FlowExecution", back_populates="user")
    idempotency_keys = relationship("IdempotencyKey", back_populates="user")

class Topic(Base, TimestampMixin):
    """Topic model"""
    __tablename__ = "topics"
    
    topic_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="topics")
    blueprints = relationship("Blueprint", back_populates="topic")
    terminal_objectives = relationship("TerminalObjective", back_populates="topic", cascade="all, delete-orphan")

class Blueprint(Base, TimestampMixin):
    """Blueprint model"""
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

class TerminalObjective(Base, TimestampMixin):
    """Terminal objective model"""
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

class EnablingObjective(Base, TimestampMixin):
    """Enabling objective model"""
    __tablename__ = "enabling_objectives"
    
    enabling_objective_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    number = Column(String(10), nullable=False)
    description = Column(Text, nullable=False)
    cognitive_level = Column(SQLAEnum(CognitiveLevelEnum), nullable=False)
    terminal_objective_id = Column(UUID(as_uuid=True), ForeignKey("terminal_objectives.terminal_objective_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    terminal_objective = relationship("TerminalObjective", back_populates="enabling_objectives")

class FlowExecution(Base, TimestampMixin):
    """Flow execution model"""
    __tablename__ = "flow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_name = Column(String(255), nullable=False)
    status = Column(SQLAEnum(FlowExecutionStatus), nullable=False, default=FlowExecutionStatus.PENDING)
    state = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    log_file = Column(String(255), nullable=True)
    cache_key = Column(String(255), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="flow_executions")
    logs = relationship("FlowLog", back_populates="flow_execution", cascade="all, delete-orphan")

class IdempotencyKey(Base, TimestampMixin):
    """Model for storing idempotency keys to prevent duplicate flow executions."""
    __tablename__ = "idempotency_keys"
    
    key = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("flow_executions.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=1))
    
    # Indexes
    __table_args__ = (
        Index("idx_idempotency_keys_user_id", "user_id"),
        Index("idx_idempotency_keys_created_at", "created_at"),
    )
    
    # Relationships
    user = relationship("User", back_populates="idempotency_keys")

class FlowLog(Base, TimestampMixin):
    """Flow log model"""
    __tablename__ = "flow_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("flow_executions.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default='now()')
    level = Column(SQLAEnum(LogLevel, name='loglevel'), nullable=False)
    message = Column(Text, nullable=False)
    log_metadata = Column(JSONB)
    
    # Relationships
    flow_execution = relationship("FlowExecution", back_populates="logs")

    def to_dict(self):
        """Convert log entry to dictionary."""
        return {
            'id': str(self.id),
            'execution_id': str(self.execution_id),
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'metadata': self.log_metadata
        }
