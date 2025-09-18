#!/bin/bash

# Docker entrypoint script for AgriFinHub Chatbot Backend
# This script handles container initialization and graceful shutdown

set -e

# Function to handle graceful shutdown
graceful_shutdown() {
    echo "Received shutdown signal. Gracefully shutting down..."
    # Kill the background process if it exists
    if [ ! -z "$PID" ]; then
        kill -TERM "$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true
    fi
    echo "Shutdown complete."
    exit 0
}

# Set up signal handlers
trap graceful_shutdown SIGTERM SIGINT

# Wait for database to be ready (if using PostgreSQL)
if [ ! -z "$DB_HOST" ] && [ ! -z "$DB_PORT" ]; then
    echo "Waiting for database at $DB_HOST:$DB_PORT..."
    
    # Simple wait logic
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            echo "Database is ready!"
            break
        fi
        
        attempt=$((attempt + 1))
        echo "Database not ready yet... attempt $attempt/$max_attempts"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "Warning: Database connection timeout. Proceeding anyway..."
    fi
fi

# Create necessary directories
mkdir -p /app/logs

# Set proper permissions (only if we have permission to do so)
if [ -w /app/logs ]; then
    chown -R appuser:appuser /app/logs 2>/dev/null || echo "Warning: Could not change ownership of logs directory"
else
    echo "Warning: No write permission for logs directory"
fi

# Validate critical environment variables
echo "Validating environment variables..."

if [ -z "$GOOGLE_GENAI_API_KEY" ]; then
    echo "Warning: GOOGLE_GENAI_API_KEY is not set. AI features may not work."
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    echo "Error: JWT_SECRET_KEY is required for authentication."
    exit 1
fi

echo "Environment validation complete."

# Start the application
echo "Starting AgriFinHub Chatbot Backend..."

# Run the main application in the background
python run.py &
PID=$!

# Wait for the background process
wait $PID