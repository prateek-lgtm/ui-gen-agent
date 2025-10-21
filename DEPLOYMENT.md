# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Huawei Analytics UI Generator in various environments, from local development to production cloud deployments.

## 📋 Table of Contents

- [Environment Requirements](#environment-requirements)
- [Local Development Deployment](#local-development-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Environment Requirements

### System Requirements

**Minimum Requirements:**
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB available space
- **Network**: Stable internet connection for API calls

**Recommended Requirements:**
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 20GB+ SSD
- **Network**: High-bandwidth connection for optimal performance

### Software Dependencies

```bash
# Core requirements
Python 3.8+ (3.11 recommended)
pip 21.0+
git 2.30+

# Optional but recommended
Docker 20.10+
Docker Compose 2.0+
```

## Local Development Deployment

### Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd huawei_agent_poc_openai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start development server
python api.py
```

### Environment Configuration

Create `.env` file with required variables:

```env
# Required API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Configuration
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
DEVELOPMENT_MODE=true

# Model Configuration
MODEL_NAME=claude-sonnet-4
TEMPERATURE=0.7
MAX_TOKENS=4000

# Database Configuration
CHROMA_DB_PATH=./chroma_db
USER_DATA_PATH=data/user_activity/user_data_for_vectordb.txt
```

### Development Server Options

```bash
# Basic development server
python api.py

# With auto-reload
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# With debug logging
LOG_LEVEL=DEBUG python api.py

# CLI interface for testing
python run.py
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  analytics-ui-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data:ro
      - chroma_data:/app/chroma_db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - analytics-ui-api
    restart: unless-stopped

volumes:
  chroma_data:
```

### Building and Running

```bash
# Build image
docker build -t analytics-ui-api .

# Run container
docker run -d \
  --name analytics-ui \
  -p 8000:8000 \
  --env-file .env \
  analytics-ui-api

# Or use Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f analytics-ui-api

# Stop services
docker-compose down
```

## Cloud Deployment

### AWS Deployment

#### Using AWS App Runner

1. **Prepare source code**:
   ```bash
   # Create apprunner.yaml
   cat > apprunner.yaml << EOF
   version: 1.0
   runtime: python3
   build:
     commands:
       build:
         - pip install -r requirements.txt
   run:
     runtime-version: 3.11
     command: uvicorn api:app --host 0.0.0.0 --port 8000
     network:
       port: 8000
       env: PORT
     env:
       - name: PORT
         value: "8000"
   EOF
   ```

2. **Deploy via AWS CLI**:
   ```bash
   aws apprunner create-service \
     --service-name analytics-ui-generator \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "your-ecr-repo/analytics-ui-api:latest",
         "ImageConfiguration": {
           "Port": "8000",
           "RuntimeEnvironmentVariables": {
             "OPENROUTER_API_KEY": "your-key",
             "OPENAI_API_KEY": "your-key"
           }
         },
         "ImageRepositoryType": "ECR"
       },
       "AutoDeploymentsEnabled": true
     }'
   ```

#### Using ECS with Fargate

1. **Create task definition**:
   ```json
   {
     "family": "analytics-ui-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "analytics-ui-api",
         "image": "your-ecr-repo/analytics-ui-api:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "PORT",
             "value": "8000"
           }
         ],
         "secrets": [
           {
             "name": "OPENROUTER_API_KEY",
             "valueFrom": "arn:aws:secretsmanager:region:account:secret:openrouter-key"
           },
           {
             "name": "OPENAI_API_KEY",
             "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/analytics-ui-api",
             "awslogs-region": "us-west-2",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Deploy with gcloud**:
   ```bash
   # Build and push to GCR
   gcloud builds submit --tag gcr.io/PROJECT-ID/analytics-ui-api
   
   # Deploy to Cloud Run
   gcloud run deploy analytics-ui-api \
     --image gcr.io/PROJECT-ID/analytics-ui-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000 \
     --memory 2Gi \
     --cpu 2 \
     --set-env-vars LOG_LEVEL=INFO \
     --set-secrets OPENROUTER_API_KEY=openrouter-key:latest \
     --set-secrets OPENAI_API_KEY=openai-key:latest
   ```

2. **Configure custom domain**:
   ```bash
   gcloud run domain-mappings create \
     --service analytics-ui-api \
     --domain api.yourdomian.com \
     --region us-central1
   ```

#### Cloud Run YAML Configuration

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: analytics-ui-api
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/PROJECT-ID/analytics-ui-api
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
        env:
        - name: PORT
          value: "8000"
        - name: LOG_LEVEL
          value: "INFO"
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: openrouter-key
              key: latest
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-key
              key: latest
```

### Azure Deployment

#### Using Azure Container Instances

```bash
# Create resource group
az group create --name analytics-ui-rg --location eastus

# Create container instance
az container create \
  --resource-group analytics-ui-rg \
  --name analytics-ui-api \
  --image your-registry/analytics-ui-api:latest \
  --dns-name-label analytics-ui-api \
  --ports 8000 \
  --environment-variables LOG_LEVEL=INFO \
  --secure-environment-variables \
    OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
    OPENAI_API_KEY=$OPENAI_API_KEY \
  --cpu 2 \
  --memory 4
```

## Production Configuration

### Environment Variables

```env
# Production API Configuration
OPENROUTER_API_KEY=your_production_openrouter_key
OPENAI_API_KEY=your_production_openai_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=INFO

# Security Configuration
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,app.yourdomain.com

# Performance Configuration
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
VECTOR_DB_CACHE_SIZE=1000

# Monitoring Configuration
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30
```

### Production Server Configuration

#### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn uvicorn[standard]

# Run with gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --timeout 30 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 100
```

#### Gunicorn Configuration File

Create `gunicorn.conf.py`:

```python
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'analytics-ui-api'

# Server mechanics
daemon = False
pidfile = '/tmp/analytics-ui-api.pid'
user = os.getenv('USER', 'app')
group = os.getenv('GROUP', 'app')
tmp_upload_dir = None

# SSL (if enabled)
if os.getenv('SSL_CERT_PATH') and os.getenv('SSL_KEY_PATH'):
    certfile = os.getenv('SSL_CERT_PATH')
    keyfile = os.getenv('SSL_KEY_PATH')
```

### Reverse Proxy Configuration

#### Nginx Configuration

Create `nginx.conf`:

```nginx
upstream analytics_ui_api {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    # Add more servers for load balancing
    # server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Timeouts
    proxy_connect_timeout 5s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    
    # Main API location
    location / {
        proxy_pass http://analytics_ui_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle large requests
        client_max_body_size 10M;
        
        # Proxy buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://analytics_ui_api/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Database and Storage

#### Vector Database Optimization

```python
# Production ChromaDB configuration
import chromadb
from chromadb.config import Settings

# Configure for production
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/data/chroma_db",
    chroma_server_host="localhost",  # If using client-server mode
    chroma_server_http_port=8001,
))
```

#### Data Backup Strategy

```bash
#!/bin/bash
# backup_data.sh

BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
DATA_DIR="/app/data"
CHROMA_DIR="/app/chroma_db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup user data
tar -czf "$BACKUP_DIR/user_data.tar.gz" "$DATA_DIR"

# Backup vector database
tar -czf "$BACKUP_DIR/chroma_db.tar.gz" "$CHROMA_DIR"

# Upload to cloud storage (AWS S3 example)
aws s3 sync "$BACKUP_DIR" s3://your-backup-bucket/analytics-ui-api/

# Cleanup old backups (keep 30 days)
find /backups -type d -mtime +30 -exec rm -rf {} +
```

## Monitoring and Logging

### Application Monitoring

#### Prometheus Metrics

Create `metrics.py`:

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import time

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
UI_GENERATION_TIME = Histogram('ui_generation_duration_seconds', 'UI generation time')

@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Health Check Implementation

```python
from fastapi import HTTPException
import psutil
import time

@app.get("/health/detailed")
async def detailed_health_check():
    checks = {
        "timestamp": time.time(),
        "status": "healthy",
        "components": {}
    }
    
    # Check API components
    checks["components"]["analytics_agent"] = {
        "status": "healthy" if analytics_agent is not None else "unhealthy",
        "last_check": time.time()
    }
    
    checks["components"]["user_data"] = {
        "status": "healthy" if user_data is not None else "unhealthy",
        "records": len(user_data) if user_data else 0
    }
    
    # Check system resources
    checks["components"]["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # Check external dependencies
    try:
        # Test OpenRouter connectivity
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
        checks["components"]["openrouter"] = {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        checks["components"]["openrouter"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Overall health
    unhealthy_components = [
        comp for comp, data in checks["components"].items() 
        if data.get("status") != "healthy"
    ]
    
    if unhealthy_components:
        checks["status"] = "degraded"
        checks["unhealthy_components"] = unhealthy_components
    
    return checks
```

### Logging Configuration

#### Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
            
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/analytics-ui-api.log")
    ]
)

# Apply structured formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(StructuredFormatter())
```

### Log Aggregation

#### ELK Stack Configuration

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    ports:
      - "5044:5044"

  kibana:
    image: kibana:7.14.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    ports:
      - "5601:5601"

volumes:
  es_data:
```

## Backup and Recovery

### Automated Backup

```bash
#!/bin/bash
# automated_backup.sh

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_ROOT="/backups"
DATA_BACKUP="$BACKUP_ROOT/data_$TIMESTAMP"
DB_BACKUP="$BACKUP_ROOT/chroma_$TIMESTAMP"

# Create backup directories
mkdir -p "$DATA_BACKUP" "$DB_BACKUP"

# Backup application data
echo "Backing up application data..."
tar -czf "$DATA_BACKUP/user_activity.tar.gz" /app/data/user_activity/
tar -czf "$DATA_BACKUP/ui_patterns.tar.gz" /app/data/ui_patterns/

# Backup vector database
echo "Backing up vector database..."
tar -czf "$DB_BACKUP/chroma_db.tar.gz" /app/chroma_db/

# Upload to cloud storage
echo "Uploading to cloud storage..."
aws s3 cp "$DATA_BACKUP/" s3://your-backup-bucket/analytics-ui-api/data/ --recursive
aws s3 cp "$DB_BACKUP/" s3://your-backup-bucket/analytics-ui-api/database/ --recursive

# Cleanup local backups older than 7 days
find "$BACKUP_ROOT" -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed successfully"
```

### Recovery Procedures

```bash
#!/bin/bash
# recovery.sh

BACKUP_DATE="$1"
RESTORE_DIR="/app"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    aws s3 ls s3://your-backup-bucket/analytics-ui-api/data/ | grep PRE
    exit 1
fi

# Download backups from cloud storage
echo "Downloading backup for $BACKUP_DATE..."
mkdir -p /tmp/restore
aws s3 cp s3://your-backup-bucket/analytics-ui-api/data/data_$BACKUP_DATE/ /tmp/restore/data/ --recursive
aws s3 cp s3://your-backup-bucket/analytics-ui-api/database/chroma_$BACKUP_DATE/ /tmp/restore/database/ --recursive

# Stop application
echo "Stopping application..."
docker-compose down

# Restore data
echo "Restoring data..."
rm -rf "$RESTORE_DIR/data" "$RESTORE_DIR/chroma_db"
tar -xzf /tmp/restore/data/user_activity.tar.gz -C /
tar -xzf /tmp/restore/data/ui_patterns.tar.gz -C /
tar -xzf /tmp/restore/database/chroma_db.tar.gz -C /

# Set correct permissions
chown -R app:app "$RESTORE_DIR/data" "$RESTORE_DIR/chroma_db"

# Start application
echo "Starting application..."
docker-compose up -d

# Cleanup
rm -rf /tmp/restore

echo "Recovery completed successfully"
```

## Troubleshooting

### Common Issues

#### Issue: API Fails to Start

**Symptoms:**
- Server doesn't respond on configured port
- Health check endpoints return 503

**Diagnosis:**
```bash
# Check application logs
docker-compose logs analytics-ui-api

# Check system resources
docker stats

# Verify environment variables
docker-compose exec analytics-ui-api env | grep -E "(OPENROUTER|OPENAI)"
```

**Solutions:**
1. **Missing API Keys:**
   ```bash
   # Verify API keys are set
   echo $OPENROUTER_API_KEY
   echo $OPENAI_API_KEY
   ```

2. **Port Conflicts:**
   ```bash
   # Check port usage
   lsof -i :8000
   # Change port in docker-compose.yml or kill conflicting process
   ```

3. **Memory Issues:**
   ```bash
   # Check available memory
   free -h
   # Increase memory limits in docker-compose.yml
   ```

#### Issue: Slow Response Times

**Symptoms:**
- Requests take longer than 5 seconds
- Timeouts in client applications

**Diagnosis:**
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# Monitor resource usage
docker exec analytics-ui-api top
```

**Solutions:**
1. **Increase Resources:**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```

2. **Optimize Vector Database:**
   ```python
   # Reduce chunk size for faster search
   text_splitter = RecursiveCharacterTextSplitter(
       chunk_size=300,  # Reduced from 500
       chunk_overlap=50   # Reduced from 100
   )
   ```

#### Issue: Vector Database Errors

**Symptoms:**
- ChromaDB connection errors
- Empty search results
- Database corruption messages

**Diagnosis:**
```bash
# Check database files
ls -la /app/chroma_db/
```

**Solutions:**
1. **Rebuild Vector Database:**
   ```bash
   # Remove existing database
   rm -rf /app/chroma_db/*
   
   # Restart application (will rebuild)
   docker-compose restart analytics-ui-api
   ```

2. **Check Data Files:**
   ```bash
   # Verify user data files exist
   ls -la /app/data/user_activity/
   ```

### Performance Optimization

#### Memory Optimization

```python
# In production settings
import gc
import resource

# Limit memory usage
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))  # 2GB limit

# Force garbage collection after requests
@app.middleware("http")
async def gc_middleware(request, call_next):
    response = await call_next(request)
    gc.collect()
    return response
```

#### Database Optimization

```python
# Optimize ChromaDB settings
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    allow_reset=False,
    chroma_server_cors_allow_origins=["*"],
    chroma_server_ssl_enabled=False,
    # Production optimizations
    chroma_collection_cache_size=1000,
    chroma_segment_cache_policy="LRU",
))
```

### Monitoring and Alerting

#### Set up Alerts

```bash
# Example alert rules for Prometheus
groups:
- name: analytics-ui-api
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: High error rate detected

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High response time detected

  - alert: ServiceDown
    expr: up{job="analytics-ui-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Service is down
```

This deployment guide provides comprehensive instructions for setting up the Analytics UI Generator in various environments with proper monitoring, security, and reliability measures.