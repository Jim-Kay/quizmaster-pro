###Handy Commands

##Prompts to get started:
Review the 
documentation\TEST_PLAN.md

as well as 
documentation\BACKEND_ARCHITECTURE.md

Then try to run 
tests\test_runner.py

using a command like this:

cmd.exe /c set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& call conda activate crewai-quizmaster-pro&& python tests/test_runner.py



##Run Test Runner
cmd /c call conda activate crewai-quizmaster-pro && set TEST_MODE=true && set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend && python tests/test_runner.py
cmd.exe /c set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& call conda activate crewai-quizmaster-pro&& python tests/test_runner.py


##Run PSQL against Test Database
psql postgresql://test_user:test_password@localhost:5432/quizmaster_test -c SELECT typname FROM pg_type WHERE typname = 'llm_provider_enum';