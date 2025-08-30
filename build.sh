#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗃️ Running migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"