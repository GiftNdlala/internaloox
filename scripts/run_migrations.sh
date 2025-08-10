#!/usr/bin/env bash
set -euo pipefail

echo "[migrate] Starting migration step..."

# Ensure env vars
export SECRET_KEY=${SECRET_KEY:-"temp-secret-key"}
export DEBUG=${DEBUG:-"False"}

# Check database connectivity (best effort)
if python manage.py check --database default; then
  echo "[migrate] Database connection OK. Running migrations..."
  python manage.py migrate --no-input
  echo "[migrate] Migrations complete."
  if python manage.py help setup_mvp_data >/dev/null 2>&1; then
    echo "[migrate] Seeding MVP data (idempotent)..."
    python manage.py setup_mvp_data || true
  fi
else
  echo "[migrate] WARNING: Database connection failed; skipping migrations for this deploy stage." >&2
fi