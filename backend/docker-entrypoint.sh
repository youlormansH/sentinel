#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'EOF'
import time
import sys
import psycopg2
import os

url = os.environ.get("SYNC_DATABASE_URL", "postgresql://sentinel:sentinel@db:5432/sentinel")
for attempt in range(30):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print("Database is ready.")
        sys.exit(0)
    except psycopg2.OperationalError:
        print(f"Database not ready (attempt {attempt + 1}/30), retrying...")
        time.sleep(2)
print("Database did not become ready in time.", file=sys.stderr)
sys.exit(1)
EOF

echo "Running database migrations..."
alembic upgrade head

echo "Seeding RBAC roles/permissions and first admin user..."
python -m app.db.seed

echo "Starting application..."
exec "$@"
