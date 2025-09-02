"""
Comprehensive Tests for Serendipity Configuration Management

This module contains unit tests for serendipity-specific configuration,
feature toggling, environment variable handling, and integration scenarios.
"""

import unittest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules to test
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, get_config
from serendipity_service import get_serendipity_service, reset_serendipity_service, SerendipityServiceError


class TestSerendipityConfiguration(unittest.TestCase):
    """Test cases for serendipity configuration management"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Store original environment variables
        self.original_env = {}
        serendipity_env_vars = [
            'ENABLE_SERENDIPITY_ENGINE',
            'SERENDIPITY_MIN_INSIGHTS',
            'SERENDIPITY_MAX_MEMORY_SIZE_MB',
            'SERENDIPITY_ANALYSIS_TIMEOUT'
        ]
        
        for var in serendipity_env_vars:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        # Reset serendipity service instance
        reset_serendipity_service()
    
    def tearDown(self):
        """Clean up after each test method"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
        
        # Reset serendipity service instance
        reset_serendipity_service()
    
    def test_default_serendipity_configuration(self):
        """Test default serendipity configuration values"""
        config = Config()
        
        # Test default values
        self.assertTrue(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertEqual(config.SERENDIPITY_MIN_INSIGHTS, 3)
        self.assertEqual(config.SERENDIPITY_MAX_MEMORY_SIZE_MB, 50)
        self.assertEqual(config.SERENDIPITY_ANALYSIS_TIMEOUT, 120)
    
    def test_serendipity_environment_variable_override(self):
        """Test serendipity configuration override via environment variables"""
        # Set environment variables
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '5'
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '100'
        os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '180'
        
        config = Config()
        
        # Test overridden values
        self.assertFalse(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertEqual(config.SERENDIPITY_MIN_INSIGHTS, 5)
        self.assertEqual(config.SERENDIPITY_MAX_MEMORY_SIZE_MB, 100)
        self.assertEqual(config.SERENDIPITY_ANALYSIS_TIMEOUT, 180)
    
    def test_serendipity_boolean_parsing(self):
        """Test boolean parsing for ENABLE_SERENDIPITY_ENGINE"""
        test_cases = [
            ('True', True),
            ('true', True),
            ('TRUE', True),
            ('1', False),  # Only 'true' (case insensitive) should be True
            ('False', False),
            ('false', False),
            ('FALSE', False),
            ('0', False),
            ('', False),
            ('invalid', False)
        ]
        
        for env_value, expected in test_cases:
            with self.subTest(env_value=env_value):
                os.environ['ENABLE_SERENDIPITY_ENGINE'] = env_value
                config = Config()
                self.assertEqual(config.ENABLE_SERENDIPITY_ENGINE, expected)
                del os.environ['ENABLE_SERENDIPITY_ENGINE']
    
    def test_serendipity_numeric_validation(self):
        """Test numeric configuration validation"""
        # Test valid numeric values
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '10'
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '200'
        os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '300'
        
        config = Config()
        self.assertEqual(config.SERENDIPITY_MIN_INSIGHTS, 10)
        self.assertEqual(config.SERENDIPITY_MAX_MEMORY_SIZE_MB, 200)
        self.assertEqual(config.SERENDIPITY_ANALYSIS_TIMEOUT, 300)
    
    def test_serendipity_invalid_numeric_values(self):
        """Test handling of invalid numeric configuration values"""
        # Test invalid numeric values (should raise ValueError)
        invalid_values = ['invalid', '', 'abc', '1.5']
        
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                os.environ['SERENDIPITY_MIN_INSIGHTS'] = invalid_value
                
                with self.assertRaises(ValueError):
                    config = Config()
                    _ = config.SERENDIPITY_MIN_INSIGHTS
                
                del os.environ['SERENDIPITY_MIN_INSIGHTS']
    
    def test_configuration_validation_with_serendipity_enabled(self):
        """Test configuration validation when serendipity is enabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '5'
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '100'
        os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '180'
        
        config = Config()
        issues = config.validate_config()
        
        # Should have no serendipity-related issues
        serendipity_issues = [issue for issue in issues if 'SERENDIPITY' in issue]
        self.assertEqual(len(serendipity_issues), 0)
    
    def test_configuration_validation_with_invalid_serendipity_values(self):
        """Test configuration validation with invalid serendipity values"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '0'  # Invalid: must be positive
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '-1'  # Invalid: must be positive
        os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '0'  # Invalid: must be positive
        
        config = Config()
        issues = config.validate_config()
        
        # Should have serendipity-related issues
        expected_issues = [
            "SERENDIPITY_MIN_INSIGHTS must be positive",
            "SERENDIPITY_MAX_MEMORY_SIZE_MB must be positive",
            "SERENDIPITY_ANALYSIS_TIMEOUT must be positive"
        ]
        
        for expected_issue in expected_issues:
            self.assertIn(expected_issue, issues)
    
    def test_configuration_validation_with_serendipity_disabled(self):
        """Test configuration validation when serendipity is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '0'  # Would be invalid if enabled
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '-1'  # Would be invalid if enabled
        
        config = Config()
        issues = config.validate_config()
        
        # Should have no serendipity-related issues when disabled
        serendipity_issues = [issue for issue in issues if 'SERENDIPITY' in issue]
        self.assertEqual(len(serendipity_issues), 0)
    
    def test_development_config_serendipity_defaults(self):
        """Test serendipity configuration in development environment"""
        config = DevelopmentConfig()
        
        # Should inherit base configuration
        self.assertTrue(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertEqual(config.SERENDIPITY_MIN_INSIGHTS, 3)
        self.assertEqual(config.SERENDIPITY_MAX_MEMORY_SIZE_MB, 50)
        self.assertEqual(config.SERENDIPITY_ANALYSIS_TIMEOUT, 120)
    
    def test_production_config_serendipity_defaults(self):
        """Test serendipity configuration in production environment"""
        config = ProductionConfig()
        
        # Should inherit base configuration
        self.assertTrue(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertEqual(config.SERENDIPITY_MIN_INSIGHTS, 3)
        self.assertEqual(config.SERENDIPITY_MAX_MEMORY_SIZE_MB, 50)
        self.assertEqual(config.SERENDIPITY_ANALYSIS_TIMEOUT, 120)
    
    def test_testing_config_serendipity_defaults(self):
        """Test serendipity configuration in testing environment"""
        config = TestingConfig()
        
        # Should inherit base configuration
        self.assertTrue(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertEqual(config.SERENDIPITY_MIN_INSIGHTS, 3)
        self.assertEqual(config.SERENDIPITY_MAX_MEMORY_SIZE_MB, 50)
        self.assertEqual(config.SERENDIPITY_ANALYSIS_TIMEOUT, 120)
    
    def test_get_config_dict_includes_serendipity(self):
        """Test that get_config_dict includes serendipity configuration"""
        config = Config()
        config_dict = config.get_config_dict()
        
        # Check that serendipity configuration is included
        self.assertIn('ENABLE_SERENDIPITY_ENGINE', config_dict)
        self.assertIn('SERENDIPITY_MIN_INSIGHTS', config_dict)
        self.assertIn('SERENDIPITY_MAX_MEMORY_SIZE_MB', config_dict)
        self.assertIn('SERENDIPITY_ANALYSIS_TIMEOUT', config_dict)
        
        # Check values
        self.assertTrue(config_dict['ENABLE_SERENDIPITY_ENGINE'])
        self.assertEqual(config_dict['SERENDIPITY_MIN_INSIGHTS'], 3)
        self.assertEqual(config_dict['SERENDIPITY_MAX_MEMORY_SIZE_MB'], 50)
        self.assertEqual(config_dict['SERENDIPITY_ANALYSIS_TIMEOUT'], 120)


class TestSerendipityFeatureToggling(unittest.TestCase):
    """Test cases for serendipity feature toggling functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Store original environment variables
        self.original_env = os.environ.get('ENABLE_SERENDIPITY_ENGINE')
        if 'ENABLE_SERENDIPITY_ENGINE' in os.environ:
            del os.environ['ENABLE_SERENDIPITY_ENGINE']
        
        # Reset serendipity service instance
        reset_serendipity_service()
    
    def tearDown(self):
        """Clean up after each test method"""
        # Restore original environment variable
        if self.original_env is not None:
            os.environ['ENABLE_SERENDIPITY_ENGINE'] = self.original_env
        elif 'ENABLE_SERENDIPITY_ENGINE' in os.environ:
            del os.environ['ENABLE_SERENDIPITY_ENGINE']
        
        # Reset serendipity service instance
        reset_serendipity_service()
    
    @patch('serendipity_service.get_ai_service')
    def test_serendipity_service_enabled(self, mock_get_ai_service):
        """Test serendipity service initialization when enabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Mock AI service
        mock_ai_service = Mock()
        mock_get_ai_service.return_value = mock_ai_service
        
        config = get_config()
        service = get_serendipity_service(config=config)
        
        # Service should be initialized
        self.assertIsNotNone(service)
        self.assertTrue(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertIsNotNone(service.ai_service)
        mock_get_ai_service.assert_called_once()
    
    def test_serendipity_service_disabled(self):
        """Test serendipity service initialization when disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        config = get_config()
        service = get_serendipity_service(config=config)
        
        # Service should be initialized but AI service should be None
        self.assertIsNotNone(service)
        self.assertFalse(config.ENABLE_SERENDIPITY_ENGINE)
        self.assertIsNone(service.ai_service)
    
    def test_serendipity_analysis_when_disabled(self):
        """Test serendipity analysis when service is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        config = get_config()
        service = get_serendipity_service(config=config)
        
        # Analysis should raise error when disabled
        with self.assertRaises(SerendipityServiceError) as context:
            service.analyze_memory()
        
        self.assertIn("disabled", str(context.exception).lower())
    
    def test_serendipity_service_status_when_enabled(self):
        """Test service status when serendipity is enabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        config = get_config()
        service = get_serendipity_service(config=config)
        status = service.get_service_status()
        
        # Status should indicate enabled
        self.assertTrue(status['enabled'])
        self.assertIn('model', status)
        self.assertIn('min_insights_required', status)
        self.assertIn('max_memory_size_mb', status)
        self.assertIn('analysis_timeout', status)
    
    def test_serendipity_service_status_when_disabled(self):
        """Test service status when serendipity is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        config = get_config()
        service = get_serendipity_service(config=config)
        status = service.get_service_status()
        
        # Status should indicate disabled
        self.assertFalse(status['enabled'])
        self.assertFalse(status['ai_service_available'])
    
    def test_feature_toggle_runtime_change(self):
        """Test that feature toggle changes are reflected at runtime"""
        # Start with enabled
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        config1 = get_config()
        self.assertTrue(config1.ENABLE_SERENDIPITY_ENGINE)
        
        # Change to disabled
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        config2 = get_config()
        self.assertFalse(config2.ENABLE_SERENDIPITY_ENGINE)
        
        # Change back to enabled
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        config3 = get_config()
        self.assertTrue(config3.ENABLE_SERENDIPITY_ENGINE)


class TestSerendipityConfigurationIntegration(unittest.TestCase):
    """Test cases for serendipity configuration integration scenarios"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Store original environment variables
        self.original_env = {}
        env_vars = [
            'ENABLE_SERENDIPITY_ENGINE',
            'SERENDIPITY_MIN_INSIGHTS',
            'SERENDIPITY_MAX_MEMORY_SIZE_MB',
            'SERENDIPITY_ANALYSIS_TIMEOUT',
            'MEMORY_FILE'
        ]
        
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        # Reset serendipity service instance
        reset_serendipity_service()
    
    def tearDown(self):
        """Clean up after each test method"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
        
        # Reset serendipity service instance
        reset_serendipity_service()
    
    def test_serendipity_service_uses_config_parameters(self):
        """Test that serendipity service uses configuration parameters"""
        # Set custom configuration
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '10'
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '200'
        os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '300'
        
        config = get_config()
        service = get_serendipity_service(config=config)
        
        # Service should use configuration values
        self.assertEqual(service.min_insights_required, 10)
        self.assertEqual(service.max_memory_size_mb, 200)
        self.assertEqual(service.analysis_timeout, 300)
    
    def test_serendipity_service_with_memory_file_config(self):
        """Test serendipity service with custom memory file configuration"""
        # Create temporary memory file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            test_memory_data = {
                "insights": [
                    {"content": "Test insight 1", "category": "test"},
                    {"content": "Test insight 2", "category": "test"},
                    {"content": "Test insight 3", "category": "test"}
                ],
                "conversation_summaries": []
            }
            json.dump(test_memory_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Set configuration
            os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
            os.environ['MEMORY_FILE'] = temp_file_path
            
            config = get_config()
            service = get_serendipity_service(config=config)
            
            # Service should use the configured memory file
            self.assertEqual(service.config.MEMORY_FILE, temp_file_path)
            
            # Should be able to load memory data
            memory_data = service._load_memory_data()
            self.assertEqual(len(memory_data['insights']), 3)
            
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)
    
    def test_configuration_summary_includes_serendipity(self):
        """Test that configuration summary includes serendipity settings"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '5'
        os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '100'
        os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '180'
        
        config = get_config()
        
        # Capture print output
        import io
        import sys
        from config import print_config_summary
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            print_config_summary(config)
            output = captured_output.getvalue()
            
            # Check that serendipity configuration is included
            self.assertIn("Serendipity Engine: True", output)
            self.assertIn("Serendipity Engine Configuration", output)
            self.assertIn("Min Insights Required: 5", output)
            self.assertIn("Max Memory Size (MB): 100", output)
            self.assertIn("Analysis Timeout (s): 180", output)
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_configuration_summary_serendipity_disabled(self):
        """Test configuration summary when serendipity is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        config = get_config()
        
        # Capture print output
        import io
        import sys
        from config import print_config_summary
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            print_config_summary(config)
            output = captured_output.getvalue()
            
            # Check that serendipity is shown as disabled
            self.assertIn("Serendipity Engine: False", output)
            # Should not include detailed serendipity configuration
            self.assertNotIn("Serendipity Engine Configuration", output)
            
        finally:
            sys.stdout = sys.__stdout__


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)