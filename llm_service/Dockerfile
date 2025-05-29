FROM python:3.9-slim

# Set non-interactive to avoid user prompts
ENV DEBIAN_FRONTEND=noninteractive

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

WORKDIR /app

# Install system dependencies for llama-cpp-python with security updates
RUN apt-get update && apt-get install -y \
  build-essential \
  cmake \
  curl \
  ca-certificates \
  && apt-get upgrade -y \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
  # Remove pip cache
  rm -rf /root/.cache/pip/*

# Create directories for model storage and source code with proper permissions
RUN mkdir -p /app/models /app/src && \
  chown -R appuser:appuser /app

# Copy application code to src directory
COPY . /app/src/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && \
  chown appuser:appuser /entrypoint.sh

# Expose the API port
EXPOSE 8080

# Add health check (simple response check once the service is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user for running the application
USER appuser

# Change the working directory to where the source code is mounted
WORKDIR /app/src

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
