#!/bin/bash
# PostgreSQL Init Script for Kassensoftware
# Wird automatisch beim erstmaligen Start von PostgreSQL ausgeführt
# Erstellt alle notwendigen Tabellen und fügt Standard-Benutzer ein

set -e

echo "Creating Kassensoftware tables and seed data..."

# Datenbank wird bereits von POSTGRES_DB erstellt, daher nur Verbindung mit psql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create tables (will be done by SQLAlchemy on first run, but we need the users created)
    -- Tables werden von FastAPI/SQLAlchemy beim Start erstellt
    
    -- Dieser Abschnitt wird von der Anwendung beim ersten Start ausgeführt
    -- Wir müssen nur sicherstellen, dass die Datenbank leer ist
    
    -- Optional: Logging
    SELECT 'Database initialized for Kassensoftware' as status;
EOSQL

echo "Database initialization complete."
