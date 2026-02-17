#!/bin/bash
set -euo pipefail

echo "=== Database Migration & Seed ==="

# Build a sync DATABASE_URL for alembic and seeds from individual env vars
# (the DATABASE_URL env var uses asyncpg which alembic cannot use directly)
SYNC_DB_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}"

# Override the hardcoded sqlalchemy.url in alembic.ini with the real connection string
# Use /tmp for the temp file since the working dir may not be writable (OpenShift random UID)
cp alembic.ini /tmp/alembic.ini
sed -i "s|^sqlalchemy.url = .*|sqlalchemy.url = ${SYNC_DB_URL}|" /tmp/alembic.ini

echo "Running Alembic migrations..."
alembic -c /tmp/alembic.ini upgrade head
echo "Migrations complete."

echo "Running seed data..."
python -c "
import sys, os
sys.path.insert(0, '/app/packages/db/src')
os.chdir('/app/packages/db')

import seeds.seed_data as sd
# Override the hardcoded DATABASE_URL with the actual connection string
sd.DATABASE_URL = '${SYNC_DB_URL}'
sd.seed()
"
echo "Seed complete."

echo "=== Database startup finished ==="
