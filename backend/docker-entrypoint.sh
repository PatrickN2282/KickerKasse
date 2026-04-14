#!/bin/bash
# Startup script for Kassensoftware in Docker
# Handles database migrations before starting the app

set -e

echo "======================================"
echo "Starting Kassensoftware Backend"
echo "======================================"
echo ""

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
while ! pg_isready -h ${DATABASE_HOST:-postgres} -U kassensystem > /dev/null 2>&1; do
    sleep 1
done
echo "✓ Database is ready"
echo ""

# Run migrations
echo "🔄 Running database migrations..."
python -c "
from app.core import engine
from app.core.db_migration import run_migrations
import logging
logging.basicConfig(level=logging.INFO)
run_migrations(engine)
print('✓ Migrations completed')
"
echo ""

# Start the application
echo "🚀 Starting Kassensoftware..."
echo ""
exec uvicorn main:app --host 0.0.0.0 --port 8000
