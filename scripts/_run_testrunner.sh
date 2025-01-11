#!/bin/bash

# Source Conda environment
source /c/Users/JimKay/miniconda3/etc/profile.d/conda.sh
conda activate crewai-quizmaster-pro

# Export environment variables
export TEST_MODE=true
export PYTHONPATH=/c/ParseThat/QuizMasterPro/backend
export POSTGRES_USER=test_user
export POSTGRES_PASSWORD=test_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# Run the Python script
python /c/ParseThat/QuizMasterPro/tests/test_runner.py
