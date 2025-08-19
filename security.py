"""
Security Module for Synapse AI Web Application

This module provides comprehensive security measures including input validation,
sanitization, file system access restrictions, and resource limits.
"""

import os
import re
import json
import html
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from functools import wraps
from flask import request, jsonify

# Configure logging
logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration constants"""
    
    # Input validation limits
    MAX_MESSAGE_LENGTH = 10000  # Maximum characters per message
    MAX_CONVERSATION_LENGTH = 200  # Maximum messages in conversation
    MAX_PROMPT_LENGTH = 5000  # Maximum characters in system prompt
    MAX_JSON_SIZE = 1024 * 1024  # Maximum JSON payload size (1MB)
    
    # File system restrictions
    ALLOWED_EXTENSIONS = {'.json', '.txt', '.log', '.md'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # Maximum file size (10MB)
    RESTRICTED_PATHS = {
        '/etc', '/usr', '/bin', '/sbin', '/root', '/home',
        'C:\\Windows', 'C:\\Program Files', 'C:\\Users'
    }
    
    # Content filtering patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # eval() calls
        r'exec\s*\(',  # exec() calls
        r'import\s+os',  # OS imports
        r'__import__',  # Dynamic imports
        r'subprocess',  # Subprocess calls
        r'system\s*\(',  # System calls
    ]
    
    # Sensitive information patterns
    SENSITIVE_PATTERNS = [
        r'password\s*[:=]\s*["\']?([^"\'\\s]+)',
        r'api[_-]?key\s*[:=]\s*["\']?([^"\'\\s]+)',
        r'secret\s*[:=]\s*["\']?([^"\'\\s]+)',
        r'token\s*[:=]\s*["\']?([^"\'\\s]+)',
        r'/[a-zA-Z]:/.*',  # Windows paths
        r'/home/[^/\\s]+',  # Unix home paths
        r'/etc/[^\\s]+',  # System config paths
    ]

class InputValidator:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def validate_message_content(content: str) -> tuple[bool, str]:
        """
        Validate and sanitize message content
        
        Args:
            content: Message content to validate
            
        Returns:
            tuple: (is_valid, sanitized_content_or_error_message)
        """
        if not isinstance(content, str):
            return False, "Message content must be a string"
        
        # Check length
        if len(content) > SecurityConfig.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {SecurityConfig.MAX_MESSAGE_LENGTH} characters)"
        
        # Check for empty content
        if not content.strip():
            return False, "Message content cannot be empty"
        
        # Sanitize HTML
        sanitized = html.escape(content)
        
        # Check for dangerous patterns (check original content before HTML escaping)
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, "Message contains potentially dangerous content"
        
        return True, sanitized
    
    @staticmethod
    def validate_conversation_history(conversation: List[Dict[str, Any]]) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """
        Validate and sanitize conversation history
        
        Args:
            conversation: List of conversation messages
            
        Returns:
            tuple: (is_valid, sanitized_conversation_or_error_message)
        """
        if not isinstance(conversation, list):
            return False, "Conversation must be a list"
        
        # Check conversation length
        if len(conversation) > SecurityConfig.MAX_CONVERSATION_LENGTH:
            return False, f"Conversation too long (max {SecurityConfig.MAX_CONVERSATION_LENGTH} messages)"
        
        sanitized_conversation = []
        
        for i, message in enumerate(conversation):
            if not isinstance(message, dict):
                return False, f"Message at index {i} must be an object"
            
            # Validate required fields
            if 'role' not in message or 'content' not in message:
                return False, f"Message at index {i} must have 'role' and 'content' fields"
            
            # Validate role
            if message['role'] not in ['user', 'assistant', 'system']:
                return False, f"Invalid role at index {i}: must be 'user', 'assistant', or 'system'"
            
            # Validate and sanitize content
            is_valid, result = InputValidator.validate_message_content(message['content'])
            if not is_valid:
                return False, f"Invalid content at index {i}: {result}"
            
            # Create sanitized message
            sanitized_message = {
                'role': message['role'],
                'content': result
            }
            
            # Preserve timestamp if present
            if 'timestamp' in message:
                sanitized_message['timestamp'] = message['timestamp']
            
            sanitized_conversation.append(sanitized_message)
        
        return True, sanitized_conversation
    
    @staticmethod
    def validate_prompt_content(prompt: str) -> tuple[bool, str]:
        """
        Validate system prompt content
        
        Args:
            prompt: System prompt to validate
            
        Returns:
            tuple: (is_valid, sanitized_prompt_or_error_message)
        """
        if not isinstance(prompt, str):
            return False, "Prompt must be a string"
        
        # Check length
        if len(prompt) > SecurityConfig.MAX_PROMPT_LENGTH:
            return False, f"Prompt too long (max {SecurityConfig.MAX_PROMPT_LENGTH} characters)"
        
        # Check for empty content
        if not prompt.strip():
            return False, "Prompt cannot be empty"
        
        # Sanitize HTML
        sanitized = html.escape(prompt)
        
        # Check for dangerous patterns (check original content before HTML escaping)
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False, "Prompt contains potentially dangerous content"
        
        return True, sanitized
    
    @staticmethod
    def validate_json_payload(data: Any, max_size: int = None) -> tuple[bool, str]:
        """
        Validate JSON payload size and structure
        
        Args:
            data: JSON data to validate
            max_size: Maximum size in bytes (optional)
            
        Returns:
            tuple: (is_valid, error_message_if_invalid)
        """
        if max_size is None:
            max_size = SecurityConfig.MAX_JSON_SIZE
        
        try:
            # Check size
            json_str = json.dumps(data)
            if len(json_str.encode('utf-8')) > max_size:
                return False, f"JSON payload too large (max {max_size} bytes)"
            
            return True, ""
        except Exception as e:
            return False, f"Invalid JSON data: {str(e)}"

class FileSystemSecurity:
    """File system access restrictions and security"""
    
    def __init__(self, project_root: str = None):
        """
        Initialize file system security
        
        Args:
            project_root: Root directory for the project (defaults to current directory)
        """
        self.project_root = Path(project_root or os.getcwd()).resolve()
        logger.info(f"File system security initialized with project root: {self.project_root}")
    
    def is_path_allowed(self, file_path: str) -> tuple[bool, str]:
        """
        Check if a file path is allowed within security restrictions
        
        Args:
            file_path: Path to check
            
        Returns:
            tuple: (is_allowed, error_message_if_not_allowed)
        """
        try:
            # Handle relative paths by joining with project root
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_root, file_path)
            
            # Resolve the path
            resolved_path = Path(file_path).resolve()
            
            # Check if path is within project root
            try:
                resolved_path.relative_to(self.project_root)
            except ValueError:
                return False, "File access outside project directory is not allowed"
            
            # Check for restricted system paths (only for absolute paths that somehow got through)
            path_str = str(resolved_path)
            for restricted in SecurityConfig.RESTRICTED_PATHS:
                if path_str.startswith(restricted) and not path_str.startswith(str(self.project_root)):
                    return False, f"Access to system directory '{restricted}' is not allowed"
            
            # Check file extension if it's a file
            if resolved_path.suffix and resolved_path.suffix.lower() not in SecurityConfig.ALLOWED_EXTENSIONS:
                return False, f"File extension '{resolved_path.suffix}' is not allowed"
            
            return True, ""
            
        except Exception as e:
            return False, f"Invalid file path: {str(e)}"
    
    def validate_file_size(self, file_path: str) -> tuple[bool, str]:
        """
        Validate file size against security limits
        
        Args:
            file_path: Path to file to check
            
        Returns:
            tuple: (is_valid, error_message_if_invalid)
        """
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > SecurityConfig.MAX_FILE_SIZE:
                    return False, f"File too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)"
            return True, ""
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"
    
    def safe_file_operation(self, file_path: str, operation: str = "read") -> tuple[bool, str]:
        """
        Perform comprehensive file security check
        
        Args:
            file_path: Path to file
            operation: Type of operation ('read', 'write', 'delete')
            
        Returns:
            tuple: (is_allowed, error_message_if_not_allowed)
        """
        # Check path restrictions
        is_allowed, error_msg = self.is_path_allowed(file_path)
        if not is_allowed:
            return False, error_msg
        
        # Check file size for existing files
        if operation in ['read', 'write'] and os.path.exists(file_path):
            is_valid, error_msg = self.validate_file_size(file_path)
            if not is_valid:
                return False, error_msg
        
        return True, ""

class ErrorSanitizer:
    """Sanitize error messages to prevent information disclosure"""
    
    @staticmethod
    def sanitize_error_message(error_message: str, error_type: str = None) -> str:
        """
        Sanitize error message to remove sensitive information
        
        Args:
            error_message: Original error message
            error_type: Type of error (optional)
            
        Returns:
            str: Sanitized error message
        """
        if not isinstance(error_message, str):
            return "An error occurred"
        
        sanitized = error_message
        
        # Remove sensitive information patterns
        for pattern in SecurityConfig.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Remove absolute paths
        sanitized = re.sub(r'[A-Za-z]:[\\\/][^\\s]*', '[PATH]', sanitized)
        sanitized = re.sub(r'\/[^\\s]*\/[^\\s]*', '[PATH]', sanitized)
        
        # Remove stack trace information
        if 'Traceback' in sanitized or 'File "' in sanitized:
            return "An internal error occurred. Please try again."
        
        # Generic error messages for common issues
        if any(keyword in sanitized.lower() for keyword in ['permission denied', 'access denied']):
            return "Access denied. Please check permissions."
        
        if any(keyword in sanitized.lower() for keyword in ['no such file', 'file not found']):
            return "Required file not found."
        
        if any(keyword in sanitized.lower() for keyword in ['connection refused', 'connection failed']):
            return "Service connection failed. Please try again."
        
        return sanitized

# Global instances
_file_system_security = None

def get_file_system_security() -> FileSystemSecurity:
    """Get or create the global file system security instance"""
    global _file_system_security
    if _file_system_security is None:
        _file_system_security = FileSystemSecurity()
    return _file_system_security

def security_required(validate_json: bool = True, validate_conversation: bool = False):
    """
    Decorator to add security validation to Flask routes
    
    Args:
        validate_json: Whether to validate JSON payload
        validate_conversation: Whether to validate conversation history
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate content type for POST requests
                if request.method == 'POST':
                    if not request.is_json:
                        return jsonify({
                            "error": "Invalid request format",
                            "message": "Request must be JSON"
                        }), 400
                
                # Validate JSON payload size
                if validate_json and request.method == 'POST':
                    data = request.get_json()
                    if data is not None:
                        is_valid, error_msg = InputValidator.validate_json_payload(data)
                        if not is_valid:
                            return jsonify({
                                "error": "Invalid request",
                                "message": error_msg
                            }), 400
                
                # Validate conversation history if required
                if validate_conversation and request.method == 'POST':
                    data = request.get_json()
                    if data and 'conversation' in data:
                        is_valid, result = InputValidator.validate_conversation_history(data['conversation'])
                        if not is_valid:
                            return jsonify({
                                "error": "Invalid conversation data",
                                "message": result
                            }), 400
                        # Replace with sanitized conversation
                        data['conversation'] = result
                
                return func(*args, **kwargs)
                
            except Exception as e:
                # Sanitize error message
                sanitized_message = ErrorSanitizer.sanitize_error_message(str(e))
                logger.error(f"Security validation error: {str(e)}")
                return jsonify({
                    "error": "Security validation failed",
                    "message": sanitized_message
                }), 400
        
        return wrapper
    return decorator

def validate_file_access(file_path: str, operation: str = "read") -> tuple[bool, str]:
    """
    Validate file access with security restrictions
    
    Args:
        file_path: Path to file
        operation: Type of operation
        
    Returns:
        tuple: (is_allowed, error_message_if_not_allowed)
    """
    fs_security = get_file_system_security()
    return fs_security.safe_file_operation(file_path, operation)

def sanitize_error_for_user(error: Exception, context: str = None) -> str:
    """
    Sanitize an exception for user display
    
    Args:
        error: Exception to sanitize
        context: Additional context (optional)
        
    Returns:
        str: Sanitized error message
    """
    error_message = str(error)
    error_type = type(error).__name__
    
    # Add context if provided
    if context:
        error_message = f"{context}: {error_message}"
    
    return ErrorSanitizer.sanitize_error_message(error_message, error_type)