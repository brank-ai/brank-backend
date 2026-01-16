#!/bin/sh
set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start Gunicorn
# Use exec to ensure gunicorn replaces the shell as PID 1 (important for signal handling)
echo "Starting Gunicorn on 0.0.0.0:${PORT:-8080}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 4 --threads 2 --timeout 120 --access-logfile - --error-logfile - app:app
