@echo off
REM Start the frontend server
setlocal

REM Use environment parameter or default to development
if "%1"=="" (
    set NODE_ENV=development
    set QUIZMASTER_ENVIRONMENT=development
) else (
    set NODE_ENV=%1
    set QUIZMASTER_ENVIRONMENT=%1
)

echo Starting frontend in %NODE_ENV% environment...

CALL conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\frontend

REM Run npm command
npm run dev

endlocal
