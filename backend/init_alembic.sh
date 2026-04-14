#!/bin/bash
# Initialize Alembic for database migrations (OPTIONAL - for future use)
# This script is optional; the app uses db_migration.py for automatic migrations

cd "$(dirname "$0")"

if [ ! -d "alembic" ]; then
    echo "Initializing Alembic..."
    alembic init alembic
    echo "✓ Alembic initialized"
    echo ""
    echo "Next steps:"
    echo "1. Edit alembic/env.py to set up SQLAlchemy database URL"
    echo "2. Create a migration: alembic revision --autogenerate -m 'your message'"
    echo "3. Apply migrations: alembic upgrade head"
else
    echo "Alembic already initialized in $(pwd)/alembic"
fi
