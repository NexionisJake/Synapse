"""
Test Flask integration with AI service
"""

import unittest
from unittest.mock import patch
from app import app

class TestFlaskIntegration(unittest.TestCase):
    """Test Flask application integration with AI service"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_route(self):
        """Test that the index route works"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.get_ai_service')
    def test_api_status_success(self, mock_get_ai_service):
        """Test API status endpoint with successful AI service"""
        # Mock successful AI service
        mock_service = mock_get_ai_service.return_value
        mock_service.test_connection.return_value = {
            "connected": True,
            "model": "llama3:8b",
            "available_models": ["llama3:8b"],
            "timestamp": "2024-01-01T00:00:00"
        }
        
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['connected'])
        self.assertEqual(data['model'], 'llama3:8b')
    
    @patch('app.get_ai_service')
    def test_api_status_failure(self, mock_get_ai_service):
        """Test API status endpoint with AI service failure"""
        from ai_service import AIServiceError
        
        # Mock AI service error
        mock_get_ai_service.side_effect = AIServiceError("Ollama not available")
        
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 503)
        
        data = response.get_json()
        self.assertTrue(data['error'])
        self.assertIn('message', data)

if __name__ == '__main__':
    unittest.main(verbosity=2)