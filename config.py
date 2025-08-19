"""
Configuration module for Synapse AI Web Application

This module provides centralized configuration management with support for
environment variables, different deployment environments, and secure defaults.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Base configuration class with common settings"""
    
    # Flask Configuration
    @property
    def SECRET_KEY(self):
        return os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    @property
    def TEMPLATES_AUTO_RELOAD(self):
        return os.environ.get('TEMPLATES_AUTO_RELOAD', 'True').lower() == 'true'
    
    # AI Model Configuration
    @property
    def OLLAMA_MODEL(self):
        return os.environ.get('OLLAMA_MODEL', 'llama3:8b')
    
    @property
    def OLLAMA_HOST(self):
        return os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    
    @property
    def OLLAMA_TIMEOUT(self):
        return int(os.environ.get('OLLAMA_TIMEOUT', '30'))
    
    # Memory and Storage Configuration
    @property
    def MEMORY_FILE(self):
        return os.environ.get('MEMORY_FILE', 'memory.json')
    
    @property
    def PROMPT_CONFIG_FILE(self):
        return os.environ.get('PROMPT_CONFIG_FILE', 'prompt_config.json')
    
    @property
    def MAX_MEMORY_FILE_SIZE(self):
        return int(os.environ.get('MAX_MEMORY_FILE_SIZE', '10485760'))  # 10MB
    
    # Performance Configuration
    @property
    def MAX_CONVERSATION_LENGTH(self):
        return int(os.environ.get('MAX_CONVERSATION_LENGTH', '100'))
    
    @property
    def CONVERSATION_CLEANUP_THRESHOLD(self):
        return int(os.environ.get('CONVERSATION_CLEANUP_THRESHOLD', '80'))
    
    @property
    def INSIGHT_GENERATION_THRESHOLD(self):
        return int(os.environ.get('INSIGHT_GENERATION_THRESHOLD', '5'))
    
    @property
    def RESPONSE_TIMEOUT(self):
        return int(os.environ.get('RESPONSE_TIMEOUT', '60'))
    
    @property
    def STREAMING_TIMEOUT(self):
        return int(os.environ.get('STREAMING_TIMEOUT', '180'))  # 3 minutes for streaming
    
    # Security Configuration
    @property
    def MAX_MESSAGE_LENGTH(self):
        return int(os.environ.get('MAX_MESSAGE_LENGTH', '10000'))
    
    @property
    def MAX_PROMPT_LENGTH(self):
        return int(os.environ.get('MAX_PROMPT_LENGTH', '5000'))
    
    @property
    def ALLOWED_FILE_EXTENSIONS(self):
        return os.environ.get('ALLOWED_FILE_EXTENSIONS', '.json,.txt,.md').split(',')
    
    @property
    def SANITIZE_ERRORS(self):
        return os.environ.get('SANITIZE_ERRORS', 'True').lower() == 'true'
    
    # Logging Configuration
    @property
    def LOG_LEVEL(self):
        return os.environ.get('LOG_LEVEL', 'INFO')
    
    @property
    def LOG_FILE(self):
        return os.environ.get('LOG_FILE', 'synapse_errors.log')
    
    @property
    def LOG_MAX_SIZE(self):
        return int(os.environ.get('LOG_MAX_SIZE', '1048576'))  # 1MB
    
    @property
    def LOG_BACKUP_COUNT(self):
        return int(os.environ.get('LOG_BACKUP_COUNT', '3'))
    
    # Application Paths
    PROJECT_ROOT = Path(__file__).parent
    TEMPLATES_DIR = PROJECT_ROOT / 'templates'
    STATIC_DIR = PROJECT_ROOT / 'static'
    
    # Feature Flags
    @property
    def ENABLE_MEMORY_PROCESSING(self):
        return os.environ.get('ENABLE_MEMORY_PROCESSING', 'True').lower() == 'true'
    
    @property
    def ENABLE_SERENDIPITY_ENGINE(self):
        return os.environ.get('ENABLE_SERENDIPITY_ENGINE', 'True').lower() == 'true'
    
    @property
    def ENABLE_PROMPT_CUSTOMIZATION(self):
        return os.environ.get('ENABLE_PROMPT_CUSTOMIZATION', 'True').lower() == 'true'
    
    @property
    def ENABLE_PERFORMANCE_MONITORING(self):
        return os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'True').lower() == 'true'
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary for easy access"""
        config_dict = {}
        for key in dir(self):
            if not key.startswith('_') and not callable(getattr(type(self), key, None)):
                try:
                    value = getattr(self, key)
                    if not callable(value):
                        config_dict[key] = value
                except:
                    # Skip properties that might fail
                    pass
        return config_dict
    
    def validate_config(self) -> Dict[str, str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check required files and directories
        if not self.TEMPLATES_DIR.exists():
            issues.append(f"Templates directory not found: {self.TEMPLATES_DIR}")
        
        if not self.STATIC_DIR.exists():
            issues.append(f"Static directory not found: {self.STATIC_DIR}")
        
        # Validate numeric ranges
        if self.MAX_CONVERSATION_LENGTH <= 0:
            issues.append("MAX_CONVERSATION_LENGTH must be positive")
        
        if self.CONVERSATION_CLEANUP_THRESHOLD >= self.MAX_CONVERSATION_LENGTH:
            issues.append("CONVERSATION_CLEANUP_THRESHOLD must be less than MAX_CONVERSATION_LENGTH")
        
        if self.RESPONSE_TIMEOUT <= 0:
            issues.append("RESPONSE_TIMEOUT must be positive")
        
        # Validate file size limits
        if self.MAX_MEMORY_FILE_SIZE <= 0:
            issues.append("MAX_MEMORY_FILE_SIZE must be positive")
        
        if self.MAX_MESSAGE_LENGTH <= 0:
            issues.append("MAX_MESSAGE_LENGTH must be positive")
        
        return issues


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    @property
    def LOG_LEVEL(self):
        return os.environ.get('LOG_LEVEL', 'DEBUG')
    
    # Shorter timeouts for faster development iteration
    @property
    def OLLAMA_TIMEOUT(self):
        return int(os.environ.get('OLLAMA_TIMEOUT', '15'))
    
    @property
    def RESPONSE_TIMEOUT(self):
        return int(os.environ.get('RESPONSE_TIMEOUT', '30'))
    
    # Smaller limits for development testing
    @property
    def MAX_CONVERSATION_LENGTH(self):
        return int(os.environ.get('MAX_CONVERSATION_LENGTH', '50'))
    
    @property
    def CONVERSATION_CLEANUP_THRESHOLD(self):
        return int(os.environ.get('CONVERSATION_CLEANUP_THRESHOLD', '40'))


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Override SECRET_KEY to get from environment at runtime
    @property
    def SECRET_KEY(self):
        return os.environ.get('SECRET_KEY') or super().SECRET_KEY
    
    # Disable template auto-reload in production
    @property
    def TEMPLATES_AUTO_RELOAD(self):
        return False
    
    # More conservative timeouts in production
    @property
    def OLLAMA_TIMEOUT(self):
        return int(os.environ.get('OLLAMA_TIMEOUT', '60'))
    
    @property
    def RESPONSE_TIMEOUT(self):
        return int(os.environ.get('RESPONSE_TIMEOUT', '120'))
    
    @property
    def STREAMING_TIMEOUT(self):
        return int(os.environ.get('STREAMING_TIMEOUT', '300'))  # 5 minutes for production streaming
    
    # Larger limits for production use
    @property
    def MAX_CONVERSATION_LENGTH(self):
        return int(os.environ.get('MAX_CONVERSATION_LENGTH', '200'))
    
    @property
    def CONVERSATION_CLEANUP_THRESHOLD(self):
        return int(os.environ.get('CONVERSATION_CLEANUP_THRESHOLD', '150'))
    
    # Enhanced security in production
    @property
    def SANITIZE_ERRORS(self):
        return True


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory or temporary files for testing
    @property
    def MEMORY_FILE(self):
        return os.environ.get('TEST_MEMORY_FILE', 'test_memory.json')
    
    @property
    def PROMPT_CONFIG_FILE(self):
        return os.environ.get('TEST_PROMPT_CONFIG_FILE', 'test_prompt_config.json')
    
    @property
    def LOG_FILE(self):
        return os.environ.get('TEST_LOG_FILE', 'test_synapse_errors.log')
    
    # Faster timeouts for testing
    @property
    def OLLAMA_TIMEOUT(self):
        return int(os.environ.get('OLLAMA_TIMEOUT', '5'))
    
    @property
    def RESPONSE_TIMEOUT(self):
        return int(os.environ.get('RESPONSE_TIMEOUT', '10'))
    
    @property
    def STREAMING_TIMEOUT(self):
        return int(os.environ.get('STREAMING_TIMEOUT', '30'))  # 30 seconds for testing
    
    # Smaller limits for faster testing
    @property
    def MAX_CONVERSATION_LENGTH(self):
        return int(os.environ.get('MAX_CONVERSATION_LENGTH', '20'))
    
    @property
    def CONVERSATION_CLEANUP_THRESHOLD(self):
        return int(os.environ.get('CONVERSATION_CLEANUP_THRESHOLD', '15'))
    
    @property
    def MAX_MEMORY_FILE_SIZE(self):
        return int(os.environ.get('MAX_MEMORY_FILE_SIZE', '1048576'))  # 1MB
    
    # Disable some features for testing isolation
    @property
    def ENABLE_PERFORMANCE_MONITORING(self):
        return False


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration class based on environment
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config_map.get(config_name, config_map['default'])
    config_instance = config_class()
    
    # Validate production-specific requirements
    if config_name == 'production' and not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    return config_instance


def print_config_summary(config: Config) -> None:
    """Print a summary of current configuration (for debugging)"""
    print("=== Synapse Configuration Summary ===")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {getattr(config, 'DEBUG', False)}")
    print(f"AI Model: {config.OLLAMA_MODEL}")
    print(f"Ollama Host: {config.OLLAMA_HOST}")
    print(f"Max Conversation Length: {config.MAX_CONVERSATION_LENGTH}")
    print(f"Response Timeout: {config.RESPONSE_TIMEOUT}s")
    print(f"Streaming Timeout: {config.STREAMING_TIMEOUT}s")
    print(f"Memory File: {config.MEMORY_FILE}")
    print(f"Log Level: {config.LOG_LEVEL}")
    print(f"Templates Auto-Reload: {config.TEMPLATES_AUTO_RELOAD}")
    
    # Feature flags
    print("\n=== Feature Flags ===")
    print(f"Memory Processing: {config.ENABLE_MEMORY_PROCESSING}")
    print(f"Serendipity Engine: {config.ENABLE_SERENDIPITY_ENGINE}")
    print(f"Prompt Customization: {config.ENABLE_PROMPT_CUSTOMIZATION}")
    print(f"Performance Monitoring: {config.ENABLE_PERFORMANCE_MONITORING}")
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        print("\n=== Configuration Issues ===")
        for issue in issues:
            print(f"⚠️  {issue}")
    else:
        print("\n✅ Configuration validation passed")
    
    print("=" * 40)


if __name__ == '__main__':
    # When run directly, print configuration summary
    config = get_config()
    print_config_summary(config)