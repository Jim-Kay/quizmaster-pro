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

The system uses environment-specific configuration files to manage settings for different environments. Each environment has its own database and configuration:

### Environment Types

1. **Development**
   - Database: `quizmaster_dev`
   - Color: Blue
   - Purpose: Local development and testing

2. **Test**
   - Database: `quizmaster_test`
   - Color: Orange
   - Purpose: Running automated tests and QA

3. **Production**
   - Database: `quizmaster`
   - Color: Green
   - Purpose: Live system

### Configuration Files

#### Backend Configuration
Environment-specific `.env` files in the backend directory:

1. `.env.development`
   ```env
   QUIZMASTER_POSTGRES_USER=test_user
   QUIZMASTER_POSTGRES_PASSWORD=test_password
   QUIZMASTER_POSTGRES_HOST=localhost
   QUIZMASTER_POSTGRES_PORT=5432
   QUIZMASTER_POSTGRES_DB=quizmaster_dev
   QUIZMASTER_ENVIRONMENT=development
   ```

2. `.env.test`
   ```env
   QUIZMASTER_POSTGRES_USER=test_user
   QUIZMASTER_POSTGRES_PASSWORD=test_password
   QUIZMASTER_POSTGRES_HOST=localhost
   QUIZMASTER_POSTGRES_PORT=5432
   QUIZMASTER_POSTGRES_DB=quizmaster_test
   QUIZMASTER_ENVIRONMENT=test
   QUIZMASTER_MOCK_AUTH=true
   ```

3. `.env.production`
   ```env
   QUIZMASTER_POSTGRES_USER=postgres
   QUIZMASTER_POSTGRES_PASSWORD=secure_password
   QUIZMASTER_POSTGRES_HOST=localhost
   QUIZMASTER_POSTGRES_PORT=5432
   QUIZMASTER_POSTGRES_DB=quizmaster
   QUIZMASTER_ENVIRONMENT=production
   ```

#### Frontend Configuration
The frontend uses Next.js's built-in environment configuration system with environment-specific `.env` files:

1. `.env.development.local`
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_ENVIRONMENT=development
   ```

2. `.env.test.local`
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_ENVIRONMENT=test
   NEXT_PUBLIC_IS_TEST=true
   ```

3. `.env.production.local`
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_ENVIRONMENT=production
   ```

## Environment Indicator

The system includes a visual environment indicator in the top-right corner of the UI that shows:
- Current environment name (e.g., "DEVELOPMENT")
- Current database name (e.g., "quizmaster_dev")
- Color-coded background based on environment
- Tooltip with additional details on hover

## Running Tests

When running tests:

1. The environment must be set to `test`:
   ```bash
   set QUIZMASTER_ENVIRONMENT=test
   ```

2. The test runner will verify:
   - Correct environment is set
   - Required environment variables are present
   - Database connection is available

3. All tests run against the `quizmaster_test` database to ensure isolation

## Best Practices

1. **Environment Selection**:
   - Use the Process Manager GUI to switch environments
   - Never mix development and test databases
   - Keep production configuration secure

2. **Database Usage**:
   - Development work should use `quizmaster_dev`
   - Tests should only use `quizmaster_test`
   - Production should use `quizmaster`

3. **Configuration Management**:
   - Keep sensitive data out of version control
   - Use environment-specific `.env` files
   - Follow the naming convention: `.env.<environment>`
