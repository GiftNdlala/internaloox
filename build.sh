#!/usr/bin/env bash
# exit on error
set -o errexit

# Force clear pip cache
pip cache purge || true

# Install dependencies with no cache
pip install --no-cache-dir -r requirements.txt

# Set default environment variables for build
export SECRET_KEY=${SECRET_KEY:-"temp-secret-key-for-build"}
export DEBUG=${DEBUG:-"False"}

# Collect static files
python manage.py collectstatic --no-input

# Run migrations (only if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ]; then
    python manage.py migrate
fi