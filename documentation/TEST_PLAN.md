# QuizMasterPro Test Plan

## Test Organization Structure

```
tests/
├── unit/                     # Simple unit tests using pytest
│   ├── backend/             # Backend unit tests
│   └── frontend/            # Frontend unit tests
├── integration/             # Integration tests (non-pytest)
│   ├── api/                 # API integration tests
│   ├── flows/               # Flow execution tests
│   └── e2e/                 # End-to-end tests
├── verified/                # Verified and documented tests
│   ├── unit/
│   ├── integration/
│   └── documentation/       # Test documentation files
└── uncategorized/          # Supporting test files and configurations
    ├── config/             # Test configuration files (e.g., conftest.py)
    ├── data/              # Test data files and fixtures
    ├── requirements/      # Test-specific requirements files
    └── logs/              # Test log directory
```

## Test Categories

### Unit Tests
- Use pytest framework
- Test individual components in isolation
- Quick execution time
- No external dependencies
- Located in `tests/unit/`

### Integration Tests
- Custom test frameworks
- Test component interactions
- May require external services
- Located in `tests/integration/`

### End-to-End Tests
- Full system tests
- Require complete environment setup
- Located in `tests/integration/e2e/`

## Test Documentation Requirements

Each test file must include a header comment with:

```python
"""
Test Name: [Test name]
Description: [Brief description of what is being tested]

Environment:
    - Conda Environment: [environment name]
    - Working Directory: [directory to run from]
    - Required Services: [list of required services]

Setup:
    1. [Setup step 1]
    2. [Setup step 2]

Execution:
    [Command to run the test]

Expected Results:
    [What constitutes a successful test run]
"""
```

## Verified Tests Process

1. Tests must meet these criteria to be moved to verified/:
   - Complete header documentation
   - Successful execution verified
   - Clear pass/fail criteria
   - Consistent results across multiple runs

2. Verification Process:
   - Document test according to template
   - Review by another team member
   - Three successful test runs
   - Move to verified/ directory

## Test Execution Guidelines

1. Unit Tests:
   ```bash
   # Backend unit tests
   conda activate quiz_master_backend
   cd backend/
   pytest tests/unit/

   # Frontend unit tests
   cd frontend/
   npm test
   ```

2. Integration Tests:
   ```bash
   # API integration tests
   conda activate quiz_master_backend
   cd backend/api/
   python -m tests.integration.run_tests
   ```

## Test Execution Sequence

### Level 0: Infrastructure Tests
- Database connectivity and basic operations
- Backend server startup and health checks
- Frontend server startup and basic rendering
- Network connectivity between components

### Level 1: Core Service Tests
- User authentication and mock user setup
- Basic API endpoint availability
- WebSocket connectivity
- Frontend-Backend communication

### Level 2: Backend Feature Tests
1. User Management
   - User creation
   - Authentication flows
   - Permission checks

2. Quiz Core Features
   - Topic management
   - Question generation
   - Blueprint operations
   - Flow execution

3. Data Management
   - Database CRUD operations
   - Data validation
   - Error handling

### Level 3: Frontend Feature Tests
1. User Interface
   - Component rendering
   - Responsive design
   - Navigation

2. User Interactions
   - Form submissions
   - Real-time updates
   - Error displays

### Level 4: Integration Tests
- End-to-end workflows
- Complex user scenarios
- Performance tests
- Error recovery scenarios

### Test Execution Strategy

```python
test_sequence = {
    "level_0": {
        "priority": 0,
        "parallel": False,  # Run sequentially
        "blocking": True,   # Must pass to continue
        "tests": [
            "verified/infrastructure/test_database.py",
            "verified/infrastructure/test_backend_health.py",
            "verified/infrastructure/test_frontend_health.py"
        ]
    },
    "level_1": {
        "priority": 1,
        "parallel": False,
        "blocking": True,
        "tests": [
            "verified/core/test_auth.py",
            "verified/core/test_api_health.py",
            "verified/core/test_websocket.py"
        ]
    },
    "level_2": {
        "priority": 2,
        "parallel": True,  # Backend tests can run in parallel
        "blocking": True,
        "tests": [
            "verified/backend/user/*",
            "verified/backend/quiz/*",
            "verified/backend/data/*"
        ]
    },
    "level_3": {
        "priority": 3,
        "parallel": True,  # Frontend tests can run in parallel
        "blocking": False, # Non-blocking
        "tests": [
            "verified/frontend/ui/*",
            "verified/frontend/interaction/*"
        ]
    },
    "level_4": {
        "priority": 4,
        "parallel": False,
        "blocking": False,
        "tests": [
            "verified/integration/*"
        ]
    }
}
```

### Test Runner Implementation

1. Create a test runner that:
   - Reads test sequence configuration
   - Validates test dependencies
   - Manages test execution order
   - Handles parallel execution where allowed
   - Provides clear progress reporting
   - Stops on blocking test failures

2. Test File Requirements:
   ```python
   """
   Test Metadata:
       Level: [0-4]
       Dependencies: [list of test files this depends on]
       Blocking: [True/False]
       Parallel_Safe: [True/False]
       Estimated_Duration: [time in seconds]
   """
   ```

3. Execution Modes:
   - `quick`: Run only blocking tests (Levels 0-2)
   - `full`: Run all tests
   - `ci`: Run tests appropriate for CI environment
   - `pre-release`: Run all tests with extended validations

4. Reporting:
   - Real-time test status dashboard
   - Test dependency graph visualization
   - Execution time analytics
   - Failure impact analysis

### Test Maintenance

1. Regular Review Process:
   - Quarterly review of test sequence
   - Update test dependencies
   - Optimize execution order
   - Remove obsolete tests

2. Performance Monitoring:
   - Track test execution times
   - Identify bottlenecks
   - Optimize parallel execution
   - Maintain test execution SLAs

## Continuous Integration

- Unit tests run on every PR
- Integration tests run nightly
- E2E tests run before releases

## Test Maintenance

- Review and update tests quarterly
- Remove obsolete tests
- Update documentation as needed
- Verify all tests in verified/ still pass

### Next Steps
based on this TEST_PLAN.md, consider what the next test is that should be either moved from one of the subfolders of @tests into the @tests/verified  structure, or simply created fresh? 
