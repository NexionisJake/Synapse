# Serendipity Analysis - Deployment Guide

## Overview

This guide covers the deployment configuration and monitoring setup for the Serendipity Analysis feature in the Synapse AI Web Application.

## Pre-Deployment Checklist

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space for caching and logs
- **Network**: Internet access for AI model downloads

### Dependencies

#### Core Dependencies
```bash
# Python packages (already in requirements.txt)
flask>=2.3.0
ollama>=0.1.0
aiofiles>=0.8.0
psutil>=5.9.0
```

#### AI Service
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download recommended model
ollama pull llama3:8b
```

## Environment Configuration

### Required Environment Variables

Create or update your `.env` file:

```bash
# Core Feature Toggle
ENABLE_SERENDIPITY_ENGINE=True

# Data Processing Configuration
SERENDIPITY_MIN_INSIGHTS=3
SERENDIPITY_MAX_MEMORY_SIZE_MB=10

# Caching Configuration (seconds)
SERENDIPITY_MEMORY_CACHE_TTL=3600      # 1 hour
SERENDIPITY_ANALYSIS_CACHE_TTL=1800    # 30 minutes
SERENDIPITY_FORMATTED_CACHE_TTL=1800   # 30 minutes

# Performance Tuning
SERENDIPITY_MAX_CHUNK_SIZE=4000
SERENDIPITY_CHUNK_OVERLAP=300

# Queue Management
SERENDIPITY_MAX_QUEUE_SIZE=10
SERENDIPITY_WORKER_COUNT=3
SERENDIPITY_REQUEST_TIMEOUT=300        # 5 minutes

# Monitoring and Logging
SERENDIPITY_ENABLE_PERFORMANCE_MONITORING=True
SERENDIPITY_LOG_LEVEL=INFO
```

### Optional Configuration

```bash
# Advanced Performance Settings
SERENDIPITY_ENABLE_COMPRESSION=True
SERENDIPITY_COMPRESSION_LEVEL=6
SERENDIPITY_MEMORY_LIMIT_MB=1024

# Development Settings
SERENDIPITY_DEBUG_MODE=False
SERENDIPITY_ENABLE_PROFILING=False
SERENDIPITY_MOCK_AI_RESPONSES=False
```

## Deployment Steps

### 1. Verify Integration

```bash
# Check if serendipity service can be imported
python -c "
from serendipity_service import SerendipityService
from config import get_config
config = get_config()
service = SerendipityService(config=config)
print('✅ Serendipity service ready')
"
```

### 2. Validate Configuration

```bash
# Run configuration validation
python -c "
from config import get_config
config = get_config()
print(f'ENABLE_SERENDIPITY_ENGINE: {getattr(config, \"ENABLE_SERENDIPITY_ENGINE\", False)}')
print(f'MIN_INSIGHTS: {getattr(config, \"SERENDIPITY_MIN_INSIGHTS\", 3)}')
print(f'MAX_MEMORY_SIZE: {getattr(config, \"SERENDIPITY_MAX_MEMORY_SIZE_MB\", 10)}MB')
print('✅ Configuration validated')
"
```

### 3. Test AI Service Connection

```bash
# Verify Ollama is running and accessible
curl -s http://localhost:11434/api/tags | jq '.models[].name' | grep llama3

# Test AI service through Synapse
curl -s http://localhost:5000/api/status | jq '.ai_service_status'
```

### 4. Verify Frontend Integration

```bash
# Check if serendipity section exists in dashboard
curl -s http://localhost:5000/dashboard | grep -o "serendipity-section" && echo "✅ Frontend integrated"

# Verify JavaScript files are loaded
curl -s http://localhost:5000/static/js/dashboard.js | grep -o "discoverConnections" && echo "✅ JavaScript ready"

# Check CSS styles
curl -s http://localhost:5000/static/css/style.css | grep -o "serendipity-section" && echo "✅ CSS integrated"
```

### 5. Test API Endpoints

```bash
# Test serendipity status endpoint
curl -X GET http://localhost:5000/api/serendipity

# Test serendipity analysis (requires memory data)
curl -X POST http://localhost:5000/api/serendipity \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Web Server Configuration

#### Nginx Configuration
```nginx
# Add to your existing Nginx config
location /api/serendipity {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Increase timeout for long-running analysis
    proxy_read_timeout 300s;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    
    # Disable buffering for real-time responses
    proxy_buffering off;
    proxy_cache off;
}

# Static assets caching
location /static/ {
    expires 1d;
    add_header Cache-Control "public, immutable";
}
```

#### Apache Configuration
```apache
# Add to your existing Apache config
<Location "/api/serendipity">
    ProxyPass "http://127.0.0.1:5000/api/serendipity"
    ProxyPassReverse "http://127.0.0.1:5000/api/serendipity"
    ProxyTimeout 300
</Location>

# Static assets
<Directory "/path/to/synapse/static">
    ExpiresActive On
    ExpiresDefault "access plus 1 day"
</Directory>
```

### Process Management

#### Systemd Service
```ini
# /etc/systemd/system/synapse-serendipity.service
[Unit]
Description=Synapse AI Web Application with Serendipity Analysis
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=synapse
Group=synapse
WorkingDirectory=/opt/synapse
Environment=PATH=/opt/synapse/venv/bin
ExecStart=/opt/synapse/venv/bin/python app.py
Restart=always
RestartSec=10

# Environment variables
EnvironmentFile=/opt/synapse/.env

# Resource limits
LimitNOFILE=65536
MemoryMax=2G

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=synapse-serendipity

[Install]
WantedBy=multi-user.target
```

#### Docker Configuration
```dockerfile
# Dockerfile for Serendipity-enabled Synapse
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 synapse && chown -R synapse:synapse /app
USER synapse

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/status || exit 1

# Start command
CMD ["python", "app.py"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  synapse:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ENABLE_SERENDIPITY_ENGINE=True
      - SERENDIPITY_MIN_INSIGHTS=3
      - SERENDIPITY_MAX_MEMORY_SIZE_MB=10
    volumes:
      - ./memory.json:/app/memory.json
      - ./logs:/app/logs
      - serendipity_cache:/app/cache
    depends_on:
      - ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ollama_data:
  serendipity_cache:
```

## Monitoring and Logging

### Application Monitoring

#### Health Check Endpoint
```python
# Add to app.py if not present
@app.route('/health/serendipity')
def serendipity_health():
    """Health check for serendipity feature"""
    try:
        from serendipity_service import SerendipityService
        service = SerendipityService(config=config)
        
        # Basic functionality test
        status = {
            'service': 'healthy',
            'cache': 'operational',
            'queue': 'ready',
            'ai_service': 'connected' if service.ai_service else 'disconnected'
        }
        
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 503
```

#### Metrics Collection
```python
# Performance metrics endpoint
@app.route('/metrics/serendipity')
def serendipity_metrics():
    """Serendipity performance metrics"""
    try:
        from performance_monitor import get_performance_monitor
        monitor = get_performance_monitor()
        
        metrics = {
            'analysis_count': monitor.analysis_stats['total_analyses'],
            'success_rate': monitor.get_success_rate(),
            'average_duration': monitor.get_average_duration(),
            'cache_hit_rate': monitor.get_cache_hit_rate(),
            'queue_length': monitor.get_queue_length(),
            'memory_usage': monitor.get_memory_usage()
        }
        
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Log Configuration

#### Structured Logging
```python
# Enhanced logging configuration
import logging
import json
from datetime import datetime

class SerendipityFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'component': 'serendipity',
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'analysis_id'):
            log_entry['analysis_id'] = record.analysis_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'cache_hit'):
            log_entry['cache_hit'] = record.cache_hit
            
        return json.dumps(log_entry)

# Configure serendipity logger
serendipity_logger = logging.getLogger('serendipity')
handler = logging.FileHandler('logs/serendipity.log')
handler.setFormatter(SerendipityFormatter())
serendipity_logger.addHandler(handler)
serendipity_logger.setLevel(logging.INFO)
```

#### Log Rotation
```bash
# /etc/logrotate.d/synapse-serendipity
/opt/synapse/logs/serendipity.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 synapse synapse
    postrotate
        systemctl reload synapse-serendipity
    endscript
}
```

### Performance Monitoring

#### System Metrics
```bash
# Monitor system resources
#!/bin/bash
# monitor_serendipity.sh

echo "=== Serendipity System Monitor ==="
echo "Timestamp: $(date)"
echo

# Memory usage
echo "Memory Usage:"
ps aux | grep -E "(python|ollama)" | awk '{print $1, $2, $4, $11}' | column -t

# Disk usage
echo -e "\nDisk Usage:"
df -h /opt/synapse/cache /opt/synapse/logs

# Network connections
echo -e "\nNetwork Connections:"
netstat -an | grep -E "(5000|11434)" | head -10

# Process status
echo -e "\nProcess Status:"
systemctl status synapse-serendipity ollama --no-pager -l

# Cache statistics
echo -e "\nCache Statistics:"
curl -s http://localhost:5000/metrics/serendipity | jq '.'

echo -e "\n=== End Monitor ==="
```

#### Alerting Configuration
```bash
# Simple alerting script
#!/bin/bash
# serendipity_alerts.sh

# Check service health
if ! curl -sf http://localhost:5000/health/serendipity > /dev/null; then
    echo "ALERT: Serendipity service is down" | mail -s "Synapse Alert" admin@example.com
fi

# Check memory usage
MEMORY_USAGE=$(ps aux | grep python | awk '{sum+=$4} END {print sum}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "ALERT: High memory usage: ${MEMORY_USAGE}%" | mail -s "Synapse Memory Alert" admin@example.com
fi

# Check disk space
DISK_USAGE=$(df /opt/synapse | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "ALERT: High disk usage: ${DISK_USAGE}%" | mail -s "Synapse Disk Alert" admin@example.com
fi
```

## Security Configuration

### Firewall Rules
```bash
# UFW configuration
sudo ufw allow 5000/tcp comment "Synapse Web Application"
sudo ufw allow from 127.0.0.1 to any port 11434 comment "Ollama (localhost only)"
```

### SSL/TLS Configuration
```nginx
# HTTPS configuration for Nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Backup and Recovery

### Data Backup
```bash
#!/bin/bash
# backup_serendipity.sh

BACKUP_DIR="/backup/synapse/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup memory data
cp /opt/synapse/memory.json "$BACKUP_DIR/"

# Backup configuration
cp /opt/synapse/.env "$BACKUP_DIR/"

# Backup logs (last 7 days)
find /opt/synapse/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# Backup cache metadata (not the cache itself)
if [ -d "/opt/synapse/cache" ]; then
    ls -la /opt/synapse/cache > "$BACKUP_DIR/cache_inventory.txt"
fi

# Create archive
tar -czf "/backup/synapse_$(date +%Y%m%d_%H%M%S).tar.gz" -C /backup/synapse "$(basename $BACKUP_DIR)"

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Procedures
```bash
#!/bin/bash
# restore_serendipity.sh

BACKUP_FILE="$1"
RESTORE_DIR="/opt/synapse"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop services
systemctl stop synapse-serendipity

# Extract backup
tar -xzf "$BACKUP_FILE" -C /tmp/

# Restore files
cp /tmp/*/memory.json "$RESTORE_DIR/"
cp /tmp/*/.env "$RESTORE_DIR/"

# Set permissions
chown synapse:synapse "$RESTORE_DIR/memory.json" "$RESTORE_DIR/.env"

# Clear cache to force refresh
rm -rf "$RESTORE_DIR/cache/*"

# Start services
systemctl start synapse-serendipity

echo "Recovery completed from: $BACKUP_FILE"
```

## Troubleshooting

### Common Deployment Issues

#### Service Won't Start
```bash
# Check logs
journalctl -u synapse-serendipity -f

# Verify configuration
python -c "from config import get_config; print(get_config().__dict__)"

# Test imports
python -c "from serendipity_service import SerendipityService; print('OK')"
```

#### High Memory Usage
```bash
# Monitor memory usage
watch -n 5 'ps aux | grep python | head -10'

# Check cache sizes
du -sh /opt/synapse/cache/*

# Adjust cache settings in .env
echo "SERENDIPITY_MEMORY_CACHE_TTL=1800" >> .env
```

#### Slow Performance
```bash
# Check AI service response time
time curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3:8b","prompt":"test"}'

# Monitor queue length
curl -s http://localhost:5000/metrics/serendipity | jq '.queue_length'

# Check system resources
htop
```

### Performance Tuning

#### Memory Optimization
```bash
# Reduce cache sizes for memory-constrained systems
export SERENDIPITY_MEMORY_CACHE_TTL=1800
export SERENDIPITY_ANALYSIS_CACHE_TTL=900
export SERENDIPITY_MAX_MEMORY_SIZE_MB=5
```

#### CPU Optimization
```bash
# Adjust worker count based on CPU cores
export SERENDIPITY_WORKER_COUNT=$(nproc)
export SERENDIPITY_MAX_QUEUE_SIZE=$(($(nproc) * 2))
```

#### Network Optimization
```bash
# Increase timeouts for slow networks
export SERENDIPITY_REQUEST_TIMEOUT=600
export SERENDIPITY_AI_TIMEOUT=300
```

## Maintenance

### Regular Maintenance Tasks

#### Weekly Tasks
```bash
# Clean old cache entries
find /opt/synapse/cache -type f -mtime +7 -delete

# Rotate logs
logrotate -f /etc/logrotate.d/synapse-serendipity

# Check disk usage
df -h /opt/synapse
```

#### Monthly Tasks
```bash
# Update AI model if needed
ollama pull llama3:8b

# Backup configuration and data
./backup_serendipity.sh

# Review performance metrics
curl -s http://localhost:5000/metrics/serendipity | jq '.'
```

### Updates and Upgrades

#### Application Updates
```bash
# Backup before update
./backup_serendipity.sh

# Stop service
systemctl stop synapse-serendipity

# Update code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/test_serendipity.py

# Start service
systemctl start synapse-serendipity

# Verify functionality
curl -X GET http://localhost:5000/api/serendipity
```

---

*This deployment guide ensures proper setup, monitoring, and maintenance of the Serendipity Analysis feature in production environments.*