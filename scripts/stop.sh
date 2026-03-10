#!/bin/bash

# SlipScribe - Stop All Services

set -e

echo "🛑 Stopping SlipScribe services..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Stop backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm logs/backend.pid
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo "Backend process not running"
        rm logs/backend.pid
    fi
else
    echo "Backend PID file not found"
fi

# Stop frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm logs/frontend.pid
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo "Frontend process not running"
        rm logs/frontend.pid
    fi
else
    echo "Frontend PID file not found"
fi

# Stop Docker services
echo "Stopping Docker services..."
docker-compose down
echo -e "${GREEN}✓ Docker services stopped${NC}"

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
