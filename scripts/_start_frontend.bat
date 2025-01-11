@echo off
setlocal

if "%1"=="" (
    set QUIZMASTER_ENV=development
) else (
    set QUIZMASTER_ENV=%1
)

echo Starting frontend in %QUIZMASTER_ENV% environment...

CALL conda activate crewai-quizmaster-pro

cd C:\ParseThat\QuizMasterPro\frontend
set NEXT_PUBLIC_QUIZMASTER_ENV=%QUIZMASTER_ENV%
npm run dev

endlocal
