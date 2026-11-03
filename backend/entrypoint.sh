#!/bin/bash
set -e

if [ "$#" -eq 0 ] || [ "$1" = "uvicorn" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || echo "Migration warning: continuing with existing schema"
    echo "Starting LeaveHRAlone AI API server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    exec "$@"
fi
