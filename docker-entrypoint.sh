#!/bin/bash
set -e

echo "Running database migrations..."
# Mark existing tables as current baseline (ignore error if fresh deploy)
flask db stamp head 2>/dev/null || true
# Apply any pending migrations
flask db upgrade

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:app
