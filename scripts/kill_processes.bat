@echo off
setlocal

:: Check for command line argument
if not "%~1"=="" (
    call :KILL_COMPONENT %1
    goto END
)

:MENU
cls
echo QuizMasterPro Process Killer
echo ===========================
echo.
echo Select processes to kill:
echo 1. Frontend Only
echo 2. Backend Only
echo 3. Both Frontend and Backend
echo.
echo Q. Quit
echo.
set /p choice="Select option (1-3, Q to quit): "

call :KILL_COMPONENT %choice%
if errorlevel 1 (
    if /i "%choice%"=="Q" goto END
    echo Invalid choice. Please try again.
    timeout /t 2 >nul
    goto MENU
)
goto END

:KILL_COMPONENT
if "%1"=="1" (
    echo.
    echo Killing Frontend processes...
    :: Kill by window title
    taskkill /F /FI "WINDOWTITLE eq *Frontend*" >nul 2>&1
    :: Kill any remaining node processes
    taskkill /F /IM "node.exe" >nul 2>&1
    echo Frontend processes killed.
    exit /b 0
)
if "%1"=="2" (
    echo.
    echo Killing Backend processes...
    :: Kill by window title
    taskkill /F /FI "WINDOWTITLE eq *Backend*" >nul 2>&1
    :: Kill Python processes running uvicorn
    wmic process where "commandline like '%%uvicorn%%'" call terminate >nul 2>&1
    :: Kill any remaining Python processes with our backend window title
    wmic process where "commandline like '%%_start_backend.bat%%'" call terminate >nul 2>&1
    echo Backend processes killed.
    exit /b 0
)
if "%1"=="3" (
    echo.
    echo Killing all QuizMasterPro processes...
    :: Kill Frontend
    taskkill /F /FI "WINDOWTITLE eq *Frontend*" >nul 2>&1
    taskkill /F /IM "node.exe" >nul 2>&1
    :: Kill Backend
    taskkill /F /FI "WINDOWTITLE eq *Backend*" >nul 2>&1
    wmic process where "commandline like '%%uvicorn%%'" call terminate >nul 2>&1
    wmic process where "commandline like '%%_start_backend.bat%%'" call terminate >nul 2>&1
    echo All processes killed.
    exit /b 0
)
if /i not "%1"=="Q" (
    echo Invalid component argument: %1
    echo Usage: kill_processes.bat [component]
    echo   component: 1=frontend, 2=backend, 3=both
    exit /b 1
)
exit /b 0

:END
endlocal
