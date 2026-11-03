#!/bin/bash
set -e

PORT="${PORT:-8000}"

if [ "$#" -eq 0 ] || [ "$1" = "uvicorn" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || echo "Migration warning: continuing with existing schema"
    echo "Starting LeaveHRAlone AI API server on port $PORT..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
else
    exec "$@"
fi
