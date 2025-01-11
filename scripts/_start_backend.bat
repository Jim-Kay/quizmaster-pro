@echo off
REM Start the backend server
setlocal

if "%1"=="" (
    set QUIZMASTER_ENVIRONMENT=development
) else (
    set QUIZMASTER_ENVIRONMENT=%1
)

echo Starting backend in %QUIZMASTER_ENVIRONMENT% environment...

call conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\backend

REM Copy environment-specific .env file
copy /Y .env.%QUIZMASTER_ENVIRONMENT% .env

set QUIZMASTER_ENVIRONMENT=%QUIZMASTER_ENVIRONMENT%
python -m uvicorn api.main:app --reload

endlocal