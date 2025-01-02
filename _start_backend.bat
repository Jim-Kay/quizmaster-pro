@echo off
call conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\backend\api
python -m uvicorn main:app --reload