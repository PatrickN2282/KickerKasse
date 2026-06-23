#!/bin/bash
# Startup script for Kassensoftware in Docker
# Ensures database migrations are applied before starting the app

set -e

echo "========================================================================"
echo "KASSENSOFTWARE DOCKER CONTAINER STARTUP"
echo "========================================================================"
echo ""

# Step 1: Wait for database to be ready
echo "⏳ STEP 1: Waiting for database connection..."
DB_READY=0
for i in {1..30}; do
    if pg_isready -h ${DATABASE_HOST:-postgres} -U ${DATABASE_USER:-kassensystem-test} > /dev/null 2>&1; then
        echo "✓ Database connection successful"
        DB_READY=1
        break
    fi
    echo "  Attempt $i/30: Database not ready yet, retrying..."
    sleep 2
done

if [ $DB_READY -eq 0 ]; then
    echo "✗ ERROR: Could not connect to database after 60 seconds"
    exit 1
fi
echo ""

# Step 2: Run database migrations
echo "🔄 STEP 2: Running database migrations..."
python << 'EOF'
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from app.core import engine
    from app.core.db_migration import run_migrations
    
    logger = logging.getLogger(__name__)
    logger.info("Starting migration process...")
    
    success = run_migrations(engine)
    
    if success:
        print("\n✓ Database migration completed successfully")
    else:
        print("\n⚠️  Database migration completed with warnings - check logs above")
        
except Exception as e:
    print(f"\n✗ ERROR during migration: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "✗ ERROR: Database migration failed"
    exit 1
fi
echo ""

# Step 3: Start the application
echo "🚀 STEP 3: Starting Kassensoftware with uvicorn..."
echo "========================================================================"
echo ""
exec uvicorn main:app --host 0.0.0.0 --port 8000
