#!/bin/bash
set -e

echo "=== User Service Entrypoint ==="
echo "Version: ${APP_VERSION:-unknown}"

# Run Alembic migrations before starting the app
echo "Running database migrations..."
alembic upgrade head 2>&1 || {
    echo "WARNING: Alembic migration failed, continuing anyway..."
    echo "The app may encounter errors if the database schema is outdated."
}
echo "Migrations complete."

# Start uvicorn
echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8444
