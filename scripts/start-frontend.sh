#!/bin/bash

# SlipScribe - Start Frontend Only

set -e

echo "⚛️  Starting SlipScribe Frontend..."

# Check if node_modules exists
if [ ! -d frontend/node_modules ]; then
    echo "Installing dependencies..."
    cd frontend
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        npm install
    fi
    cd ..
fi

# Start frontend
cd frontend

echo "Starting Vite dev server..."
echo "Frontend: http://localhost:5173"
echo ""

if command -v pnpm &> /dev/null; then
    pnpm dev
else
    npm run dev
fi
