@echo off
setlocal EnableDelayedExpansion

REM Parse command line arguments
set "TEST_LEVEL=%1"
if "%1"=="" set "TEST_LEVEL=all"

REM Set environment variables
set "QUIZMASTER_ENVIRONMENT=test"
set "TEST_MODE=true"
set "PYTHONPATH=%~dp0..\backend"

REM Database configuration
set "POSTGRES_USER=postgres"
set "POSTGRES_PASSWORD=postgres"
set "POSTGRES_HOST=localhost"
set "POSTGRES_PORT=5432"
set "POSTGRES_DB=quizmaster_test"

REM Service ports
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3000"

REM Activate conda environment
call conda activate crewai-quizmaster-pro

REM Change to project root
cd %~dp0..

REM Function to check if a port is in use
:check_port
netstat -ano | findstr ":%~1" > nul
if %ERRORLEVEL% equ 0 (
    echo Port %~1 is in use
    exit /b 1
)
exit /b 0

REM Function to wait for service readiness
:wait_for_service
set "url=%~1"
set "max_attempts=%~2"
set "attempt=0"

:retry
set /a "attempt+=1"
curl -s %url% > nul
if !ERRORLEVEL! equ 0 (
    echo Service at %url% is ready
    exit /b 0
)
if !attempt! lss !max_attempts! (
    echo Waiting for service to be ready... Attempt !attempt!/%~2
    timeout /t 1 /nobreak > nul
    goto retry
)
echo Service failed to start after %~2 attempts
exit /b 1

REM Function to start services
:start_services
if "%~1"=="integration" (
    REM Check if ports are already in use
    call :check_port %BACKEND_PORT%
    if !ERRORLEVEL! neq 0 (
        echo Backend port is already in use. Please stop any running services first.
        exit /b 1
    )
    call :check_port %FRONTEND_PORT%
    if !ERRORLEVEL! neq 0 (
        echo Frontend port is already in use. Please stop any running services first.
        exit /b 1
    )

    REM Start backend
    echo Starting backend service...
    start "QuizMaster Backend" cmd /c "cd backend && uvicorn api.main:app --reload --port %BACKEND_PORT%"
    
    REM Wait for backend to be ready
    call :wait_for_service "http://localhost:%BACKEND_PORT%/api/health" 30
    if !ERRORLEVEL! neq 0 (
        echo Backend failed to start
        call :stop_services
        exit /b 1
    )

    REM Start frontend
    echo Starting frontend service...
    start "QuizMaster Frontend" cmd /c "cd frontend && npm run dev -- -p %FRONTEND_PORT%"
    
    REM Wait for frontend to be ready
    call :wait_for_service "http://localhost:%FRONTEND_PORT%" 30
    if !ERRORLEVEL! neq 0 (
        echo Frontend failed to start
        call :stop_services
        exit /b 1
    )
)
exit /b 0

REM Function to stop services
:stop_services
echo Stopping services...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage_processes.ps1" -Stop
exit /b 0

REM Function to run tests with proper setup
:run_tests
echo Running %~1 tests...
pytest %~2 -v
set "TEST_RESULT=!ERRORLEVEL!"
if !TEST_RESULT! neq 0 (
    echo Test suite %~1 failed
    exit /b !TEST_RESULT!
)
exit /b 0

REM Check if any services are using the test database
echo Checking for active database connections...
psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '%POSTGRES_DB%';" > temp.txt
set /p CONNECTIONS=<temp.txt
del temp.txt

if %CONNECTIONS% gtr 1 (
    echo Warning: Test database is currently in use by other processes
    echo Please stop any services running in the test environment before running tests
    exit /b 1
)

REM Start services if needed
call :start_services "%TEST_LEVEL%"
if !ERRORLEVEL! neq 0 exit /b !ERRORLEVEL!

REM Run tests based on level
if "%TEST_LEVEL%"=="infrastructure" (
    call :run_tests "Infrastructure" "tests/verified/infrastructure/"
) else if "%TEST_LEVEL%"=="core" (
    call :run_tests "Core" "tests/verified/core/"
) else if "%TEST_LEVEL%"=="integration" (
    call :run_tests "Integration" "tests/verified/integration/"
) else if "%TEST_LEVEL%"=="all" (
    echo Running all test suites...
    call :run_tests "Infrastructure" "tests/verified/infrastructure/"
    call :run_tests "Core" "tests/verified/core/"
    call :run_tests "Integration" "tests/verified/integration/"
) else (
    echo Invalid test level specified
    echo Usage: run_tests.bat [infrastructure^|core^|integration^|all]
    exit /b 1
)

REM Store the test result
set "FINAL_RESULT=!ERRORLEVEL!"

REM Always stop services before exiting
call :stop_services

if !FINAL_RESULT! neq 0 (
    echo Tests failed with error code !FINAL_RESULT!
    exit /b !FINAL_RESULT!
)

echo All tests completed successfully
endlocal
