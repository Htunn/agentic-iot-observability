#!/bin/bash

# Stop script for standalone LLM service

set -e

echo "=== Stopping IoT Observability LLM Service ==="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed or not in PATH"
    exit 1
fi

# Stop the service
echo "Stopping LLM service..."
docker-compose -f docker-compose.llm.yml down

# Clean up GPU-specific compose file if it exists
if [ -f "docker-compose.llm-gpu.yml" ]; then
    echo "Cleaning up GPU configuration..."
    rm -f docker-compose.llm-gpu.yml
fi

echo "✅ LLM service stopped successfully"

# Optionally remove the image (uncomment if needed)
# echo "Removing Docker image..."
# docker rmi iot-llm-service 2>/dev/null || echo "Image already removed or doesn't exist"

echo ""
echo "To start again: ./start_llm_service.sh"
