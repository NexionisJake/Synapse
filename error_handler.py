"""
Comprehensive Error Handling Module for Synapse AI Web Application

This module provides centralized error handling, logging, and recovery mechanisms
for all components of the Synapse application.
"""

import logging
import traceback
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better classification"""
    AI_SERVICE = "ai_service"
    MEMORY_SERVICE = "memory_service"
    SERENDIPITY_SERVICE = "serendipity_service"
    PROMPT_SERVICE = "prompt_service"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

class ErrorHandler:
    """
    Centralized error handling and logging system
    """
    
    def __init__(self, log_file: str = "synapse_errors.log", max_log_size: int = 10 * 1024 * 1024):
        """
        Initialize the error handler
        
        Args:
            log_file: Path to the error log file
            max_log_size: Maximum log file size in bytes (default: 10MB)
        """
        self.log_file = log_file
        self.max_log_size = max_log_size
        self.error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "last_error": None,
            "session_start": datetime.now().isoformat()
        }
        
        # Setup logging
        self._setup_logging()
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file) if os.path.dirname(self.log_file) else "."
        os.makedirs(log_dir, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('synapse_error_handler')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create file handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_log_size,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_error(self, 
                  error: Exception, 
                  category: ErrorCategory = ErrorCategory.UNKNOWN,
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  context: Dict[str, Any] = None,
                  user_message: str = None) -> Dict[str, Any]:
        """
        Log an error with comprehensive details
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level of the error
            context: Additional context information
            user_message: User-friendly error message
            
        Returns:
            dict: Error information for API responses
        """
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
        
        error_info = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "severity": severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_message": user_message or self._generate_user_message(error, category),
            "context": context or {},
            "traceback": traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        }
        
        # Update statistics
        self._update_error_stats(category, severity, error_info)
        
        # Log the error
        log_level = self._get_log_level(severity)
        self.logger.log(log_level, f"[{error_id}] {category.value}: {str(error)}", extra=error_info)
        
        # For critical errors, also log to console
        if severity == ErrorSeverity.CRITICAL:
            print(f"CRITICAL ERROR [{error_id}]: {str(error)}")
        
        return error_info
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """
        Generate user-friendly error messages based on error type and category
        
        Args:
            error: The exception that occurred
            category: Category of the error
            
        Returns:
            str: User-friendly error message
        """
        error_type = type(error).__name__
        error_str = str(error).lower()
        
        # AI Service errors
        if category == ErrorCategory.AI_SERVICE:
            if "connection" in error_str or "network" in error_str:
                return "Unable to connect to the AI service. Please ensure Ollama is running and try again."
            elif "model" in error_str:
                return "The AI model is not available. Please check that the required model is installed."
            elif "timeout" in error_str:
                return "The AI service is taking too long to respond. Please try again."
            else:
                return "The AI service encountered an error. Please try again in a moment."
        
        # Memory Service errors
        elif category == ErrorCategory.MEMORY_SERVICE:
            if "json" in error_str:
                return "There was an issue processing your conversation data. Your conversation is safe, but insights may not be saved."
            elif "file" in error_str:
                return "Unable to save conversation insights. Please check file permissions and try again."
            else:
                return "There was an issue processing your conversation for insights. Please try again."
        
        # File System errors
        elif category == ErrorCategory.FILE_SYSTEM:
            if "permission" in error_str:
                return "File permission error. Please check that the application has write access to its directory."
            elif "disk" in error_str or "space" in error_str:
                return "Insufficient disk space. Please free up some space and try again."
            elif "not found" in error_str:
                return "A required file was not found. The application will attempt to recreate it."
            else:
                return "File system error occurred. Please check file permissions and disk space."
        
        # Network errors
        elif category == ErrorCategory.NETWORK:
            return "Network connection error. Please check your internet connection and try again."
        
        # Validation errors
        elif category == ErrorCategory.VALIDATION:
            return f"Invalid input: {str(error)}"
        
        # Configuration errors
        elif category == ErrorCategory.CONFIGURATION:
            return "Configuration error. The application will use default settings."
        
        # Default message
        else:
            return "An unexpected error occurred. Please try again, and contact support if the problem persists."
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get logging level based on error severity"""
        severity_to_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_to_level.get(severity, logging.WARNING)
    
    def _update_error_stats(self, category: ErrorCategory, severity: ErrorSeverity, error_info: Dict[str, Any]):
        """Update error statistics"""
        self.error_stats["total_errors"] += 1
        self.error_stats["last_error"] = error_info["timestamp"]
        
        # Update category stats
        cat_key = category.value
        if cat_key not in self.error_stats["errors_by_category"]:
            self.error_stats["errors_by_category"][cat_key] = 0
        self.error_stats["errors_by_category"][cat_key] += 1
        
        # Update severity stats
        sev_key = severity.value
        if sev_key not in self.error_stats["errors_by_severity"]:
            self.error_stats["errors_by_severity"][sev_key] = 0
        self.error_stats["errors_by_severity"][sev_key] += 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return self.error_stats.copy()
    
    def clear_error_stats(self):
        """Clear error statistics (useful for testing)"""
        self.error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "last_error": None,
            "session_start": datetime.now().isoformat()
        }

# Global error handler instance
_error_handler_instance = None

def get_error_handler() -> ErrorHandler:
    """Get or create the global error handler instance"""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler()
    return _error_handler_instance

def handle_service_error(category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    Decorator for handling service errors
    
    Args:
        category: Error category
        severity: Error severity level
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                error_info = error_handler.log_error(e, category, severity, context)
                
                # Re-raise with additional context
                raise type(e)(error_info["user_message"]) from e
        return wrapper
    return decorator

def safe_file_operation(operation: Callable, fallback_value=None, error_category: ErrorCategory = ErrorCategory.FILE_SYSTEM):
    """
    Safely execute a file operation with error handling
    
    Args:
        operation: The file operation to execute
        fallback_value: Value to return if operation fails
        error_category: Category for error logging
        
    Returns:
        Result of operation or fallback_value if operation fails
    """
    try:
        return operation()
    except Exception as e:
        error_handler = get_error_handler()
        error_handler.log_error(e, error_category, ErrorSeverity.MEDIUM)
        return fallback_value

def create_error_response(error_info: Dict[str, Any], http_status: int = 500) -> tuple:
    """
    Create a standardized error response for Flask endpoints
    
    Args:
        error_info: Error information from error handler
        http_status: HTTP status code
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        "error": True,
        "error_id": error_info["error_id"],
        "message": error_info["user_message"],
        "category": error_info["category"],
        "timestamp": error_info["timestamp"]
    }
    
    # Include additional details for development
    if os.getenv("FLASK_ENV") == "development":
        response["details"] = {
            "error_type": error_info["error_type"],
            "error_message": error_info["error_message"]
        }
    
    return response, http_status

class RecoveryManager:
    """
    Manages error recovery strategies
    """
    
    @staticmethod
    def recover_corrupted_json_file(file_path: str, backup_data: Dict[str, Any] = None) -> bool:
        """
        Attempt to recover a corrupted JSON file
        
        Args:
            file_path: Path to the corrupted file
            backup_data: Default data structure to use if recovery fails
            
        Returns:
            bool: True if recovery was successful
        """
        try:
            # Create backup of corrupted file
            if os.path.exists(file_path):
                backup_path = f"{file_path}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(file_path, backup_path)
                get_error_handler().logger.info(f"Backed up corrupted file to {backup_path}")
            
            # Create new file with backup data or empty structure
            if backup_data is None:
                backup_data = {"created_at": datetime.now().isoformat(), "recovered": True}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            get_error_handler().logger.info(f"Successfully recovered file: {file_path}")
            return True
            
        except Exception as e:
            get_error_handler().log_error(e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH)
            return False
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            get_error_handler().log_error(e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.MEDIUM)
            return False
    
    @staticmethod
    def check_disk_space(path: str = ".", min_space_mb: int = 100) -> bool:
        """
        Check if there's sufficient disk space
        
        Args:
            path: Path to check disk space for
            min_space_mb: Minimum required space in MB
            
        Returns:
            bool: True if sufficient space is available
        """
        try:
            import shutil
            free_bytes = shutil.disk_usage(path).free
            free_mb = free_bytes / (1024 * 1024)
            return free_mb >= min_space_mb
        except Exception as e:
            get_error_handler().log_error(e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.LOW)
            return True  # Assume space is available if we can't check