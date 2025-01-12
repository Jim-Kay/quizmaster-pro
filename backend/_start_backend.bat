@echo off

REM Use environment parameter or default to development
if "%1"=="" (
    set QUIZMASTER_ENVIRONMENT=development
) else (
    set QUIZMASTER_ENVIRONMENT=%1
)

echo Starting backend in %QUIZMASTER_ENVIRONMENT% environment...

REM Activate conda environment
call conda activate crewai-quizmaster-pro

REM Change to backend directory
cd C:\ParseThat\QuizMasterPro\backend

REM Set Python path
set PYTHONPATH=C:\ParseThat\QuizMasterPro\backend

REM Start uvicorn with the environment variable
uvicorn api.main:app --reload