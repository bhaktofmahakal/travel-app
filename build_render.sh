#!/usr/bin/env bash
# Minimal build script for Render deployment

set -o errexit  # Exit on error

echo "🚀 Starting build process..."

# Upgrade pip
pip install --upgrade pip

# Install minimal dependencies
echo "📦 Installing dependencies..."
pip install Django==4.2.7
pip install django-crispy-forms==2.1
pip install crispy-bootstrap5==2024.2
pip install django-extensions==3.2.3
pip install python-dateutil==2.8.2
pip install gunicorn==21.2.0
pip install dj-database-url==2.1.0

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗃️ Running migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"