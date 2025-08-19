"""
Unit tests for Memory Processing Flask Endpoints

This module contains tests for the Flask endpoints that handle memory
processing and insight generation functionality.
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app import app
from memory_service import reset_memory_service


class TestMemoryEndpoints(unittest.TestCase):
    """Test cases for memory processing Flask endpoints"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_memory_file = os.path.join(self.test_dir, 'test_memory.json')
        
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['OLLAMA_MODEL'] = 'test-model'
        self.client = app.test_client()
        
        # Sample conversation data for testing
        self.sample_conversation = [
            {"role": "user", "content": "I'm really interested in machine learning and AI"},
            {"role": "assistant", "content": "That's fascinating! What aspects of ML interest you most?"},
            {"role": "user", "content": "I love working with neural networks and deep learning"},
            {"role": "assistant", "content": "Deep learning is such an exciting field. Are you working on any projects?"}
        ]
        
        # Sample AI response for insight extraction
        self.sample_ai_response = {
            "insights": [
                {
                    "category": "interests",
                    "content": "User has strong interest in machine learning and AI",
                    "confidence": 0.9,
                    "tags": ["machine_learning", "AI", "technology"],
                    "evidence": "I'm really interested in machine learning and AI"
                }
            ],
            "conversation_summary": "Discussion about user's interest in machine learning and AI",
            "key_themes": ["machine_learning", "AI", "deep_learning"]
        }
        
        # Reset global memory service instance
        reset_memory_service()
    
    def tearDown(self):
        """Clean up after each test method"""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.test_dir)
        reset_memory_service()
    
    @patch('app.get_memory_service')
    def test_memory_process_endpoint_success(self, mock_get_service):
        """Test successful memory processing endpoint"""
        # Mock memory service
        mock_service = MagicMock()
        mock_service.process_conversation.return_value = {
            'success': True,
            'insights_extracted': 1,
            'conversation_summary': 'Test summary',
            'key_themes': ['test'],
            'memory_stats': {'total_insights': 1},
            'timestamp': '2024-01-01T00:00:00'
        }
        mock_get_service.return_value = mock_service
        
        # Make request
        response = self.client.post('/memory/process',
                                  json={'conversation': self.sample_conversation},
                                  content_type='application/json')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['insights_extracted'], 1)
        self.assertIn('conversation_summary', data)
        self.assertIn('memory_stats', data)
        
        # Verify service was called correctly
        # Note: Content gets HTML-escaped by security decorator
        call_args = mock_service.process_conversation.call_args[0][0]
        self.assertEqual(len(call_args), len(self.sample_conversation))
        # Check that the conversation structure is preserved
        for i, message in enumerate(call_args):
            self.assertEqual(message['role'], self.sample_conversation[i]['role'])
    
    def test_memory_process_endpoint_missing_conversation(self):
        """Test memory processing endpoint with missing conversation field"""
        response = self.client.post('/memory/process',
                                  json={'invalid': 'data'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn("conversation", data['message'])
    
    def test_memory_process_endpoint_invalid_conversation_format(self):
        """Test memory processing endpoint with invalid conversation format"""
        response = self.client.post('/memory/process',
                                  json={'conversation': 'not a list'},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('list', data['message'])
    
    def test_memory_process_endpoint_insufficient_conversation(self):
        """Test memory processing endpoint with insufficient conversation data"""
        response = self.client.post('/memory/process',
                                  json={'conversation': [{"role": "user", "content": "Hi"}]},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('2 messages required', data['message'])
    
    def test_memory_process_endpoint_not_json(self):
        """Test memory processing endpoint with non-JSON request"""
        response = self.client.post('/memory/process',
                                  data='not json',
                                  content_type='text/plain')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('JSON', data['message'])
    
    def test_memory_process_endpoint_empty_data(self):
        """Test memory processing endpoint with empty request data"""
        response = self.client.post('/memory/process',
                                  data='{}',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn("conversation", data['message'])
    
    @patch('app.get_memory_service')
    def test_memory_process_endpoint_service_error(self, mock_get_service):
        """Test memory processing endpoint with service error"""
        # Mock memory service to raise error
        mock_service = MagicMock()
        mock_service.process_conversation.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service
        
        response = self.client.post('/memory/process',
                                  json={'conversation': self.sample_conversation},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Memory processing error', data['message'])
    
    @patch('app.get_memory_service')
    def test_memory_stats_endpoint_success(self, mock_get_service):
        """Test successful memory stats endpoint"""
        # Mock memory service
        mock_service = MagicMock()
        mock_service.get_memory_stats.return_value = {
            'total_insights': 5,
            'total_conversations': 3,
            'categories': {'interests': 2, 'skills': 3},
            'confidence_distribution': {'high': 3, 'medium': 2, 'low': 0},
            'memory_file_exists': True,
            'memory_file_size': 1024
        }
        mock_get_service.return_value = mock_service
        
        # Make request
        response = self.client.get('/memory/stats')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_insights'], 5)
        self.assertEqual(data['total_conversations'], 3)
        self.assertIn('categories', data)
        self.assertIn('confidence_distribution', data)
        self.assertTrue(data['memory_file_exists'])
        
        # Verify service was called correctly
        mock_service.get_memory_stats.assert_called_once()
    
    @patch('app.get_memory_service')
    def test_memory_stats_endpoint_service_error(self, mock_get_service):
        """Test memory stats endpoint with service error"""
        # Mock memory service to raise error
        mock_service = MagicMock()
        mock_service.get_memory_stats.side_effect = Exception("Stats error")
        mock_get_service.return_value = mock_service
        
        response = self.client.get('/memory/stats')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Stats error', data['message'])


class TestMemoryEndpointsIntegration(unittest.TestCase):
    """Integration tests for memory endpoints with actual memory service"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)  # Change to temp dir so memory.json is created there
        
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['OLLAMA_MODEL'] = 'test-model'
        self.client = app.test_client()
        
        # Sample conversation data
        self.sample_conversation = [
            {"role": "user", "content": "I love programming in Python"},
            {"role": "assistant", "content": "Python is a great language! What do you like about it?"},
            {"role": "user", "content": "I enjoy its simplicity and the data science libraries"},
            {"role": "assistant", "content": "The data science ecosystem in Python is indeed impressive!"}
        ]
        
        # Reset global memory service instance
        reset_memory_service()
    
    def tearDown(self):
        """Clean up after tests"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
        reset_memory_service()
    
    @patch('memory_service.ollama.chat')
    def test_memory_process_integration(self, mock_chat):
        """Test complete memory processing integration"""
        # Mock AI response
        ai_response = {
            "insights": [
                {
                    "category": "programming_languages",
                    "content": "User enjoys programming in Python",
                    "confidence": 0.9,
                    "tags": ["Python", "programming"],
                    "evidence": "I love programming in Python"
                },
                {
                    "category": "interests",
                    "content": "User is interested in data science",
                    "confidence": 0.8,
                    "tags": ["data_science", "libraries"],
                    "evidence": "I enjoy its simplicity and the data science libraries"
                }
            ],
            "conversation_summary": "Discussion about Python programming and data science",
            "key_themes": ["Python", "programming", "data_science"]
        }
        
        mock_chat.return_value = {
            'message': {
                'content': json.dumps(ai_response)
            }
        }
        
        # Make request to process memory
        response = self.client.post('/memory/process',
                                  json={'conversation': self.sample_conversation},
                                  content_type='application/json')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['insights_extracted'], 2)
        self.assertIn('conversation_summary', data)
        self.assertIn('memory_stats', data)
        
        # Verify memory file was created
        self.assertTrue(os.path.exists('memory.json'))
        
        # Verify memory stats endpoint works
        stats_response = self.client.get('/memory/stats')
        self.assertEqual(stats_response.status_code, 200)
        stats_data = json.loads(stats_response.data)
        self.assertEqual(stats_data['total_insights'], 2)
        self.assertEqual(stats_data['total_conversations'], 1)
        self.assertTrue(stats_data['memory_file_exists'])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)