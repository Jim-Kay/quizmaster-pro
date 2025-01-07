@echo off
REM Start the backend server

call conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\backend

set TEST_MODE=true
python -m uvicorn api.main:app --reload