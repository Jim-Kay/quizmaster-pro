"""SQLAlchemy Base class and shared mixins"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, func
from datetime import datetime

# Create base class for SQLAlchemy models
Base = declarative_base()

class TimestampMixin:
    """Add created_at and updated_at timestamps to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SoftDeleteMixin:
    """Add soft delete capability to models"""
    deleted_at = Column(DateTime, nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
