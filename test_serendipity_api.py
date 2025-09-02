"""
Tests for Serendipity API Endpoint

This module contains tests for the Flask API endpoint that handles
serendipity analysis requests and feature toggling.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import Flask app and related modules
from app import app
from config import get_config
from serendipity_service import reset_serendipity_service


class TestSerendipityAPI(unittest.TestCase):
    """Test cases for serendipity API endpoint"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Configure Flask app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
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
    
    def test_serendipity_api_head_enabled(self):
        """Test HEAD request when serendipity is enabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        response = self.client.head('/api/serendipity')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'')
    
    def test_serendipity_api_head_disabled(self):
        """Test HEAD request when serendipity is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        response = self.client.head('/api/serendipity')
        
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, b'')
    
    def test_serendipity_api_get_enabled(self):
        """Test GET request when serendipity is enabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        with patch('serendipity_service.get_serendipity_service') as mock_get_service:
            # Mock service and status
            mock_service = Mock()
            mock_service.get_service_status.return_value = {
                'enabled': True,
                'ai_service_available': True,
                'model': 'llama3:8b'
            }
            mock_get_service.return_value = mock_service
            
            response = self.client.get('/api/serendipity')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            self.assertTrue(data['enabled'])
            self.assertEqual(data['status'], 'available')
            self.assertIn('service_info', data)
            self.assertIn('timestamp', data)
    
    def test_serendipity_api_get_disabled(self):
        """Test GET request when serendipity is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        response = self.client.get('/api/serendipity')
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        
        self.assertFalse(data['enabled'])
        self.assertEqual(data['status'], 'disabled')
        self.assertIn('message', data)
    
    @patch('serendipity_service.get_serendipity_service')
    def test_serendipity_api_post_success(self, mock_get_service):
        """Test successful POST request for analysis"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Mock service and analysis results
        mock_service = Mock()
        mock_analysis_results = {
            'connections': [
                {
                    'title': 'Test Connection',
                    'description': 'A test connection',
                    'surprise_factor': 0.8,
                    'relevance': 0.9
                }
            ],
            'meta_patterns': [],
            'serendipity_summary': 'Test summary',
            'recommendations': ['Test recommendation'],
            'metadata': {
                'analysis_timestamp': '2024-01-01T00:00:00',
                'model_used': 'llama3:8b'
            }
        }
        mock_service.analyze_memory.return_value = mock_analysis_results
        mock_get_service.return_value = mock_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('connections', data)
        self.assertIn('meta_patterns', data)
        self.assertIn('serendipity_summary', data)
        self.assertIn('recommendations', data)
        self.assertIn('metadata', data)
        self.assertEqual(len(data['connections']), 1)
        self.assertEqual(data['connections'][0]['title'], 'Test Connection')
    
    def test_serendipity_api_post_disabled(self):
        """Test POST request when serendipity is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('disabled', data['message'].lower())
    
    @patch('serendipity_service.get_serendipity_service')
    def test_serendipity_api_post_service_error(self, mock_get_service):
        """Test POST request when service raises an error"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Mock service to raise SerendipityServiceError
        from serendipity_service import SerendipityServiceError
        mock_service = Mock()
        mock_service.analyze_memory.side_effect = SerendipityServiceError("Test error")
        mock_get_service.return_value = mock_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('timestamp', data)
    
    @patch('serendipity_service.get_serendipity_service')
    def test_serendipity_api_post_unexpected_error(self, mock_get_service):
        """Test POST request when service raises unexpected error"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Mock service to raise unexpected error
        mock_service = Mock()
        mock_service.analyze_memory.side_effect = Exception("Unexpected error")
        mock_get_service.return_value = mock_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('timestamp', data)
    
    def test_serendipity_api_unsupported_method(self):
        """Test unsupported HTTP methods"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Test PUT method (not supported)
        response = self.client.put('/api/serendipity')
        self.assertEqual(response.status_code, 405)
        
        # Test DELETE method (not supported)
        response = self.client.delete('/api/serendipity')
        self.assertEqual(response.status_code, 405)
    
    def test_serendipity_api_post_with_unexpected_json(self):
        """Test POST request with unexpected JSON payload"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Send JSON payload (should be rejected)
        response = self.client.post('/api/serendipity', 
                                  json={'unexpected': 'data'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('Invalid request', data['error'])
        self.assertIn('does not accept JSON payload', data['message'])
    
    def test_serendipity_api_post_with_empty_json(self):
        """Test POST request with empty JSON payload (should be allowed)"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        with patch('serendipity_service.get_serendipity_service') as mock_get_service:
            # Mock service and analysis results
            mock_service = Mock()
            mock_analysis_results = {
                'connections': [],
                'meta_patterns': [],
                'serendipity_summary': 'Test summary',
                'recommendations': [],
                'metadata': {}
            }
            mock_service.analyze_memory.return_value = mock_analysis_results
            mock_get_service.return_value = mock_service
            
            # Send empty JSON payload (should be allowed)
            response = self.client.post('/api/serendipity', 
                                      json={},
                                      content_type='application/json')
            
            # Should succeed since empty JSON is acceptable
            self.assertEqual(response.status_code, 200)
    
    def test_serendipity_api_post_without_json(self):
        """Test POST request without JSON content type"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        with patch('serendipity_service.get_serendipity_service') as mock_get_service:
            # Mock service and analysis results
            mock_service = Mock()
            mock_analysis_results = {
                'connections': [],
                'meta_patterns': [],
                'serendipity_summary': 'Test summary',
                'recommendations': [],
                'metadata': {}
            }
            mock_service.analyze_memory.return_value = mock_analysis_results
            mock_get_service.return_value = mock_service
            
            # Send POST without JSON content type
            response = self.client.post('/api/serendipity')
            
            # Should succeed since JSON is not required
            self.assertEqual(response.status_code, 200)


class TestSerendipityAPIIntegration(unittest.TestCase):
    """Integration tests for serendipity API with real configuration"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Configure Flask app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
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
    
    def test_serendipity_api_with_insufficient_data(self):
        """Test API with insufficient memory data"""
        # Create temporary memory file with insufficient data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            test_memory_data = {
                "insights": [
                    {"content": "Only one insight", "category": "test"}
                ],
                "conversation_summaries": []
            }
            json.dump(test_memory_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Set configuration
            os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
            os.environ['MEMORY_FILE'] = temp_file_path
            os.environ['SERENDIPITY_MIN_INSIGHTS'] = '3'
            
            response = self.client.post('/api/serendipity')
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            
            self.assertIn('error', data)
            self.assertIn('message', data)
            
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)
    
    def test_serendipity_api_with_nonexistent_memory_file(self):
        """Test API with nonexistent memory file"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['MEMORY_FILE'] = 'nonexistent_memory_file.json'
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('message', data)
    
    def test_serendipity_api_configuration_integration(self):
        """Test API with custom configuration parameters"""
        # Create temporary memory file with sufficient data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            test_memory_data = {
                "insights": [
                    {"content": "Test insight 1", "category": "test"},
                    {"content": "Test insight 2", "category": "test"},
                    {"content": "Test insight 3", "category": "test"},
                    {"content": "Test insight 4", "category": "test"},
                    {"content": "Test insight 5", "category": "test"}
                ],
                "conversation_summaries": []
            }
            json.dump(test_memory_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Set custom configuration
            os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
            os.environ['MEMORY_FILE'] = temp_file_path
            os.environ['SERENDIPITY_MIN_INSIGHTS'] = '2'  # Lower threshold
            os.environ['SERENDIPITY_MAX_MEMORY_SIZE_MB'] = '100'
            os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '60'
            
            # Mock AI service to avoid actual AI calls
            with patch('serendipity_service.get_ai_service') as mock_get_ai_service:
                mock_ai_service = Mock()
                mock_ai_service.chat.return_value = json.dumps({
                    'connections': [],
                    'meta_patterns': [],
                    'serendipity_summary': 'Test summary',
                    'recommendations': []
                })
                mock_get_ai_service.return_value = mock_ai_service
                
                response = self.client.post('/api/serendipity')
                
                # Should succeed with mocked AI service
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                
                self.assertIn('connections', data)
                self.assertIn('metadata', data)
                
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)


class TestSerendipityAPISecurity(unittest.TestCase):
    """Security-focused tests for serendipity API endpoint"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Configure Flask app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
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
    
    def test_serendipity_api_malicious_json_payload(self):
        """Test endpoint with potentially malicious JSON payload"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        malicious_payloads = [
            {'__import__': 'os'},
            {'eval': 'print("test")'},
            {'script': '<script>alert("xss")</script>'},
            {'path': '/etc/passwd'},
            {'command': 'rm -rf /'},
            {'injection': "'; DROP TABLE users; --"}
        ]
        
        for payload in malicious_payloads:
            with self.subTest(payload=payload):
                response = self.client.post('/api/serendipity', 
                                          json=payload,
                                          content_type='application/json')
                
                # Should reject all malicious payloads
                self.assertEqual(response.status_code, 400)
                data = json.loads(response.data)
                self.assertIn('error', data)
    
    def test_serendipity_api_large_json_payload(self):
        """Test endpoint with oversized JSON payload"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create a large payload
        large_payload = {'data': 'x' * 10000}  # 10KB of data
        
        response = self.client.post('/api/serendipity', 
                                  json=large_payload,
                                  content_type='application/json')
        
        # Should reject large payloads
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_serendipity_api_invalid_content_type(self):
        """Test endpoint with invalid content types"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        with patch('serendipity_service.get_serendipity_service') as mock_get_service:
            # Mock service
            mock_service = Mock()
            mock_analysis_results = {'connections': [], 'metadata': {}}
            mock_service.analyze_memory.return_value = mock_analysis_results
            mock_get_service.return_value = mock_service
            
            # Test various content types
            invalid_content_types = [
                'text/plain',
                'application/xml',
                'multipart/form-data',
                'application/x-www-form-urlencoded'
            ]
            
            for content_type in invalid_content_types:
                with self.subTest(content_type=content_type):
                    response = self.client.post('/api/serendipity',
                                              data='test data',
                                              content_type=content_type)
                    
                    # Should still work since JSON is not required
                    self.assertEqual(response.status_code, 200)
    
    def test_serendipity_api_cors_headers(self):
        """Test that endpoint handles CORS appropriately"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Test OPTIONS request (Flask handles this automatically)
        response = self.client.options('/api/serendipity')
        
        # Flask automatically handles OPTIONS for defined methods
        self.assertIn(response.status_code, [200, 405])  # Either is acceptable
    
    def test_serendipity_api_rate_limiting_simulation(self):
        """Test rapid successive requests to simulate rate limiting scenarios"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        with patch('serendipity_service.get_serendipity_service') as mock_get_service:
            # Mock service
            mock_service = Mock()
            mock_analysis_results = {'connections': [], 'metadata': {}}
            mock_service.analyze_memory.return_value = mock_analysis_results
            mock_get_service.return_value = mock_service
            
            # Make rapid successive requests
            responses = []
            for i in range(5):
                response = self.client.post('/api/serendipity')
                responses.append(response.status_code)
            
            # All requests should succeed (no rate limiting implemented yet)
            for status_code in responses:
                self.assertEqual(status_code, 200)
    
    def test_serendipity_api_error_message_sanitization(self):
        """Test that error messages are properly sanitized"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        with patch('serendipity_service.get_serendipity_service') as mock_get_service:
            # Mock service to raise error with sensitive information
            mock_service = Mock()
            sensitive_error = Exception("Database connection failed at /home/user/secret/database.db with password=secret123")
            mock_service.analyze_memory.side_effect = sensitive_error
            mock_get_service.return_value = mock_service
            
            response = self.client.post('/api/serendipity')
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            
            # Error message should be sanitized
            self.assertIn('error', data)
            self.assertIn('message', data)
            
            # Should not contain sensitive information
            error_message = data['message'].lower()
            self.assertNotIn('password', error_message)
            self.assertNotIn('secret', error_message)
            self.assertNotIn('/home/user', error_message)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)