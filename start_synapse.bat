@echo off
REM Synapse AI Web Application Startup Script (Windows)
REM This script handles the complete startup process for the Synapse application

setlocal enabledelayedexpansion

REM Configuration
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
if "%OLLAMA_MODEL%"=="" set "OLLAMA_MODEL=llama3:8b"
if "%FLASK_PORT%"=="" set "FLASK_PORT=5000"
if "%FLASK_HOST%"=="" set "FLASK_HOST=127.0.0.1"

REM Colors (limited support in Windows)
set "INFO_PREFIX=[INFO]"
set "SUCCESS_PREFIX=[SUCCESS]"
set "WARNING_PREFIX=[WARNING]"
set "ERROR_PREFIX=[ERROR]"

REM Function to print status messages
:print_status
echo %INFO_PREFIX% %~1
goto :eof

:print_success
echo %SUCCESS_PREFIX% %~1
goto :eof

:print_warning
echo %WARNING_PREFIX% %~1
goto :eof

:print_error
echo %ERROR_PREFIX% %~1
goto :eof

REM Function to check if a command exists
:command_exists
where %1 >nul 2>&1
goto :eof

REM Function to check if Ollama is running
:check_ollama_running
curl -s "http://localhost:11434/api/version" >nul 2>&1
goto :eof

REM Function to check if model is available
:check_model_available
ollama list | findstr /C:"%OLLAMA_MODEL%" >nul 2>&1
goto :eof

REM Function to start Ollama if not running
:start_ollama
call :check_ollama_running
if %errorlevel%==0 (
    call :print_success "Ollama is already running"
    goto :eof
)

call :print_status "Starting Ollama service..."

call :command_exists ollama
if %errorlevel% neq 0 (
    call :print_error "Ollama command not found. Please install Ollama first."
    exit /b 1
)

REM Start Ollama in background
start /B ollama serve > ollama.log 2>&1

REM Wait for Ollama to start (up to 30 seconds)
for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    call :check_ollama_running
    if !errorlevel!==0 (
        call :print_success "Ollama started successfully"
        goto :eof
    )
)

call :print_error "Failed to start Ollama within 30 seconds"
exit /b 1

REM Function to ensure model is downloaded
:ensure_model
call :check_model_available
if %errorlevel%==0 (
    call :print_success "Model %OLLAMA_MODEL% is available"
    goto :eof
)

call :print_status "Downloading model %OLLAMA_MODEL% (this may take several minutes)..."
ollama pull "%OLLAMA_MODEL%"
if %errorlevel%==0 (
    call :print_success "Model %OLLAMA_MODEL% downloaded successfully"
    goto :eof
) else (
    call :print_error "Failed to download model %OLLAMA_MODEL%"
    exit /b 1
)

REM Function to setup Python virtual environment
:setup_venv
if not exist "%VENV_DIR%" (
    call :print_status "Creating Python virtual environment..."
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        call :print_error "Failed to create virtual environment"
        exit /b 1
    )
    call :print_success "Virtual environment created"
) else (
    call :print_status "Virtual environment already exists"
)

REM Activate virtual environment
call :print_status "Activating virtual environment..."
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
call :print_status "Upgrading pip..."
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
if exist "%SCRIPT_DIR%requirements.txt" (
    call :print_status "Installing Python dependencies..."
    pip install -r "%SCRIPT_DIR%requirements.txt" >nul 2>&1
    if %errorlevel%==0 (
        call :print_success "Dependencies installed"
    ) else (
        call :print_warning "Some dependencies may have failed to install"
    )
) else (
    call :print_warning "requirements.txt not found, skipping dependency installation"
)
goto :eof

REM Function to validate configuration
:validate_config
call :print_status "Validating configuration..."

cd /d "%SCRIPT_DIR%"

if exist "config.py" (
    python config.py >nul 2>&1
    if %errorlevel%==0 (
        call :print_success "Configuration validation passed"
    ) else (
        call :print_warning "Configuration validation failed, but continuing..."
    )
) else (
    call :print_warning "config.py not found, using default configuration"
)
goto :eof

REM Function to check if port is available
:check_port_available
netstat -an | findstr ":%FLASK_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    exit /b 1
) else (
    exit /b 0
)

REM Function to start the Flask application
:start_flask
cd /d "%SCRIPT_DIR%"

REM Check if port is available
call :check_port_available
if %errorlevel% neq 0 (
    call :print_error "Port %FLASK_PORT% is already in use"
    call :print_status "You can set a different port with: set FLASK_PORT=5001"
    exit /b 1
)

call :print_status "Starting Synapse AI Web Application..."
call :print_status "Server will be available at: http://%FLASK_HOST%:%FLASK_PORT%"
call :print_status "Press Ctrl+C to stop the application"

REM Set environment variables
if "%FLASK_ENV%"=="" set "FLASK_ENV=development"
set "FLASK_RUN_HOST=%FLASK_HOST%"
set "FLASK_RUN_PORT=%FLASK_PORT%"

REM Start the application
python app.py
goto :eof

REM Function to show help
:show_help
echo Synapse AI Web Application Startup Script
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   -h, --help          Show this help message
echo   -p, --port PORT     Set Flask port (default: 5000)
echo   -H, --host HOST     Set Flask host (default: 127.0.0.1)
echo   -m, --model MODEL   Set Ollama model (default: llama3:8b)
echo   --no-ollama         Skip Ollama startup (assume it's already running)
echo   --dev               Run in development mode
echo   --prod              Run in production mode
echo.
echo Environment Variables:
echo   FLASK_PORT          Flask server port
echo   FLASK_HOST          Flask server host
echo   OLLAMA_MODEL        AI model to use
echo   FLASK_ENV           Flask environment (development/production)
echo.
echo Examples:
echo   %~nx0                  # Start with default settings
echo   %~nx0 -p 8080          # Start on port 8080
echo   %~nx0 --no-ollama      # Start without managing Ollama
echo   %~nx0 --prod           # Start in production mode
goto :eof

REM Main execution
:main
set "skip_ollama=false"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :start_execution
if "%~1"=="-h" goto :show_help_and_exit
if "%~1"=="--help" goto :show_help_and_exit
if "%~1"=="-p" (
    set "FLASK_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--port" (
    set "FLASK_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-H" (
    set "FLASK_HOST=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--host" (
    set "FLASK_HOST=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-m" (
    set "OLLAMA_MODEL=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--model" (
    set "OLLAMA_MODEL=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--no-ollama" (
    set "skip_ollama=true"
    shift
    goto :parse_args
)
if "%~1"=="--dev" (
    set "FLASK_ENV=development"
    shift
    goto :parse_args
)
if "%~1"=="--prod" (
    set "FLASK_ENV=production"
    shift
    goto :parse_args
)

call :print_error "Unknown option: %~1"
call :show_help
exit /b 1

:show_help_and_exit
call :show_help
exit /b 0

:start_execution
call :print_status "Starting Synapse AI Web Application..."
call :print_status "Environment: %FLASK_ENV%"
call :print_status "Model: %OLLAMA_MODEL%"
call :print_status "Host: %FLASK_HOST%:%FLASK_PORT%"

REM Check prerequisites
call :command_exists python
if %errorlevel% neq 0 (
    call :print_error "Python is required but not installed"
    exit /b 1
)

if "%skip_ollama%"=="false" (
    call :command_exists ollama
    if !errorlevel! neq 0 (
        call :print_error "Ollama is required but not installed"
        call :print_status "Install Ollama from: https://ollama.ai/"
        exit /b 1
    )
)

REM Setup Python environment
call :setup_venv
if %errorlevel% neq 0 exit /b 1

REM Handle Ollama
if "%skip_ollama%"=="false" (
    call :start_ollama
    if !errorlevel! neq 0 exit /b 1
    call :ensure_model
    if !errorlevel! neq 0 exit /b 1
) else (
    call :print_status "Skipping Ollama management (--no-ollama specified)"
    call :check_ollama_running
    if !errorlevel! neq 0 (
        call :print_warning "Ollama doesn't appear to be running"
    )
)

REM Validate configuration
call :validate_config

REM Start the application
call :start_flask

goto :eof

REM Entry point
call :main %*