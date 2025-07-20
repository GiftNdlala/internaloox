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
    echo "Testing database connection..."
    python manage.py check --database default || echo "Database connection failed, skipping migrations for now"
    if python manage.py check --database default; then
        echo "Database connection successful, running migrations..."
        python manage.py makemigrations
        python manage.py migrate
        echo "Setting up MVP reference data..."
        python manage.py setup_mvp_data || echo "MVP data setup failed or already exists"
    else
        echo "Skipping migrations due to database connection issues"
    fi
fi