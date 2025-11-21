#!/bin/bash
set -e

echo "=========================================="
echo "Yoga Assistant - Container Starting"
echo "=========================================="

# Set Docker environment flag
export DOCKER_CONTAINER=true

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready!"

# Initialize database schema
echo "Initializing database schema..."
cd /app
python yoga_assistant/db_prep.py

if [ $? -eq 0 ]; then
    echo "✓ Database initialized successfully!"
else
    echo "✗ Database initialization failed!"
    exit 1
fi

# Start Streamlit application
echo "Starting Streamlit application..."
echo "=========================================="
exec streamlit run yoga_assistant/app.py
