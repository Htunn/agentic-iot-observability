#!/bin/bash
# Project readiness check script

echo "=== IoT Observability Project Readiness Check ==="
echo

# Check if Docker is installed
echo "1. Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker."
    exit 1
else
    echo "✅ Docker is installed."
    docker --version
fi

# Check if Docker Compose is installed
echo
echo "2. Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose (standalone) is installed."
    docker-compose --version
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose (plugin) is installed."
    docker compose version
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Check if all required files exist
echo
echo "3. Checking required project files..."
required_files=(
    "docker-compose.yml"
    "iot_simulator/Dockerfile"
    "iot_simulator/simulator.py"
    "iot_simulator/requirements.txt"
    "metrics_service/Dockerfile"
    "metrics_service/app.py"
    "metrics_service/requirements.txt"
    "llm_service/Dockerfile"
    "llm_service/app.py"
    "llm_service/entrypoint.sh"
    "llm_service/requirements.txt"
    "grafana/provisioning/datasources/mongodb.yaml"
    "grafana/provisioning/dashboards/dashboards.yaml"
    "grafana/dashboards/iot-metrics-dashboard.json"
    "mongodb/mongod.conf"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo "Some required files are missing. Please check the output above."
    exit 1
fi

# Check if .env.example exists and create .env if needed
echo
echo "4. Checking environment variables..."
if [ -f ".env.example" ]; then
    echo "✅ .env.example exists"
    if [ ! -f ".env" ]; then
        echo "⚠️ .env file not found. Creating from .env.example..."
        cp .env.example .env
        echo "✅ Created .env file. Please review and update if needed."
    else
        echo "✅ .env file exists"
    fi
else
    echo "❌ .env.example is missing"
fi

# Check if port 3000, 8000, and 8080 are available
echo
echo "5. Checking if required ports are available..."
for port in 3000 8000 8080 27017; do
    if nc -z localhost $port &>/dev/null; then
        echo "❌ Port $port is already in use. Please free this port before starting the project."
    else
        echo "✅ Port $port is available"
    fi
done

# Check Docker Compose configuration
echo
echo "6. Validating Docker Compose configuration..."
if command -v docker-compose &> /dev/null; then
    if docker-compose config &>/dev/null; then
        echo "✅ docker-compose.yml is valid"
    else
        echo "❌ docker-compose.yml contains errors. Please fix before proceeding."
        exit 1
    fi
else
    if docker compose config &>/dev/null; then
        echo "✅ docker-compose.yml is valid"
    else
        echo "❌ docker-compose.yml contains errors. Please fix before proceeding."
        exit 1
    fi
fi

echo
echo "=== Final Project Status ==="
echo "✅ Your IoT Observability Project appears to be ready for testing!"
echo
echo "To start the project, run:"
if command -v docker-compose &> /dev/null; then
    echo "  docker-compose up -d"
else
    echo "  docker compose up -d"
fi
echo
echo "To access services once running:"
echo "- Grafana: http://localhost:3000"
echo "- Metrics API: http://localhost:8000"
echo "- LLM Query API: http://localhost:8080"
echo
echo "Note: For production use, please ensure you change default credentials in the .env file"
