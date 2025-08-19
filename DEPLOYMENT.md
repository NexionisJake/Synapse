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

### Option 4: Docker Deployment (Advanced)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

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