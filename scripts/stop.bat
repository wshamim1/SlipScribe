@echo off
REM SlipScribe - Stop All Services (Windows)

echo Stopping SlipScribe services...
echo.

REM Stop Docker services
echo Stopping Docker services...
docker-compose down

REM Kill backend and frontend processes
echo Stopping backend and frontend...
taskkill /F /IM uvicorn.exe 2>nul
taskkill /F /IM node.exe 2>nul

echo.
echo All services stopped
pause
