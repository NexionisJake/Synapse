# Synapse AI Web Application - Setup Guide

This guide will help you set up and run the Synapse AI web application on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version` or `python3 --version`

2. **Ollama**
   - Download from [ollama.ai](https://ollama.ai/)
   - Follow the installation instructions for your operating system
   - Verify installation: `ollama --version`

3. **Git** (optional, for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/)

### System Requirements

- **RAM**: Minimum 8GB (16GB recommended for optimal AI model performance)
- **Storage**: At least 5GB free space for the AI model and application data
- **Network**: Internet connection required for initial model download

## Installation Steps

### Step 1: Get the Application

If you have the source code in a directory, navigate to it:
```bash
cd synapse-project
```

### Step 2: Set Up Python Virtual Environment

Create and activate a virtual environment to isolate dependencies:

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 3: Install Python Dependencies

Install all required Python packages:
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Ollama and AI Model

1. **Start Ollama service:**
   ```bash
   ollama serve
   ```
   Keep this terminal window open - Ollama needs to run in the background.

2. **Download the AI model** (in a new terminal window):
   ```bash
   ollama pull llama3:8b
   ```
   This will download approximately 4.7GB of model data. The download may take several minutes depending on your internet connection.

3. **Verify the model is available:**
   ```bash
   ollama list
   ```
   You should see `llama3:8b` in the list.

### Step 5: Configure the Application (Optional)

The application works with default settings, but you can customize it using environment variables or by editing the configuration.

#### Environment Variables

Create a `.env` file in the project directory (optional):
```bash
# AI Configuration
OLLAMA_MODEL=llama3:8b
OLLAMA_HOST=http://localhost:11434

# Application Settings
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Performance Settings
MAX_CONVERSATION_LENGTH=100
RESPONSE_TIMEOUT=60

# Feature Flags
ENABLE_MEMORY_PROCESSING=True
ENABLE_SERENDIPITY_ENGINE=True
ENABLE_PROMPT_CUSTOMIZATION=True
```

#### Configuration Validation

Test your configuration:
```bash
python config.py
```
This will display your current configuration and validate settings.

## Running the Application

### Method 1: Using the Startup Script (Recommended)

Use the provided startup script:

**On Windows:**
```bash
start_synapse.bat
```

**On macOS/Linux:**
```bash
./start_synapse.sh
```

### Method 2: Manual Startup

1. **Ensure Ollama is running:**
   ```bash
   ollama serve
   ```

2. **Activate virtual environment** (if not already active):
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Start the Flask application:**
   ```bash
   python app.py
   ```

### Accessing the Application

Once the application is running, open your web browser and navigate to:
- **Main Chat Interface**: http://localhost:5000
- **Cognitive Dashboard**: http://localhost:5000/dashboard
- **Prompt Management**: http://localhost:5000/prompts

## Verification and Testing

### Quick Health Check

1. **Test AI Connection:**
   Visit http://localhost:5000/api/status in your browser. You should see a JSON response indicating the AI service is connected.

2. **Test Chat Functionality:**
   - Go to http://localhost:5000
   - Type a message and press Enter or click Send
   - You should receive a response from the AI

3. **Run Test Suite:**
   ```bash
   python run_tests_simple.py
   ```

### Troubleshooting Common Issues

#### Issue: "Connection refused" or Ollama not responding

**Solution:**
1. Ensure Ollama is running: `ollama serve`
2. Check if the model is downloaded: `ollama list`
3. Verify Ollama is accessible: `curl http://localhost:11434/api/version`

#### Issue: Python module not found

**Solution:**
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`

#### Issue: Port 5000 already in use

**Solution:**
1. Find and stop the process using port 5000
2. Or set a different port: `export FLASK_RUN_PORT=5001` (Linux/Mac) or `set FLASK_RUN_PORT=5001` (Windows)

#### Issue: AI responses are very slow

**Solution:**
1. Ensure you have sufficient RAM (8GB minimum)
2. Close other resource-intensive applications
3. Consider using a smaller model if available

#### Issue: Memory or insight features not working

**Solution:**
1. Check file permissions in the project directory
2. Ensure the application can create and write to `memory.json`
3. Check the logs in `synapse_errors.log`

## Development Setup

If you plan to modify or develop the application:

### Additional Development Dependencies

Install development and testing dependencies:
```bash
pip install pytest pytest-cov pytest-mock coverage
```

### Running Tests

Run the complete test suite:
```bash
# Simple test runner
python run_tests_simple.py

# Or use pytest directly
pytest

# With coverage report
pytest --cov=. --cov-report=html
```

### Code Structure

```
synapse-project/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── SETUP.md              # This setup guide
├── start_synapse.sh      # Startup script (Linux/Mac)
├── start_synapse.bat     # Startup script (Windows)
├── memory.json           # AI memory storage (created automatically)
├── prompt_config.json    # Prompt configurations (created automatically)
├── synapse_errors.log    # Application logs (created automatically)
├── templates/            # HTML templates
├── static/               # CSS, JavaScript, and images
└── tests/                # Test files
```

## Production Deployment

For production deployment:

1. **Set production environment:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secure-secret-key
   ```

2. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Configure reverse proxy** (nginx, Apache) for better performance and security.

## Support and Troubleshooting

### Log Files

Check these files for debugging information:
- `synapse_errors.log` - Application error logs
- Console output - Real-time application status

### Configuration Check

Run configuration validation:
```bash
python config.py
```

### Performance Monitoring

Access performance metrics at:
http://localhost:5000/api/performance/status

### Getting Help

1. Check the troubleshooting section above
2. Review log files for error messages
3. Ensure all prerequisites are properly installed
4. Verify Ollama is running and the model is downloaded

## Next Steps

Once the application is running successfully:

1. **Explore the Chat Interface** - Start having conversations with your AI
2. **Check the Dashboard** - View accumulated insights and conversation patterns
3. **Customize Prompts** - Tailor the AI's personality to your preferences
4. **Review Memory Features** - See how the AI builds long-term memory from your conversations

Enjoy using Synapse, your intelligent cognitive partner!