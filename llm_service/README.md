# Standalone LLM Service

This directory contains the standalone LLM service for the IoT Observability project. The service has been separated from the main docker-compose stack to provide better GPU acceleration support and more flexible deployment options.

## Features

- **GPU Acceleration Support**: Automatically detects and uses available GPUs (NVIDIA, AMD, Intel)
- **CPU Fallback**: Gracefully falls back to CPU-only mode if no GPU is available
- **Standalone Operation**: Runs independently from the main IoT stack
- **Docker-based**: Containerized for easy deployment and isolation
- **Health Monitoring**: Built-in health checks and monitoring
- **Security**: Runs with non-root user and security constraints
- **Resource Management**: Configurable resource limits and reservations

## Quick Start

### 1. Prerequisites

- Docker and docker-compose installed
- At least 4GB of available RAM
- For GPU acceleration: NVIDIA drivers, ROCm, or Intel GPU drivers

### 2. Start the Service

```bash
# Simple start with auto-configuration
./start_llm_service.sh

# Or manually with docker-compose
docker-compose -f docker-compose.llm.yml up -d
```

### 3. Verify Service

```bash
# Check health
curl http://localhost:8080/health

# View API documentation
open http://localhost:8080/docs
```

### 4. Stop the Service

```bash
# Using stop script
./stop_llm_service.sh

# Or manually
docker-compose -f docker-compose.llm.yml down
```

## Configuration

### Environment Variables

The service can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://host.docker.internal:27017/` | MongoDB connection string |
| `MONGODB_DB` | `iot_metrics` | MongoDB database name |
| `USE_GPU` | `auto` | GPU usage: `auto`, `true`, `false` |
| `USE_MOCK_LLM` | `false` | Use mock responses for testing |
| `MAX_TOKENS` | `1024` | Maximum tokens in LLM responses |
| `TEMPERATURE` | `0.7` | LLM temperature (creativity) |
| `N_CTX` | `2048` | Context window size |
| `N_THREADS` | `4` | Number of CPU threads to use |
| `MODEL_PATH` | `/tmp/models/llama-2-7b-chat.Q4_K_M.gguf` | Path to the LLM model file |

### Custom Configuration

Create a `.env` file in the llm_service directory:

```bash
# .env file example
MONGODB_URI=mongodb://your-mongodb-host:27017/
USE_GPU=true
MAX_TOKENS=2048
TEMPERATURE=0.5
```

## Model Management

### Downloading Models

The service expects a Llama model in GGUF format. You can download one:

```bash
# Create models directory
mkdir -p /tmp/models

# Download Llama 2 7B Chat model (Q4_K_M quantization)
wget -O /tmp/models/llama-2-7b-chat.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
```

### Using Different Models

To use a different model, update the `MODEL_PATH` environment variable:

```bash
export MODEL_PATH=/tmp/models/your-model.gguf
./start_llm_service.sh
```

### Mock Mode for Testing

For testing without downloading models:

```bash
export USE_MOCK_LLM=true
./start_llm_service.sh
```

## GPU Support

### NVIDIA GPU

For NVIDIA GPU support:

1. Install NVIDIA Docker runtime:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nvidia-docker2
   sudo systemctl restart docker
   ```

2. Start with GPU support:
   ```bash
   export USE_GPU=true
   ./start_llm_service.sh
   ```

### AMD GPU (ROCm)

For AMD GPU support:

1. Install ROCm drivers
2. The service will auto-detect ROCm support

### Intel GPU

For Intel GPU support:

1. Ensure Intel GPU drivers are installed
2. The service will auto-detect Intel GPU support

### CPU-Only Mode

To force CPU-only mode:

```bash
export USE_GPU=false
./start_llm_service.sh
```

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service health status.

### Query LLM
```bash
POST /query
Content-Type: application/json

{
  "query": "What is the average temperature in the last hour?",
  "max_tokens": 1024,
  "temperature": 0.7
}
```

### API Documentation
```bash
GET /docs
```
Interactive Swagger UI documentation.

## Monitoring and Logs

### View Logs
```bash
# Real-time logs
docker logs -f iot_llm_service

# Last 100 lines
docker logs --tail 100 iot_llm_service
```

### Monitor Resources
```bash
# Container stats
docker stats iot_llm_service

# Detailed info
docker inspect iot_llm_service
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   docker logs iot_llm_service
   
   # Check if port is in use
   netstat -ln | grep 8080
   ```

2. **GPU not detected**
   ```bash
   # Check NVIDIA
   nvidia-smi
   
   # Check Intel GPU
   ls /dev/dri/
   
   # Force CPU mode
   export USE_GPU=false
   ```

3. **Out of memory**
   ```bash
   # Reduce context size
   export N_CTX=1024
   export MAX_TOKENS=512
   ```

4. **MongoDB connection issues**
   ```bash
   # Test MongoDB connection
   docker run --rm mongo:latest mongosh "mongodb://host.docker.internal:27017/"
   
   # Use different MongoDB URI
   export MONGODB_URI="mongodb://your-host:27017/"
   ```

### Performance Tuning

1. **For CPU-only systems**:
   ```bash
   export N_THREADS=8  # Use more CPU threads
   export N_CTX=1024   # Smaller context for speed
   ```

2. **For GPU systems**:
   ```bash
   export USE_GPU=true
   export N_CTX=4096   # Larger context with GPU
   ```

3. **Memory optimization**:
   ```bash
   # Use smaller quantized models
   # Q4_K_M is a good balance of quality and speed
   # Q2_K is faster but lower quality
   # Q8_0 is higher quality but slower
   ```

## Security Considerations

- Service runs as non-root user (UID 1000)
- Read-only filesystem with limited tmpfs
- No new privileges allowed
- Only localhost exposure by default
- Resource limits to prevent DoS

## Integration with Main Stack

### Connecting to Main MongoDB

The service connects to the main MongoDB instance using `host.docker.internal`. Ensure the main stack is running:

```bash
# In the main project directory
docker-compose up -d mongodb
```

### Service Discovery

The LLM service is available at `http://localhost:8080` and can be accessed by:
- The main API services
- Frontend applications
- External monitoring tools

### Load Balancing

For production, consider:
- Running multiple LLM service instances
- Using a load balancer (nginx, traefik)
- Implementing request queuing

## Development

### Building Custom Images

```bash
# Build with custom tags
docker build -t iot-llm-service:dev .

# Build with build arguments
docker build --build-arg PYTHON_VERSION=3.11 -t iot-llm-service:py311 .
```

### Development Mode

```bash
# Mount source for development
docker-compose -f docker-compose.llm.yml -f docker-compose.dev.yml up -d
```

### Testing

```bash
# Run with mock LLM for testing
export USE_MOCK_LLM=true
./start_llm_service.sh

# Test endpoints
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

## Support

For issues or questions:
1. Check the logs: `docker logs iot_llm_service`
2. Review this documentation
3. Check GitHub issues
4. Verify system requirements and dependencies
