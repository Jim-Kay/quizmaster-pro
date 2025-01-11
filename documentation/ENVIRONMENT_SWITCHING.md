# Environment Switching System

QuizMasterPro implements a flexible environment switching system that allows developers to easily switch between different runtime environments (Development, Test, and Production). This document explains how the system works and how to use it.

## Overview

The environment switching system consists of three main components:

1. **Process Manager GUI** - A PowerShell-based GUI tool for managing application processes
2. **Environment Configuration** - Environment-specific configuration files for both frontend and backend
3. **Startup Scripts** - Environment-aware batch scripts for starting services

## Process Manager GUI

The Process Manager (`scripts/manage_processes.ps1`) provides a user-friendly interface for:

- Selecting the target environment (Development/Test/Production)
- Starting/stopping the backend server
- Starting/stopping the frontend development server
- Managing process windows and visibility

### Features

- **Environment Selection**: Radio buttons for choosing between Development, Test, and Production environments
- **Backend Control**: Start, stop, and focus buttons for managing the backend process
- **Frontend Control**: Start, stop, and focus buttons for managing the frontend process
- **Process Status**: Live status display showing process state and PIDs
- **Window Management**: Ability to bring process windows to front

## Environment Configuration

### Frontend Configuration
The frontend uses Next.js's built-in environment configuration system with environment-specific `.env` files:

1. `.env.development.local` (for development)
   ```env
   NEXTAUTH_URL=http://localhost:3000
   MOCK_AUTH=true
   NEXT_PUBLIC_MOCK_AUTH=true
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. `.env.test.local` (for testing)
   ```env
   NEXTAUTH_URL=http://localhost:3000
   MOCK_AUTH=true
   NEXT_PUBLIC_MOCK_AUTH=true
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_IS_TEST=true
   ```

3. `.env.production.local` (for production)
   ```env
   NEXTAUTH_URL=[production-url]
   MOCK_AUTH=false
   NEXT_PUBLIC_MOCK_AUTH=false
   OIDC_ISSUER_URL=[auth0-url]
   ```

Next.js automatically loads the appropriate environment file based on `NODE_ENV`:
- `development` → loads `.env.development.local`
- `test` → loads `.env.test.local`
- `production` → loads `.env.production.local`

### Backend Configuration
The backend uses environment-specific `.env` files that are copied to `.env` during startup:

1. `.env.development`
   ```env
   POSTGRES_DB=quizmaster_dev
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

2. `.env.test`
   ```env
   POSTGRES_DB=quizmaster_test
   DEBUG=true
   LOG_LEVEL=DEBUG
   TEST_MODE=true
   ```

3. `.env.production`
   ```env
   POSTGRES_DB=quizmaster
   DEBUG=false
   LOG_LEVEL=INFO
   ```

## Test Environment Configuration

The test environment is configured to support different levels of testing as defined in the test plan:

### Test Database
- Uses dedicated `quizmaster_test` database
- Automatically reset between test runs
- Contains mock data for testing

### Test User Management
- Persistent mock user with UUID: `f9b5645d-898b-4d58-b10a-a6b50a9d234b`
- Temporary test users created/deleted per test

### Test-Specific Settings
1. Backend (`.env.test`):
   ```env
   POSTGRES_DB=quizmaster_test
   TEST_MODE=true
   MOCK_AUTH=true
   TEST_USER_UUID=f9b5645d-898b-4d58-b10a-a6b50a9d234b
   ```

2. Frontend (`.env.test.local`):
   ```env
   NEXT_PUBLIC_MOCK_AUTH=true
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_IS_TEST=true
   ```

### Test Execution
Different test levels can be run using the test runner script:

1. Run all tests:
   ```bash
   ./scripts/run_tests.bat all
   ```

2. Run specific test levels:
   ```bash
   # Infrastructure tests only
   ./scripts/run_tests.bat infrastructure

   # Core tests only
   ./scripts/run_tests.bat core

   # Integration tests only
   ./scripts/run_tests.bat integration
   ```

The test runner script (`run_tests.bat`) handles:
1. Environment Setup
   - Activates conda environment
   - Sets `QUIZMASTER_ENVIRONMENT=test`
   - Sets `TEST_MODE=true`
   - Sets correct `PYTHONPATH`
   - Configures database variables

2. Service Lifecycle Management
   - Starts required services for integration tests
   - Checks for port availability before starting
   - Waits for services to be fully ready
   - Stops all services after tests complete
   - Uses health checks to confirm service readiness

3. Safety Checks
   - Verifies test database is not in use
   - Prevents running tests while services are active
   - Ensures consistent test environment
   - Handles service cleanup on test failure

4. Test Execution
   - Runs tests in the correct order
   - Reports test results clearly
   - Exits with appropriate status code
   - Manages service dependencies per test level

### Service Readiness
The test runner ensures services are ready before running tests:

1. Backend Service:
   - Starts the backend server
   - Waits for `/api/health` endpoint to respond
   - Maximum 30 attempts with 1-second intervals

2. Frontend Service:
   - Starts the Next.js development server
   - Waits for the main page to be accessible
   - Maximum 30 attempts with 1-second intervals

### Service Cleanup
Services are properly cleaned up in all scenarios:
- After successful test completion
- After test failures
- When tests are interrupted
- Uses `manage_processes.ps1` for reliable process termination

## Startup Process

When starting the application:

1. User selects environment in Process Manager (development/test/production)
2. For Frontend:
   - Sets `NEXT_PUBLIC_QUIZMASTER_ENVIRONMENT` environment variable
   - Next.js loads the corresponding `.env` file
   - Frontend starts with environment-specific settings

3. For Backend:
   - Copies `.env.[environment]` to `.env`
   - Sets `QUIZMASTER_ENVIRONMENT` environment variable
   - Backend starts with environment-specific settings

4. Environment Indicator in the UI shows current backend environment status via `/api/environment` endpoint

## Database Configuration

Each environment connects to a different database to maintain separation of data:

- **Development**: Uses `quizmaster_dev` database
  - For local development work
  - Can be freely modified without affecting other environments
  - Migrations can be tested here first

- **Test**: Uses `quizmaster_test` database
  - For QA and integration testing
  - Can be reset between test runs
  - Maintains consistent test data

- **Production**: Uses `quizmaster` database
  - For live application data
  - Requires careful handling of migrations
  - Backup procedures should be in place

The database connection is configured through environment-specific `.env` files in the backend:

1. `.env.development`
   ```env
   POSTGRES_DB=quizmaster_dev
   ```

2. `.env.test`
   ```env
   POSTGRES_DB=quizmaster_test
   ```

3. `.env.production`
   ```env
   POSTGRES_DB=quizmaster
   ```

## Best Practices

1. **Environment Variables**
   - Keep sensitive data in `.env` files
   - Never commit `.env` files to version control
   - Maintain `.env.example` files for reference

2. **Configuration Management**
   - Keep environment-specific settings in dedicated `.env.[environment]` files
   - Use environment variables for sensitive values
   - Implement reasonable defaults for development

3. **Process Management**
   - Always use the Process Manager to start/stop services
   - Check process status before starting new instances
   - Properly terminate processes to avoid orphaned instances

## Common Issues

1. **Process Already Running**
   - Use Process Manager's stop button to terminate existing processes
   - Check Task Manager for orphaned processes
   - Verify correct environment selection before starting

2. **Configuration Mismatch**
   - Ensure environment variables are properly set
   - Verify correct environment selection in Process Manager
   - Check that the correct `.env` file was copied for backend

3. **Window Management**
   - Use "Bring to Front" button if process window is hidden
   - Restart process if window becomes unresponsive
   - Check process status in Process Manager GUI
