#!/bin/bash

# Synapse AI Web Application Startup Script (Linux/macOS)
# This script handles the complete startup process for the Synapse application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3:8b}"
FLASK_PORT="${FLASK_PORT:-5000}"
FLASK_HOST="${FLASK_HOST:-127.0.0.1}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Ollama is running
check_ollama_running() {
    if curl -s "http://localhost:11434/api/version" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if model is available
check_model_available() {
    if ollama list | grep -q "$OLLAMA_MODEL"; then
        return 0
    else
        return 1
    fi
}

# Function to start Ollama if not running
start_ollama() {
    if check_ollama_running; then
        print_success "Ollama is already running"
        return 0
    fi
    
    print_status "Starting Ollama service..."
    
    # Try to start Ollama in the background
    if command_exists ollama; then
        # Start Ollama in background
        nohup ollama serve > ollama.log 2>&1 &
        OLLAMA_PID=$!
        
        # Wait for Ollama to start (up to 30 seconds)
        for i in {1..30}; do
            if check_ollama_running; then
                print_success "Ollama started successfully (PID: $OLLAMA_PID)"
                echo $OLLAMA_PID > ollama.pid
                return 0
            fi
            sleep 1
        done
        
        print_error "Failed to start Ollama within 30 seconds"
        return 1
    else
        print_error "Ollama command not found. Please install Ollama first."
        return 1
    fi
}

# Function to ensure model is downloaded
ensure_model() {
    if check_model_available; then
        print_success "Model $OLLAMA_MODEL is available"
        return 0
    fi
    
    print_status "Downloading model $OLLAMA_MODEL (this may take several minutes)..."
    if ollama pull "$OLLAMA_MODEL"; then
        print_success "Model $OLLAMA_MODEL downloaded successfully"
        return 0
    else
        print_error "Failed to download model $OLLAMA_MODEL"
        return 1
    fi
}

# Function to setup Python virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip >/dev/null 2>&1
    
    # Install requirements
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found, skipping dependency installation"
    fi
}

# Function to validate configuration
validate_config() {
    print_status "Validating configuration..."
    
    cd "$SCRIPT_DIR"
    
    if [ -f "config.py" ]; then
        if python config.py >/dev/null 2>&1; then
            print_success "Configuration validation passed"
        else
            print_warning "Configuration validation failed, but continuing..."
        fi
    else
        print_warning "config.py not found, using default configuration"
    fi
}

# Function to check if port is available
check_port_available() {
    if lsof -Pi :$FLASK_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to start the Flask application
start_flask() {
    cd "$SCRIPT_DIR"
    
    # Check if port is available
    if ! check_port_available; then
        print_error "Port $FLASK_PORT is already in use"
        print_status "You can set a different port with: export FLASK_PORT=5001"
        return 1
    fi
    
    print_status "Starting Synapse AI Web Application..."
    print_status "Server will be available at: http://$FLASK_HOST:$FLASK_PORT"
    print_status "Press Ctrl+C to stop the application"
    
    # Set environment variables
    export FLASK_ENV="${FLASK_ENV:-development}"
    export FLASK_RUN_HOST="$FLASK_HOST"
    export FLASK_RUN_PORT="$FLASK_PORT"
    
    # Start the application
    python app.py
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    
    # Kill Ollama if we started it
    if [ -f "ollama.pid" ]; then
        OLLAMA_PID=$(cat ollama.pid)
        if kill -0 "$OLLAMA_PID" 2>/dev/null; then
            print_status "Stopping Ollama (PID: $OLLAMA_PID)..."
            kill "$OLLAMA_PID"
        fi
        rm -f ollama.pid
    fi
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Synapse AI Web Application Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -p, --port PORT     Set Flask port (default: 5000)"
    echo "  -H, --host HOST     Set Flask host (default: 127.0.0.1)"
    echo "  -m, --model MODEL   Set Ollama model (default: llama3:8b)"
    echo "  --no-ollama         Skip Ollama startup (assume it's already running)"
    echo "  --dev               Run in development mode"
    echo "  --prod              Run in production mode"
    echo ""
    echo "Environment Variables:"
    echo "  FLASK_PORT          Flask server port"
    echo "  FLASK_HOST          Flask server host"
    echo "  OLLAMA_MODEL        AI model to use"
    echo "  FLASK_ENV           Flask environment (development/production)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Start with default settings"
    echo "  $0 -p 8080          # Start on port 8080"
    echo "  $0 --no-ollama      # Start without managing Ollama"
    echo "  $0 --prod           # Start in production mode"
}

# Main execution
main() {
    local skip_ollama=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -p|--port)
                FLASK_PORT="$2"
                shift 2
                ;;
            -H|--host)
                FLASK_HOST="$2"
                shift 2
                ;;
            -m|--model)
                OLLAMA_MODEL="$2"
                shift 2
                ;;
            --no-ollama)
                skip_ollama=true
                shift
                ;;
            --dev)
                export FLASK_ENV=development
                shift
                ;;
            --prod)
                export FLASK_ENV=production
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Set up signal handlers for cleanup
    trap cleanup EXIT INT TERM
    
    print_status "Starting Synapse AI Web Application..."
    print_status "Environment: ${FLASK_ENV:-development}"
    print_status "Model: $OLLAMA_MODEL"
    print_status "Host: $FLASK_HOST:$FLASK_PORT"
    
    # Check prerequisites
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command_exists ollama && [ "$skip_ollama" = false ]; then
        print_error "Ollama is required but not installed"
        print_status "Install Ollama from: https://ollama.ai/"
        exit 1
    fi
    
    # Setup Python environment
    setup_venv
    
    # Handle Ollama
    if [ "$skip_ollama" = false ]; then
        start_ollama || exit 1
        ensure_model || exit 1
    else
        print_status "Skipping Ollama management (--no-ollama specified)"
        if ! check_ollama_running; then
            print_warning "Ollama doesn't appear to be running"
        fi
    fi
    
    # Validate configuration
    validate_config
    
    # Start the application
    start_flask
}

# Run main function with all arguments
main "$@"