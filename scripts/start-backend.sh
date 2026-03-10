#!/bin/bash

# SlipScribe - Start Backend Only

set -e

echo "🐍 Starting SlipScribe Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create it from .env.example"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d backend/venv ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Start backend
cd backend
source venv/bin/activate
echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
