#!/bin/bash

# SlipScribe - Start Docker Infrastructure Only

set -e

echo "📦 Starting SlipScribe Infrastructure..."
echo ""

docker-compose up -d

echo ""
echo "✅ Infrastructure started:"
echo "  PostgreSQL: localhost:5432"
echo "  Redis: localhost:6379"
echo "  Milvus: localhost:19530"
echo "  MinIO: localhost:9000"
echo "  MinIO Console: http://localhost:9001"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
