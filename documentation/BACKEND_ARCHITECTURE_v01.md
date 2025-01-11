# Backend Architecture Guide

This document describes the architecture of the QuizMaster Pro backend and provides guidelines for organizing code and managing dependencies.

## Directory Structure

```
backend/
  api/
    core/           # Core modules and shared components
      __init__.py   # Package exports
      base.py       # SQLAlchemy Base class and shared mixins
      config.py     # Application settings
      database.py   # Database connection and session management
      models.py     # SQLAlchemy model definitions
    routers/        # API route handlers
      __init__.py
      topics.py
      blueprints.py
      ...
    flows/          # AI flow implementations
      flow_wrapper.py
      sample_poem_flow/
      write_a_book_with_flows/
    crews/          # AI crew implementations
      blueprint_crew/
      poem_crew/
    auth.py         # Authentication utilities
    main.py         # FastAPI application
```

## Core Module

The `core` module is the foundation of our backend architecture. It contains shared components and base functionality that other modules depend on.

### Key Components

1. **base.py**: SQLAlchemy Base class and shared mixins
   ```python
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy import Column, DateTime
   from datetime import datetime
   
   # Create base class for SQLAlchemy models
   Base = declarative_base()
   
   # Common mixins for model functionality
   class TimestampMixin:
       """Add created_at and updated_at timestamps to models"""
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   
   class SoftDeleteMixin:
       """Add soft delete capability to models"""
       deleted_at = Column(DateTime, nullable=True)
       
       @property
       def is_deleted(self) -> bool:
           return self.deleted_at is not None
   ```

2. **models.py**: Actual model definitions using Base and mixins
   ```python
   from datetime import datetime
   from typing import Optional, List
   from sqlalchemy import Column, Integer, String, ForeignKey
   from sqlalchemy.orm import relationship
   
   from .base import Base, TimestampMixin
   
   class User(Base, TimestampMixin):
       """User model for authentication and ownership"""
       __tablename__ = "users"
       
       id = Column(Integer, primary_key=True)
       email = Column(String, unique=True)
       # ... rest of model definition
   
   class Topic(Base, TimestampMixin):
       """Topic model for organizing content"""
       __tablename__ = "topics"
       
       id = Column(Integer, primary_key=True)
       title = Column(String)
       user_id = Column(Integer, ForeignKey("users.id"))
       # ... rest of model definition
   ```

## Import Guidelines

To avoid circular dependencies and maintain a clean architecture, follow these import guidelines:

1. **Core Module Imports**
   ```python
   # Good - Import from core module
   from api.core.config import get_settings
   from api.core.models import User
   from api.core.database import get_db
   
   # Bad - Direct imports that bypass core
   from api.models import User  # Don't do this
   from api.database import get_db  # Don't do this
   ```

2. **Router Imports**
   ```python
   # Good - Relative imports for router components
   from .schemas import UserCreate
   from ..core.models import User
   from ..auth import get_current_user
   
   # Bad - Absolute imports within the package
   from api.schemas import UserCreate  # Don't do this
   ```

3. **Flow and Crew Imports**
   ```python
   # Good - Relative imports within flows/crews
   from .crews.poem_crew import PoemCrew
   from ..core.models import FlowExecution
   
   # Bad - Deep imports from other modules
   from api.routers.schemas import FlowResponse  # Don't do this
   ```

## Refactoring Guide

Follow these steps to refactor existing code to use the new structure:

1. **Move Model Definitions**
   - Move all SQLAlchemy models to `core/models.py`
   - Update imports to use `from api.core.models import ...`
   - Remove old model files

2. **Update Database Access**
   - Use `get_db` from `core/database.py`
   - Update connection strings to use settings from `core/config.py`
   - Remove direct database access code from other modules

3. **Reorganize Routes**
   - Keep route handlers in `routers/` directory
   - Use relative imports for dependencies
   - Group related endpoints in the same router file

4. **Fix Circular Dependencies**
   ```python
   # Before - Circular dependency
   # models.py
   from .database import Base
   # database.py
   from .models import User
   
   # After - No circular dependency
   # core/base.py
   Base = declarative_base()
   # core/models.py
   from .base import Base
   # core/database.py
   from .base import Base
   ```

## Best Practices

1. **Dependency Injection**
   - Use FastAPI's dependency injection system
   - Inject database sessions and current user
   ```python
   @router.get("/items")
   async def get_items(
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       pass
   ```

2. **Schema Separation**
   - Keep Pydantic schemas in router-specific `schemas.py` files
   - Use relative imports for schemas
   ```python
   # routers/topics/schemas.py
   from pydantic import BaseModel
   
   class TopicCreate(BaseModel):
       title: str
       description: str
   ```

3. **Error Handling**
   - Use FastAPI's exception handling
   - Create custom exceptions in `core/exceptions.py`
   ```python
   from fastapi import HTTPException
   
   if not topic:
       raise HTTPException(
           status_code=404,
           detail="Topic not found"
       )
   ```

4. **Configuration Management**
   - Store all configuration in `core/config.py`
   - Use environment variables with Pydantic validation
   - Cache settings with `@lru_cache`

## Testing

1. **Test Organization**
   ```
   tests/
   ├── verified/                # Verified and documented tests
   │   ├── infrastructure/     # Infrastructure and database tests
   │   ├── core/              # Core functionality tests
   │   ├── integration/       # Integration tests
   │   └── documentation/     # Test documentation files
   ├── unit/                  # Simple unit tests using pytest
   │   ├── backend/          # Backend unit tests
   │   └── frontend/         # Frontend unit tests
   └── uncategorized/        # Supporting test files and configurations
       ├── config/           # Test configuration files
       ├── data/            # Test data files and fixtures
       └── logs/            # Test log directory
   ```

2. **Test Documentation Requirements**
   Each test file must include a header comment with:
   ```python
   """
   Test Name: [Test name]
   Description: [Brief description]

   Test Metadata:
       Level: [Test level 0-4]
       Dependencies: [List of dependent tests]
       Blocking: [True/False]
       Parallel_Safe: [True/False]
       Estimated_Duration: [Time in seconds]
       Working_Directory: [Directory to run from]
       Required_Paths: [List of required files/directories]

   Environment:
       - Conda Environment: [environment name]
       - Required Services: [list of required services]

   Setup:
       1. [Setup step 1]
       2. [Setup step 2]

   Execution:
       [Command to run the test]

   Expected Results:
       [Success criteria]

   Notes:
       [Additional information, warnings, or special considerations]
   """
   ```

3. **Test Categories**
   - **Infrastructure Tests**: Database connectivity, session management, connection pooling
   - **Core Tests**: User authentication, API endpoints, data validation
   - **Integration Tests**: End-to-end workflows, complex user scenarios

4. **Mock User Management**
   The test suite maintains two types of test users:
   - **Mock User (Persistent)**:
     - Fixed UUID: f9b5645d-898b-4d58-b10a-a6b50a9d234b
     - Never deleted
     - Used for authentication tests
   - **Test User (Temporary)**:
     - Dynamic UUID
     - Created/deleted per test
     - Used for CRUD operations

5. **Test Execution Guidelines**
   ```bash
   # Set environment variables
   set TEST_MODE=true
   set PYTHONPATH=/path/to/backend
   set POSTGRES_USER=test_user
   set POSTGRES_PASSWORD=test_password
   set POSTGRES_HOST=localhost
   set POSTGRES_PORT=5432

   # Run infrastructure tests
   pytest tests/verified/infrastructure/ -v

   # Run core tests
   pytest tests/verified/core/ -v

   # Run integration tests
   pytest tests/verified/integration/ -v
   ```

6. **Test Dependencies**
   Required packages are specified in `requirements.txt`:
   - fastapi==0.109.0
   - pydantic==2.10.4
   - SQLAlchemy==2.0.36
   - pytest-asyncio==0.23.3
   - python-multipart>=0.0.7

## Common Issues and Solutions

1. **Circular Import Errors**
   ```python
   # Problem: Circular import between models and database
   # Solution: Move shared base classes to core/base.py
   from api.core.base import Base
   ```

2. **Import Path Issues**
   ```python
   # Problem: Inconsistent import paths
   # Solution: Use relative imports within package
   from ..core.models import User  # Good
   from api.core.models import User  # Avoid in package
   ```

3. **Configuration Access**
   ```python
   # Problem: Direct environment variable access
   # Solution: Use settings from core.config
   from api.core.config import get_settings
   
   settings = get_settings()
   database_url = settings.DATABASE_URL
   ```

## Migration Checklist

- [ ] Move models to `core/models.py`
- [ ] Update database configuration
- [ ] Fix import statements
- [ ] Update router organization
- [ ] Add type hints
- [ ] Update tests
- [ ] Verify no circular dependencies
- [ ] Update documentation

## Questions and Support

For questions about the architecture or help with refactoring, please:
1. Check this documentation first
2. Review the example code in `routers/topics.py`
3. Run the import checker: `python scripts/check_imports.py`
4. Create an issue if you need further assistance
