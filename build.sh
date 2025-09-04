#!/usr/bin/env bash

# Exit on error
set -o errexit

# Verbose output
set -o xtrace

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files (still needed for local files)
echo "Collecting static files locally..."
python manage.py collectstatic --no-input

# Also upload to S3 using our custom command
echo "Uploading static files to S3..."
python manage.py s3collectstatic --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "Build completed successfully!" 