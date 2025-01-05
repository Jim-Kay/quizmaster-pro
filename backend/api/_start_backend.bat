@echo off
call conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\backend\api

rem Add backend directory to Python path
set PYTHONPATH=C:\ParseThat\QuizMasterPro\backend;%PYTHONPATH%

python -m uvicorn main:app --reload