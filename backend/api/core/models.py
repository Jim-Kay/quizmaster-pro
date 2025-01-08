"""SQLAlchemy models"""

import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum, UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin

# Enums
class LLMProvider(str, enum.Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class FlowExecutionStatus(str, enum.Enum):
    """Flow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class LogLevel(str, enum.Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

# Models
class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    
    # Settings
    llm_provider = Column(SQLAlchemyEnum(LLMProvider, name="llm_provider_enum"), default=LLMProvider.OPENAI)
    encrypted_openai_key = Column(String, nullable=True)
    encrypted_anthropic_key = Column(String, nullable=True)
    
    # Relationships
    topics = relationship("Topic", back_populates="user")
    flow_executions = relationship("FlowExecution", back_populates="user")

class Topic(Base, TimestampMixin):
    """Topic model"""
    __tablename__ = "topics"
    
    topic_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    
    # Relationships
    user = relationship("User", back_populates="topics")
    blueprints = relationship("Blueprint", back_populates="topic")

class Blueprint(Base, TimestampMixin):
    """Learning blueprint model"""
    __tablename__ = "blueprints"
    
    blueprint_id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.topic_id"))
    title = Column(String)
    description = Column(Text)
    
    # Relationships
    topic = relationship("Topic", back_populates="blueprints")
    terminal_objectives = relationship("TerminalObjective", back_populates="blueprint")

class TerminalObjective(Base, TimestampMixin):
    """Terminal learning objective model"""
    __tablename__ = "terminal_objectives"
    
    terminal_objective_id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.blueprint_id"))
    title = Column(String)
    description = Column(Text)
    
    # Relationships
    blueprint = relationship("Blueprint", back_populates="terminal_objectives")
    enabling_objectives = relationship("EnablingObjective", back_populates="terminal_objective")

class EnablingObjective(Base, TimestampMixin):
    """Enabling learning objective model"""
    __tablename__ = "enabling_objectives"
    
    enabling_objective_id = Column(Integer, primary_key=True, index=True)
    terminal_objective_id = Column(Integer, ForeignKey("terminal_objectives.terminal_objective_id"))
    title = Column(String)
    description = Column(Text)
    
    # Relationships
    terminal_objective = relationship("TerminalObjective", back_populates="enabling_objectives")

class FlowExecution(Base, TimestampMixin):
    """Flow execution model"""
    __tablename__ = "flow_executions"
    
    flow_execution_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    flow_id = Column(String)
    status = Column(SQLAlchemyEnum(FlowExecutionStatus, name="flow_status_enum"), default=FlowExecutionStatus.PENDING)
    error = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="flow_executions")
    logs = relationship("FlowLog", back_populates="flow_execution")

class FlowLog(Base, TimestampMixin):
    """Flow execution log model"""
    __tablename__ = "flow_logs"
    
    flow_log_id = Column(Integer, primary_key=True, index=True)
    flow_execution_id = Column(Integer, ForeignKey("flow_executions.flow_execution_id"))
    level = Column(SQLAlchemyEnum(LogLevel, name="log_level_enum"), default=LogLevel.INFO)
    message = Column(Text)
    
    # Relationships
    flow_execution = relationship("FlowExecution", back_populates="logs")
