###Good to Know
There are three different environment variables with URLs:
BACKEND_URL=http://localhost:8000   -- Backend
NEXT_PUBLIC_API_URL=http://localhost:3000  -- Frontend
NEXTAUTH_URL=http://localhost:3000  -- Auth Url


###Handy Commands

##Prompts to get started:
Review the 
documentation\TEST_PLAN_v2.md

as well as 
documentation\BACKEND_ARCHITECTURE_v1.md

Then try to run the verified tests:
cmd.exe /c call conda activate crewai-quizmaster-pro&& set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& pytest tests/verified


##Run Test Runner
cmd /c call conda activate crewai-quizmaster-pro && set TEST_MODE=true && set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend && python tests/test_runner.py
cmd.exe /c set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& call conda activate crewai-quizmaster-pro&& python tests/test_runner.py

##Run PSQL against Test Database
psql postgresql://test_user:test_password@localhost:5432/quizmaster_test -c SELECT typename FROM pg_type WHERE typname = 'llmprovider';


##Run Pytest AsyncIO Database tests/test_runner
cmd.exe /c call conda activate crewai-quizmaster-pro&& pip install python-multipart>=0.0.7&& set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& pytest tests/verified/infrastructure/test_database.py tests/verified/infrastructure/test_db_init.py -v

## db_init test 
cmd.exe /c call conda activate crewai-quizmaster-pro&& set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& pytest tests/verified/infrastructure/test_db_init.py -v

#Search Helper
cmd.exe /c call conda activate crewai-quizmaster-pro&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& python c:/ParseThat/QuizMasterPro/utils/search_helper.py

#test_auth.py
cmd.exe /c call conda activate crewai-quizmaster-pro&& set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& pytest tests/verified/core/test_auth.py -v
#test_db_session.py
cmd.exe /c call conda activate crewai-quizmaster-pro&& set TEST_MODE=true&& set PYTHONPATH=c:/ParseThat/QuizMasterPro/backend&& set POSTGRES_USER=test_user&& set POSTGRES_PASSWORD=test_password&& set POSTGRES_HOST=localhost&& set POSTGRES_PORT=5432&& pytest tests/verified/core/test_db_session.py -v


## Initialize DEV Database
conda run -n crewai-quizmaster-pro --no-capture-output python scripts/init_dev_db.py

##New Test runner (run_tests.py)  - in DEV
conda run -n crewai-quizmaster-pro --no-capture-output set QUIZMASTER_ENVIRONMENT=development&& python scripts/run_tests.py tests/verified/infrastructure/test_db_init.py -v -s
cmd /c conda run -n crewai-quizmaster-pro --no-capture-output python scripts/run_tests.py tests/verified/core/test_db_session.py -v -s -e test

cmd /c conda run -n crewai-quizmaster-pro --no-capture-output python scripts/run_tests.py tests/verified/core/test_topics_api.py -v -s -e test


##Build backend docker image
C:\ParseThat\QuizMasterPro>powershell -Command cd ./backend; docker build -t quizmaster-backend:latest .

