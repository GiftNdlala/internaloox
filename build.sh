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
        # Run existing migrations only (no makemigrations to avoid interactive prompts)
        python manage.py migrate --no-input
        echo "Setting up MVP reference data (compatible with existing products)..."
        python manage.py setup_mvp_data || echo "MVP data setup failed or already exists"
        echo "Testing Product model for API debugging..."
        python manage.py test_products || echo "Product test failed"
    else
        echo "Skipping migrations due to database connection issues"
    fi
fi