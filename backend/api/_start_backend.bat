@echo off
call conda activate crewai-quizmaster-pro

cd C:\data\crewai-quizmaster-pro\backend\api
python -m uvicorn main:app --reload
