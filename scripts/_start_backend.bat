@echo off
REM Start the backend server
setlocal

if "%1"=="" (
    set QUIZMASTER_ENV=development
) else (
    set QUIZMASTER_ENV=%1
)

echo Starting backend in %QUIZMASTER_ENV% environment...

call conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\backend

set TEST_MODE=true
set QUIZMASTER_ENV=%QUIZMASTER_ENV%
python -m uvicorn api.main:app --reload

endlocal