@echo off

REM Activate Conda environment
CALL "C:\Users\JimKay\miniconda3\condabin\conda.bat" activate crewai-quizmaster-pro

REM Set environment variables
SET TEST_MODE=true
SET PYTHONPATH=C:\ParseThat\QuizMasterPro\backend
SET POSTGRES_USER=test_user
SET POSTGRES_PASSWORD=test_password
SET POSTGRES_HOST=localhost
SET POSTGRES_PORT=5432

REM Run the Python script
python C:\ParseThat\QuizMasterPro\tests\test_runner.py
