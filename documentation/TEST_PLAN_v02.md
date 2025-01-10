# QuizMasterPro Test Plan v2.0

## Test Organization Structure

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

## Test Categories and Best Practices

### Infrastructure Tests
- Database connectivity and session management
- Use SQLAlchemy async session management
- Proper connection pooling and cleanup
- Located in `tests/verified/infrastructure/`

#### Database Session Management
```python
@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine with proper connection pooling"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10
    )
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest.fixture(scope="function")
async def test_session(async_session_maker):
    """Create a fresh session for each test with proper cleanup"""
    async with session_maker() as session:
        async with session.begin():
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
```

### Core Tests
- User authentication and authorization
- API endpoint functionality
- Data validation and processing
- Located in `tests/verified/core/`

### Integration Tests
- End-to-end workflows
- Complex user scenarios
- Located in `tests/verified/integration/`

## Test Documentation Requirements

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

## Mock User Management

The test suite maintains two types of test users:

1. Mock User (Persistent):
   - Fixed UUID: f9b5645d-898b-4d58-b10a-a6b50a9d234b
   - Never deleted
   - Used for authentication tests
   - Provides consistent test environment

2. Test User (Temporary):
   - Dynamic UUID
   - Created/deleted per test
   - Used for CRUD operations
   - Cleaned up after tests

## Test Execution Sequence

### Level 0: Infrastructure Tests
```python
test_sequence = {
    "level_0": {
        "priority": 0,
        "parallel": False,
        "blocking": True,
        "tests": [
            "verified/infrastructure/test_database.py",
            "verified/infrastructure/test_db_init.py"
        ]
    }
}
```

### Level 1: Core Service Tests
```python
test_sequence = {
    "level_1": {
        "priority": 1,
        "parallel": False,
        "blocking": True,
        "tests": [
            "verified/core/test_auth.py",
            "verified/core/test_api_health.py"
        ]
    }
}
```

## Test Execution Guidelines

1. Infrastructure Tests:
   ```bash
   # Set environment variables
   set TEST_MODE=true
   set PYTHONPATH=/path/to/backend
   set POSTGRES_USER=test_user
   set POSTGRES_PASSWORD=test_password
   set POSTGRES_HOST=localhost
   set POSTGRES_PORT=5432

   # Run tests
   pytest tests/verified/infrastructure/ -v
   ```

2. Core Tests:
   ```bash
   pytest tests/verified/core/ -v
   ```

3. Integration Tests:
   ```bash
   pytest tests/verified/integration/ -v
   ```

## Dependency Management

Required packages and versions are specified in `requirements.txt`:
- fastapi==0.109.0
- pydantic==2.10.4
- SQLAlchemy==2.0.36
- pytest-asyncio==0.23.3
- python-multipart>=0.0.7

## Warning Management

The test suite handles various deprecation warnings:

1. Pydantic Models:
   - Use `ConfigDict` instead of class-based config
   - Use `min_length`/`max_length` instead of `min_items`/`max_items`

2. SQLAlchemy:
   - Use proper async session management
   - Ensure connection cleanup
   - Handle Windows-specific asyncpg warnings

3. Third-party Warnings:
   - Document and track external package warnings
   - Update dependencies when fixes are available

## Continuous Integration

1. Pre-commit Checks:
   - Code formatting (black)
   - Import sorting (isort)
   - Type checking (mypy)
   - Linting (flake8)

2. Test Sequence:
   - Run Level 0 tests first
   - Run Core tests if Level 0 passes
   - Run Integration tests last

## Future Improvements

1. Test Coverage:
   - Add more integration tests
   - Improve error scenario coverage
   - Add performance benchmarks

2. Infrastructure:
   - Containerize test environment
   - Add distributed testing support
   - Implement test result analytics
