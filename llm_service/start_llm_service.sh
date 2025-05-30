#!/bin/bash

# Start script for standalone LLM service
# This script helps configure and start the LLM service with proper GPU/CPU detection

set -e

echo "=== IoT Observability LLM Service Startup ==="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed or not in PATH"
    exit 1
fi

# Set default environment variables if not already set
export MONGODB_URI=${MONGODB_URI:-"mongodb://host.docker.internal:27017/"}
export MONGODB_DB=${MONGODB_DB:-"iot_metrics"}
export USE_GPU=${USE_GPU:-"auto"}
export USE_MOCK_LLM=${USE_MOCK_LLM:-"false"}
export MAX_TOKENS=${MAX_TOKENS:-"1024"}
export TEMPERATURE=${TEMPERATURE:-"0.7"}
export N_CTX=${N_CTX:-"2048"}
export N_THREADS=${N_THREADS:-"4"}

echo "Configuration:"
echo "  MongoDB URI: $MONGODB_URI"
echo "  MongoDB DB: $MONGODB_DB"
echo "  GPU Usage: $USE_GPU"
echo "  Mock LLM: $USE_MOCK_LLM"
echo "  Max Tokens: $MAX_TOKENS"
echo "  Temperature: $TEMPERATURE"
echo "  Context Size: $N_CTX"
echo "  Threads: $N_THREADS"

# Check for model file
MODEL_PATH="./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo "Warning: Model file not found at $MODEL_PATH"
    echo "You may need to download the model or set USE_MOCK_LLM=true"
    echo "To download the model, you can use:"
    echo "  mkdir -p ./models"
    echo "  wget -O $MODEL_PATH https://huggingface.co/microsoft/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    echo ""
    echo "Or set USE_MOCK_LLM=true to use mock responses for testing"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# GPU Detection and Configuration
GPU_AVAILABLE="false"
GPU_TYPE="none"

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        GPU_AVAILABLE="true"
        GPU_TYPE="nvidia"
        echo "NVIDIA GPU detected"
    fi
fi

# Check for AMD GPU (ROCm)
if [ -d "/opt/rocm" ] || command -v rocm-smi &> /dev/null; then
    GPU_AVAILABLE="true"
    GPU_TYPE="amd"
    echo "AMD GPU (ROCm) detected"
fi

# Check for Intel GPU
if [ -d "/dev/dri" ]; then
    GPU_AVAILABLE="true"
    GPU_TYPE="intel"
    echo "Intel GPU detected"
fi

echo "GPU Available: $GPU_AVAILABLE ($GPU_TYPE)"

# Build the Docker image
echo "Building LLM service Docker image..."
docker build -t iot-llm-service .

# Prepare docker-compose command
COMPOSE_CMD="docker-compose -f docker-compose.llm.yml"

# Add GPU-specific configuration
if [ "$USE_GPU" = "true" ] || ([ "$USE_GPU" = "auto" ] && [ "$GPU_AVAILABLE" = "true" ]); then
    echo "Configuring for GPU acceleration..."
    
    if [ "$GPU_TYPE" = "nvidia" ]; then
        echo "Using NVIDIA GPU configuration"
        # Create a GPU-enabled compose file
        cat > docker-compose.llm-gpu.yml << EOF
version: '3.8'

services:
  llm_service:
    extends:
      file: docker-compose.llm.yml
      service: llm_service
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - USE_GPU=true
    devices:
      - /dev/nvidia0:/dev/nvidia0
      - /dev/nvidiactl:/dev/nvidiactl
      - /dev/nvidia-uvm:/dev/nvidia-uvm
EOF
        COMPOSE_CMD="$COMPOSE_CMD -f docker-compose.llm-gpu.yml"
    else
        echo "Using generic GPU configuration"
        export USE_GPU="true"
    fi
else
    echo "Using CPU-only configuration"
    export USE_GPU="false"
fi

# Start the service
echo "Starting LLM service..."
$COMPOSE_CMD up -d

# Wait for service to be ready
echo "Waiting for service to start..."
sleep 10

# Health check
echo "Checking service health..."
for i in {1..30}; do
    if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ LLM service is healthy and ready!"
        echo ""
        echo "Service endpoints:"
        echo "  Health: http://localhost:8080/health"
        echo "  Query: http://localhost:8080/query"
        echo "  API Docs: http://localhost:8080/docs"
        echo ""
        echo "To view logs: docker logs iot_llm_service"
        echo "To stop: $COMPOSE_CMD down"
        exit 0
    fi
    echo "Waiting for service... ($i/30)"
    sleep 2
done

echo "❌ Service failed to start or is not responding"
echo "Check logs with: docker logs iot_llm_service"
exit 1
