# SlipScribe Scripts

This directory contains convenience scripts for starting and stopping SlipScribe services.

## Quick Start

### macOS/Linux

**Start everything (background mode):**
```bash
./scripts/start-all.sh
```

**Start in development mode (logs visible):**
```bash
./scripts/dev.sh
```

**Stop all services:**
```bash
./scripts/stop.sh
```

### Windows

**Start everything:**
```cmd
scripts\start-all.bat
```

**Stop all services:**
```cmd
scripts\stop.bat
```

## Individual Services

### Start Docker Infrastructure Only
```bash
./scripts/start-docker.sh
```

### Start Backend Only
```bash
./scripts/start-backend.sh
```

### Start Frontend Only
```bash
./scripts/start-frontend.sh
```

## What Each Script Does

### `start-all.sh` (Background Mode)
- Checks for `.env` file (creates from example if missing)
- Starts Docker services (Postgres, Redis, Milvus, MinIO)
- Creates Python virtual environment if needed
- Installs frontend dependencies if needed
- Starts backend API in background
- Starts frontend in background
- Saves PIDs to `logs/` directory
- Services run in background

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

**View Logs:**
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

### `dev.sh` (Development Mode)
- Same as `start-all.sh` but keeps logs visible in terminal
- Better for active development
- Press Ctrl+C to stop all services
- Automatically cleans up on exit

### `stop.sh`
- Stops backend and frontend processes (using PIDs from logs/)
- Stops Docker services
- Cleans up PID files

### `start-docker.sh`
- Only starts Docker infrastructure
- Use when you want to run backend/frontend manually

### `start-backend.sh`
- Starts only the FastAPI backend
- Runs in foreground with live logs
- Assumes Docker services are already running

### `start-frontend.sh`
- Starts only the React frontend
- Runs in foreground with live logs
- Assumes backend is already running

## First-Time Setup

The scripts will automatically:
1. Create `.env` from `.env.example` if it doesn't exist
2. Create Python virtual environment
3. Install Python dependencies
4. Install Node.js dependencies

**Important:** Edit `.env` and add your API keys before starting services.

## Logs Directory

Logs are saved to `logs/` directory:
- `backend.log` - FastAPI server logs
- `frontend.log` - Vite dev server logs
- `backend.pid` - Backend process ID
- `frontend.pid` - Frontend process ID

## Troubleshooting

### Port Already in Use
If ports 5173 or 8000 are already in use:
```bash
# Find and kill processes using ports
lsof -ti:5173 | xargs kill
lsof -ti:8000 | xargs kill
```

### Services Won't Start
```bash
# Stop everything and start fresh
./scripts/stop.sh
docker-compose down -v  # Warning: destroys data
./scripts/start-all.sh
```

### View Docker Logs
```bash
docker-compose logs -f
```

### Reset Everything
```bash
# Stop all services
./scripts/stop.sh

# Remove all Docker volumes (WARNING: deletes all data)
docker-compose down -v

# Remove Python venv
rm -rf backend/venv

# Remove Node modules
rm -rf frontend/node_modules

# Start fresh
./scripts/start-all.sh
```
