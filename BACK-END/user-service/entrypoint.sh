#!/bin/bash
set -e

echo "=== User Service Entrypoint ==="
echo "Version: ${APP_VERSION:-unknown}"

# Ensure alembic_version table supports our long revision IDs (>32 chars)
# Alembic defaults to VARCHAR(32) which is too small for descriptive IDs
echo "Preparing alembic_version table..."
python -c "
from database import DATABASE_URL
from sqlalchemy import create_engine, text
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text(
        \"SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version'\"
    ))
    if result.fetchone():
        conn.execute(text('ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)'))
    else:
        conn.execute(text(
            'CREATE TABLE alembic_version (version_num VARCHAR(128) NOT NULL, '
            'CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))'
        ))
    conn.commit()
    print('alembic_version table ready (VARCHAR 128)')
" 2>&1 || echo "WARNING: Could not prepare alembic_version table, continuing..."

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head 2>&1 || {
    echo "WARNING: Alembic migration failed, continuing anyway..."
    echo "The app may encounter errors if the database schema is outdated."
}
echo "Migrations complete."

# Start uvicorn
echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8444
