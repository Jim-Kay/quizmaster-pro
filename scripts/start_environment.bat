@echo off
setlocal

:: Check for command line arguments
if not "%~1"=="" if not "%~2"=="" (
    call :PROCESS_ARGS %1 %2
    goto END
)

:ENV_MENU
cls
echo QuizMasterPro Environment Selector
echo ================================
echo.
echo Select Environment:
echo 1. Development Environment (quizmaster database)
echo 2. Test Environment (quizmaster_test database)
echo 3. Production Environment (quizmaster database)
echo.
echo Q. Quit
echo.
set /p env_choice="Select environment (1-3, Q to quit): "

if "%env_choice%"=="1" (
    set env=development
    goto COMPONENT_MENU
)
if "%env_choice%"=="2" (
    set env=test
    goto COMPONENT_MENU
)
if "%env_choice%"=="3" (
    set env=production
    goto COMPONENT_MENU
)
if /i "%env_choice%"=="Q" goto END

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto ENV_MENU

:COMPONENT_MENU
cls
echo.
echo Start Components for %env% Environment
echo ====================================
echo.
echo 1. Frontend Only
echo 2. Backend Only
echo 3. Both Frontend and Backend
echo.
echo B. Back to Environment Selection
echo Q. Quit
echo.
set /p comp_choice="Select components to start (1-3, B for back, Q to quit): "

call :START_COMPONENTS %comp_choice%
if errorlevel 1 (
    if /i "%comp_choice%"=="B" goto ENV_MENU
    if /i "%comp_choice%"=="Q" goto END
    echo Invalid choice. Please try again.
    timeout /t 2 >nul
    goto COMPONENT_MENU
)
goto END

:PROCESS_ARGS
set env_arg=%1
set comp_arg=%2

if "%env_arg%"=="1" (
    set env=development
) else if "%env_arg%"=="2" (
    set env=test
) else if "%env_arg%"=="3" (
    set env=production
) else (
    echo Invalid environment argument: %env_arg%
    echo Usage: start_environment.bat [env] [component]
    echo   env: 1=development, 2=test, 3=production
    echo   component: 1=frontend, 2=backend, 3=both
    exit /b 1
)

call :START_COMPONENTS %comp_arg%
if errorlevel 1 (
    echo Invalid component argument: %comp_arg%
    echo Usage: start_environment.bat [env] [component]
    echo   env: 1=development, 2=test, 3=production
    echo   component: 1=frontend, 2=backend, 3=both
    exit /b 1
)
exit /b 0

:START_COMPONENTS
if "%1"=="1" (
    echo.
    echo Starting Frontend in %env% environment...
    start cmd /k "title QuizMasterPro Frontend (%env%) && _start_frontend.bat %env%"
    exit /b 0
)
if "%1"=="2" (
    echo.
    echo Starting Backend in %env% environment...
    start cmd /k "title QuizMasterPro Backend (%env%) && _start_backend.bat %env%"
    exit /b 0
)
if "%1"=="3" (
    echo.
    echo Starting QuizMasterPro in %env% environment...
    start cmd /k "title QuizMasterPro Backend (%env%) && _start_backend.bat %env%"
    timeout /t 2 >nul
    start cmd /k "title QuizMasterPro Frontend (%env%) && _start_frontend.bat %env%"
    exit /b 0
)
exit /b 1

:END
endlocal
