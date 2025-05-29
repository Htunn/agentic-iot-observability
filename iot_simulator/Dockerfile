FROM python:3.9-slim

# Set non-interactive to avoid user prompts
ENV DEBIAN_FRONTEND=noninteractive

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
  # Remove pip cache
  rm -rf /root/.cache/pip/*

# Create directories for source code with proper permissions
RUN mkdir -p /app/src && chown -R appuser:appuser /app

# Copy application code to src directory
COPY . /app/src/

# Use non-root user
USER appuser

# Change working directory to src
WORKDIR /app/src

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://metrics_service:8000/')" || exit 1

# Run the application
CMD ["python", "simulator.py"]
