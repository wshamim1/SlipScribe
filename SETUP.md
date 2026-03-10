# SlipScribe Development Setup

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- pnpm (or npm)

## Quick Start

### 1. Clone and Setup Environment
```bash
cd SlipScribe
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Infrastructure Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Milvus (port 19530)
- MinIO (ports 9000, 9001)

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload
```

Backend will be available at: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

Frontend will be available at: http://localhost:5173

### 5. Start Worker (Optional - for OCR processing)

```bash
cd backend

# In a new terminal, activate venv
source venv/bin/activate

# Start Celery worker
celery -A app.worker.celery_app worker --loglevel=info
```

## Verify Setup

1. Check infrastructure health:
```bash
docker-compose ps
# All services should be "Up"
```

2. Check backend health:
```bash
curl http://localhost:8000/health
```

3. Check frontend:
Open http://localhost:5173 in your browser

## Development Workflow

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run API server
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .
ruff check --fix .

# Type check
mypy app
```

### Frontend Development
```bash
cd frontend

# Dev server with hot reload
pnpm dev

# Type check
pnpm tsc --noEmit

# Lint
pnpm lint

# Format
pnpm format
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Useful Commands

### Docker Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Reset all data (WARNING: destroys all data)
docker-compose down -v
```

### MinIO (Object Storage)
- Console: http://localhost:9001
- Username: `slipscribe`
- Password: `slipscribe_dev`

Create the bucket manually via console or:
```bash
# Using AWS CLI with MinIO
aws --endpoint-url http://localhost:9000 s3 mb s3://slipscribe-receipts
```

### PostgreSQL
```bash
# Connect to database
docker exec -it slipscribe-postgres psql -U slipscribe -d slipscribe

# Or using any postgres client
psql postgresql://slipscribe:slipscribe_dev@localhost:5432/slipscribe
```

### Redis
```bash
# Connect to Redis CLI
docker exec -it slipscribe-redis redis-cli

# Monitor commands
docker exec -it slipscribe-redis redis-cli MONITOR
```

### Milvus
```bash
# Check Milvus status
curl http://localhost:9091/healthz
```

## Troubleshooting

### Port Conflicts
If ports are already in use, edit `docker-compose.yml` to use different ports.

### Database Connection Issues
1. Ensure PostgreSQL container is running: `docker ps`
2. Check DATABASE_URL in `.env`
3. Verify network: `docker network ls`

### Frontend Can't Connect to Backend
1. Check VITE_API_BASE_URL in frontend
2. Verify CORS settings in backend
3. Check backend is running: `curl http://localhost:8000/health`

### OCR/Worker Issues
1. Verify Redis is running
2. Check Celery worker logs
3. Ensure LLM API keys are set in `.env`

## Next Steps

1. Add your LLM API keys to `.env`
2. Upload a test receipt via the frontend
3. Check processing job in worker logs
4. Explore API docs at http://localhost:8000/docs

## Environment Variables Reference

See `.env.example` for all available configuration options.

**Required for MVP:**
- `DATABASE_URL`
- `REDIS_URL`
- At least one LLM provider API key (OPENAI_API_KEY or GROQ_API_KEY)
- `JWT_SECRET`

**Optional for local dev:**
- `S3_*` variables (MinIO credentials)
- `MILVUS_*` variables (defaults work)
