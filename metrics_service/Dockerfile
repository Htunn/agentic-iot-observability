FROM python:3.9-slim

# Set non-interactive to avoid user prompts
ENV DEBIAN_FRONTEND=noninteractive

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

WORKDIR /app

# Install security updates and clean up
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
  # Remove pip cache
  rm -rf /root/.cache/pip/*

# Copy application code
COPY . .

# Set proper permissions for the app directory
RUN chown -R appuser:appuser /app

# Use non-root user
USER appuser

# Expose the API port
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
