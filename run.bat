@echo off

echo Checking Docker...

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running.
    echo Please start Docker Desktop and run this script again.
    pause
    exit
)

echo Starting Docker services...
docker compose up -d --build

echo Waiting for service...

set URL=http://localhost:8000
set MAX_RETRIES=30
set RETRY=0

:check
curl -s %URL% >nul
if %errorlevel%==0 goto open

timeout /t 2 >nul
set /a RETRY+=1

if %RETRY% GEQ %MAX_RETRIES% goto fail
goto check

:open
echo Opening browser...
start %URL%
exit

:fail
echo Service did not start in time.
pause