@echo off
REM SlipScribe - Start All Services (Windows)

echo Starting SlipScribe...
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env and add your API keys before continuing.
    echo.
)

REM Start Docker services
echo Starting Docker services...
docker-compose up -d

REM Wait for services
echo Waiting for services to be ready...
timeout /t 5 /nobreak > nul

REM Check if backend virtual environment exists
if not exist backend\venv (
    echo Creating backend virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
)

REM Check if frontend dependencies are installed
if not exist frontend\node_modules (
    echo Installing frontend dependencies...
    cd frontend
    call pnpm install
    cd ..
)

REM Create logs directory
if not exist logs mkdir logs

REM Start backend
echo Starting backend API...
cd backend
call venv\Scripts\activate
start /B uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ..\logs\backend.log 2>&1
cd ..

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting frontend...
cd frontend
start /B pnpm dev > ..\logs\frontend.log 2>&1
cd ..

echo.
echo SlipScribe is running!
echo.
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo MinIO Console: http://localhost:9001
echo.
echo Logs:
echo   Backend: logs\backend.log
echo   Frontend: logs\frontend.log
echo.
echo To stop all services, run: scripts\stop.bat
echo.
pause
