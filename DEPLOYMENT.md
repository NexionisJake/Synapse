# Synapse AI Web Application - Deployment Guide

This guide covers deployment options for the Synapse AI web application.

## Quick Start

For most users, follow the [SETUP.md](SETUP.md) guide for local development and testing.

## Configuration Management

### Environment Variables

The application supports configuration through environment variables. Create a `.env` file in the project directory:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### Configuration Validation

Test your configuration:
```bash
python config.py
```

This will display your current configuration and validate all settings.

## Deployment Options

### Option 1: Local Development (Recommended)

Use the provided startup scripts:

**Linux/macOS:**
```bash
./start_synapse.sh
```

**Windows:**
```bash
start_synapse.bat
```

### Option 2: Manual Startup

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Set environment variables:**
   ```bash
   export FLASK_ENV=development
   export OLLAMA_MODEL=llama3:8b
   ```

3. **Start Ollama:**
   ```bash
   ollama serve
   ```

4. **Start the application:**
   ```bash
   python app.py
   ```

### Option 3: Production Deployment

For production deployment with a WSGI server:

1. **Install production dependencies:**
   ```bash
   pip install gunicorn
   ```

2. **Set production environment:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secure-secret-key
   ```

3. **Run with Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Option 4: Docker Deployment

Docker provides an isolated, reproducible environment for running Synapse. This is the recommended approach for production deployments and team environments.

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 1.29+
- Ollama running on host machine OR as a separate container

#### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NexionisJake/Synapse.git
   cd Synapse
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure for Docker:
   ```bash
   # Ollama connection (adjust based on your setup)
   OLLAMA_HOST=http://host.docker.internal:11434  # Docker Desktop (Windows/macOS)
   # OLLAMA_HOST=http://172.17.0.1:11434         # Linux
   
   OLLAMA_MODEL=llama3:8b
   FLASK_ENV=production
   SECRET_KEY=your-secure-random-secret-key-here
   
   # Performance settings
   STREAMING_TIMEOUT=180
   RESPONSE_TIMEOUT=60
   MAX_CONVERSATION_LENGTH=200
   ```

3. **Build and start**:
   ```bash
   docker-compose up --build -d
   ```

4. **Verify deployment**:
   ```bash
   # Check container status
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   
   # Test health endpoint
   curl http://localhost:5000/api/status
   ```

5. **Access application** at `http://localhost:5000`

#### Docker Architecture

**Container Structure:**
```
synapse_app (container)
├── Python 3.11 slim base
├── Gunicorn WSGI server (4 workers)
├── Synapse application code
├── Non-root user (synapse:synapse)
└── Mounted volumes:
    ├── ./memory.json → /app/memory.json
    └── ./synapse_errors.log → /app/synapse_errors.log
```

**Key Features:**
- ✅ **Security**: Runs as non-root user
- ✅ **Performance**: Gunicorn with 4 workers, 120s timeout
- ✅ **Health Checks**: Automatic monitoring via `/api/status`
- ✅ **Persistence**: Data persisted via volume mounts
- ✅ **Auto-restart**: `restart: unless-stopped` policy

#### Ollama Integration Options

**Option 1: Ollama on Host (Recommended)**

Run Ollama directly on your host machine:
```bash
# Start Ollama
ollama serve

# Pull model
ollama pull llama3:8b
```

In `.env`:
```bash
# Docker Desktop (Windows/macOS)
OLLAMA_HOST=http://host.docker.internal:11434

# Linux
OLLAMA_HOST=http://172.17.0.1:11434
```

**Option 2: Ollama in Separate Container**

Uncomment the Ollama service in `docker-compose.yml`:
```yaml
services:
  synapse:
    # ... existing config ...
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

In `.env`:
```bash
OLLAMA_HOST=http://ollama:11434
```

Then pull the model:
```bash
docker-compose exec ollama ollama pull llama3:8b
```

#### Production Configuration

**1. Generate Secure Secret Key**:
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```
Add to `.env` as `SECRET_KEY`.

**2. Enable Production Features**:
```bash
FLASK_ENV=production
SANITIZE_ERRORS=True
LOG_LEVEL=WARNING
```

**3. Optimize Resource Limits**:

Edit `docker-compose.yml`:
```yaml
services:
  synapse:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

**4. Add Reverse Proxy (nginx)**:

Create `nginx.conf`:
```nginx
upstream synapse {
    server localhost:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://synapse;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts for AI responses
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

#### Docker Management

**Daily Operations:**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs (follow mode)
docker-compose logs -f synapse

# View last 100 lines
docker-compose logs --tail=100 synapse

# Execute commands in container
docker-compose exec synapse python config.py
```

**Updates and Maintenance:**
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up --build -d

# Clean up old images
docker image prune -a

# Backup data
cp memory.json memory.json.backup.$(date +%Y%m%d)
cp synapse_errors.log synapse_errors.log.backup.$(date +%Y%m%d)
```

**Monitoring:**
```bash
# Container resource usage
docker stats synapse_app

# Health check
curl http://localhost:5000/api/status

# Performance metrics
curl http://localhost:5000/api/performance/status

# Memory statistics
curl http://localhost:5000/api/memory/stats
```

#### Troubleshooting Docker Deployment

**Container won't start:**
```bash
# Check logs for errors
docker-compose logs synapse

# Verify configuration
docker-compose config

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Ollama connection issues:**
```bash
# Test from container
docker-compose exec synapse curl http://host.docker.internal:11434/api/tags

# Verify Ollama on host
ollama list
curl http://localhost:11434/api/tags
```

**Performance issues:**
```bash
# Check resource usage
docker stats synapse_app

# Increase worker count (edit docker-compose.yml CMD)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", "--timeout", "180", "app:app"]

# Rebuild and restart
docker-compose up --build -d
```

**Data persistence issues:**
```bash
# Verify volume mounts
docker-compose exec synapse ls -la /app/memory.json

# Check file permissions
ls -la memory.json synapse_errors.log

# Fix permissions (if needed)
chmod 666 memory.json synapse_errors.log
```

#### Advanced Docker Configurations

**Multi-Stage Build (Optimized Image)**

Create `Dockerfile.optimized`:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . .

# Create non-root user
RUN addgroup --system synapse && adduser --system --ingroup synapse synapse
RUN chown -R synapse:synapse /app
USER synapse

EXPOSE 5000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

**Docker Compose Override for Development**

Create `docker-compose.override.yml`:
```yaml
version: "3.8"

services:
  synapse:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - FLASK_ENV=development
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app  # Live code reload
    command: ["python", "app.py"]  # Development server
```

Use with:
```bash
# Development mode (auto-applied)
docker-compose up

# Production mode (ignore override)
docker-compose -f docker-compose.yml up
```

#### Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use strong SECRET_KEY** in production
3. **Run as non-root user** (already configured)
4. **Keep base images updated**:
   ```bash
   docker-compose build --pull
   ```
5. **Scan for vulnerabilities**:
   ```bash
   docker scan synapse_app
   ```
6. **Limit container capabilities**:
   ```yaml
   security_opt:
     - no-new-privileges:true
   cap_drop:
     - ALL
   cap_add:
     - NET_BIND_SERVICE
   ```

#### Backup and Recovery

**Backup Data:**
```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

cp memory.json $BACKUP_DIR/
cp synapse_errors.log $BACKUP_DIR/
cp .env $BACKUP_DIR/

echo "Backup saved to $BACKUP_DIR"
```

**Restore Data:**
```bash
cp backups/20250123_120000/memory.json .
cp backups/20250123_120000/.env .
docker-compose restart
```

For additional deployment scenarios and optimization, see [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md

EXPOSE 5000
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t synapse-ai .
docker run -p 5000:5000 -e FLASK_ENV=production synapse-ai
```

## Environment-Specific Configuration

### Development Environment

```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
export MAX_CONVERSATION_LENGTH=50
```

### Production Environment

```bash
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key
export LOG_LEVEL=INFO
export MAX_CONVERSATION_LENGTH=200
export SANITIZE_ERRORS=True
```

### Testing Environment

```bash
export FLASK_ENV=testing
export MEMORY_FILE=test_memory.json
export LOG_FILE=test_synapse_errors.log
```

## Security Considerations

### Production Security

1. **Set a secure SECRET_KEY:**
   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **Enable error sanitization:**
   ```bash
   export SANITIZE_ERRORS=True
   ```

3. **Use HTTPS in production** (configure reverse proxy)

4. **Restrict file access** (application automatically restricts to project directory)

### Network Security

- The application runs on localhost by default
- For network access, set `FLASK_RUN_HOST=0.0.0.0` (use with caution)
- Consider using a reverse proxy (nginx, Apache) for production

## Monitoring and Maintenance

### Log Files

Monitor these files:
- `synapse_errors.log` - Application errors and warnings
- `ollama.log` - Ollama service logs (if using startup scripts)

### Performance Monitoring

Access performance metrics:
```bash
curl http://localhost:5000/api/performance/status
```

### Health Checks

Check application health:
```bash
curl http://localhost:5000/api/status
```

### Cleanup and Maintenance

1. **Clear error statistics:**
   ```bash
   curl -X POST http://localhost:5000/api/errors/clear
   ```

2. **Trigger performance cleanup:**
   ```bash
   curl -X POST http://localhost:5000/api/performance/cleanup
   ```

3. **Backup memory data:**
   ```bash
   cp memory.json memory.json.backup
   ```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   export FLASK_RUN_PORT=5001
   ```

2. **Ollama connection failed:**
   - Ensure Ollama is running: `ollama serve`
   - Check model is available: `ollama list`

3. **Configuration errors:**
   - Run configuration validation: `python config.py`
   - Check environment variables: `env | grep FLASK`

4. **Permission errors:**
   - Ensure write permissions in project directory
   - Check log file permissions

### Debug Mode

Enable debug mode for detailed error information:
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
```

### Getting Help

1. Check log files for error messages
2. Run configuration validation
3. Verify all prerequisites are installed
4. Test Ollama connection independently

## Scaling and Performance

### Performance Tuning

1. **Adjust conversation limits:**
   ```bash
   export MAX_CONVERSATION_LENGTH=200
   export CONVERSATION_CLEANUP_THRESHOLD=150
   ```

2. **Optimize timeouts:**
   ```bash
   export OLLAMA_TIMEOUT=60
   export RESPONSE_TIMEOUT=120
   ```

3. **Enable performance monitoring:**
   ```bash
   export ENABLE_PERFORMANCE_MONITORING=True
   ```

### Resource Requirements

- **Minimum**: 8GB RAM, 2 CPU cores
- **Recommended**: 16GB RAM, 4 CPU cores
- **Storage**: 10GB free space (for AI model and data)

## Backup and Recovery

### Data Backup

Important files to backup:
- `memory.json` - AI memory and insights
- `prompt_config.json` - Custom prompts
- `.env` - Environment configuration

### Recovery

To restore from backup:
1. Copy backed up files to project directory
2. Restart the application
3. Verify data integrity through the dashboard

## Support

For additional support:
1. Review the [SETUP.md](SETUP.md) guide
2. Check configuration with `python config.py`
3. Monitor log files for error details
4. Verify system requirements are met