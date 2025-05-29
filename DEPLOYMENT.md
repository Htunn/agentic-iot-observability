# Deployment Guide

This guide provides instructions for deploying the IoT Observability Project securely in both development and production environments.

## Development Deployment

For local development and testing:

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/iot-observability.git
   cd iot-observability
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env file with appropriate settings
   ```

3. **Run the readiness check**
   ```bash
   ./check-readiness.sh
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Access services**
   - Grafana: http://localhost:3000 (default credentials: admin/admin)
   - Metrics API: http://localhost:8000
   - LLM Query API: http://localhost:8080

## Production Deployment

For secure production deployment:

### 1. Security Hardening

Before deploying to production, apply these security measures:

**Environment Configuration**
- Create a secure `.env` file with strong credentials
- Enable MongoDB authentication
- Change all default passwords

**Docker Compose Overrides**
Create a `docker-compose.prod.yml` file with production settings:

```yaml
version: '3.8'

services:
  # Configure proper restart policies
  iot_simulator:
    restart: always
  
  metrics_service:
    restart: always
  
  mongodb:
    # Enable authentication
    command: ["--auth", "--bind_ip_all"]
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_ROOT_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
  
  llm_service:
    restart: always
    # Add more restrictive CORS
    environment:
      - ALLOWED_ORIGINS=https://your-domain.com
  
  grafana:
    restart: always
    # Force HTTPS
    environment:
      - GF_SERVER_PROTOCOL=https
      - GF_SERVER_CERT_FILE=/etc/grafana/certs/cert.pem
      - GF_SERVER_CERT_KEY=/etc/grafana/certs/key.pem
    volumes:
      - ./certs:/etc/grafana/certs:ro
```

### 2. Add HTTPS with Reverse Proxy

For production, deploy behind a reverse proxy that handles HTTPS:

```yaml
version: '3.8'

services:
  # Add nginx or traefik reverse proxy
  nginx:
    image: nginx:stable-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf:/etc/nginx/conf.d:ro
      - ./nginx/certs:/etc/nginx/certs:ro
      - ./nginx/www:/var/www/html:ro
    depends_on:
      - metrics_service
      - llm_service
      - grafana
```

Sample Nginx configuration (`nginx/conf/default.conf`):
```
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Grafana proxy
    location / {
        proxy_pass http://grafana:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API proxies
    location /api/metrics/ {
        proxy_pass http://metrics_service:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/llm/ {
        proxy_pass http://llm_service:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Rate limiting
        limit_req zone=api burst=10 nodelay;
    }
}
```

### 3. Production Deployment Steps

1. **Provision a production server** with adequate CPU and RAM
   - Recommended: 4 CPU cores, 16GB RAM for LLM processing

2. **Install Docker and Docker Compose**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Clone repository and prepare environment**
   ```bash
   git clone https://github.com/your-username/iot-observability.git
   cd iot-observability
   
   # Create and configure production .env file
   cp .env.example .env.prod
   # Edit .env.prod with secure credentials
   ```

4. **Set up SSL certificates**
   ```bash
   mkdir -p nginx/certs
   # Add your SSL certificates to this directory
   ```

5. **Start services with production configuration**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

6. **Set up monitoring**
   ```bash
   # Install Prometheus and node_exporter for system monitoring
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

### 4. Backup Strategy

1. **Set up automated MongoDB backups**
   ```bash
   # Add to crontab
   0 2 * * * /path/to/backup-script.sh
   ```

2. **Create a backup script**
   ```bash
   #!/bin/bash
   # backup-script.sh
   
   TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
   BACKUP_DIR="/path/to/backups"
   
   # Create backup directory if it doesn't exist
   mkdir -p $BACKUP_DIR
   
   # Backup MongoDB
   docker exec mongodb mongodump --out=/data/db/backup
   
   # Copy backup from container
   docker cp mongodb:/data/db/backup $BACKUP_DIR/mongodb_$TIMESTAMP
   
   # Compress backup
   tar -czf $BACKUP_DIR/mongodb_$TIMESTAMP.tar.gz -C $BACKUP_DIR mongodb_$TIMESTAMP
   
   # Remove uncompressed backup
   rm -rf $BACKUP_DIR/mongodb_$TIMESTAMP
   
   # Keep only the last 7 backups
   ls -tp $BACKUP_DIR/mongodb_*.tar.gz | grep -v '/$' | tail -n +8 | xargs -I {} rm -- {}
   ```

### 5. Monitoring and Alerting

1. **Set up Prometheus and Alertmanager**
2. **Configure alerts for:**
   - Container health status
   - High resource usage
   - Error rates in application logs
   - Database connection issues

## Regular Maintenance

1. **Update dependencies monthly**
   ```bash
   # Pull latest images
   docker-compose pull
   
   # Rebuild with updated dependencies
   docker-compose build --no-cache
   
   # Restart services
   docker-compose up -d
   ```

2. **Check for security vulnerabilities**
   ```bash
   # Scan container images
   docker scan <image-name>
   
   # Check dependencies for vulnerabilities
   docker run --rm -v $(pwd):/app owasp/dependency-check --scan /app
   ```

3. **Review logs regularly for security issues**
   ```bash
   docker-compose logs | grep -i "error\|warning\|exception"
   ```
