"""
Unit tests for the chat API endpoint

This module tests the POST /chat route functionality including:
- Request validation and error handling
- AI service integration
- Response formatting
- Error scenarios
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from ai_service import AIServiceError

class TestChatEndpoint(unittest.TestCase):
    """Test cases for the chat API endpoint"""
    
    def setUp(self):
        """Set up test client and test data"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Sample valid conversation history
        self.valid_conversation = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What's the weather like?"}
        ]
        
        # Sample AI response
        self.sample_ai_response = "I don't have access to real-time weather data, but I'd be happy to discuss weather patterns or help you find weather information!"
    
    def test_chat_endpoint_success(self):
        """Test successful chat request with valid conversation history"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = self.sample_ai_response
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make request
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': self.valid_conversation}),
                                      content_type='application/json')
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('message', data)
            self.assertIn('timestamp', data)
            self.assertIn('model', data)
            self.assertEqual(data['message'], self.sample_ai_response)
            self.assertEqual(data['model'], 'llama3:8b')
            
            # Verify AI service was called correctly
            # Note: Content gets HTML-escaped by security decorator
            call_args = mock_ai_service.chat.call_args[0][0]
            self.assertEqual(len(call_args), len(self.valid_conversation))
            self.assertEqual(call_args[0]['role'], 'user')
            self.assertEqual(call_args[0]['content'], 'Hello, how are you?')  # This one doesn't have apostrophes
    
    def test_chat_endpoint_non_json_request(self):
        """Test chat endpoint with non-JSON request"""
        response = self.client.post('/chat',
                                  data='not json',
                                  content_type='text/plain')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid request format')
    
    def test_chat_endpoint_null_data(self):
        """Test chat endpoint with null request data"""
        response = self.client.post('/chat',
                                  data='null',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid request data')
    
    def test_chat_endpoint_empty_dict(self):
        """Test chat endpoint with empty dictionary"""
        response = self.client.post('/chat',
                                  data=json.dumps({}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid request data')
    
    def test_chat_endpoint_missing_conversation(self):
        """Test chat endpoint with missing conversation field"""
        response = self.client.post('/chat',
                                  data=json.dumps({'other_field': 'value'}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid request data')
    
    def test_chat_endpoint_invalid_conversation_type(self):
        """Test chat endpoint with conversation field that's not a list"""
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': 'not a list'}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
    
    def test_chat_endpoint_empty_conversation(self):
        """Test chat endpoint with empty conversation history"""
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': []}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
    
    def test_chat_endpoint_invalid_message_format(self):
        """Test chat endpoint with invalid message format"""
        invalid_conversation = [
            {"role": "user", "content": "Hello"},
            "not a dictionary"  # Invalid message format
        ]
        
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': invalid_conversation}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
        self.assertIn('index 1', data['message'])
    
    def test_chat_endpoint_missing_message_fields(self):
        """Test chat endpoint with messages missing required fields"""
        invalid_conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant"}  # Missing content field
        ]
        
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': invalid_conversation}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
        self.assertIn('role', data['message'])
        self.assertIn('content', data['message'])
    
    def test_chat_endpoint_invalid_message_role(self):
        """Test chat endpoint with invalid message role"""
        invalid_conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "invalid_role", "content": "Response"}  # Invalid role
        ]
        
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': invalid_conversation}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
    
    def test_chat_endpoint_empty_message_content(self):
        """Test chat endpoint with empty message content"""
        invalid_conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": ""}  # Empty content
        ]
        
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': invalid_conversation}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
    
    def test_chat_endpoint_whitespace_only_content(self):
        """Test chat endpoint with whitespace-only message content"""
        invalid_conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "   "}  # Whitespace only
        ]
        
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': invalid_conversation}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid conversation data')
    
    def test_chat_endpoint_ai_service_error(self):
        """Test chat endpoint when AI service raises an error"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service to raise an error
            mock_ai_service = MagicMock()
            mock_ai_service.chat.side_effect = AIServiceError("AI model not available")
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make request
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': self.valid_conversation}),
                                      content_type='application/json')
            
            # Verify error response
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('error', data)
            self.assertIn('message', data)
    
    def test_chat_endpoint_unexpected_error(self):
        """Test chat endpoint when an unexpected error occurs"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service to raise an unexpected error
            mock_ai_service = MagicMock()
            mock_ai_service.chat.side_effect = Exception("Unexpected error")
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make request
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': self.valid_conversation}),
                                      content_type='application/json')
            
            # Verify error response
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('error', data)
    
    def test_chat_endpoint_single_message(self):
        """Test chat endpoint with single message conversation"""
        single_message_conversation = [
            {"role": "user", "content": "Hello!"}
        ]
        
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = "Hello! How can I help you today?"
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make request
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': single_message_conversation}),
                                      content_type='application/json')
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('message', data)
            self.assertEqual(data['message'], "Hello! How can I help you today?")
    
    def test_chat_endpoint_long_conversation(self):
        """Test chat endpoint with long conversation history"""
        long_conversation = []
        for i in range(20):
            long_conversation.append({"role": "user", "content": f"Message {i}"})
            long_conversation.append({"role": "assistant", "content": f"Response {i}"})
        
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = "I understand the conversation history."
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make request
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': long_conversation}),
                                      content_type='application/json')
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('message', data)
            
            # Verify AI service was called with the full conversation
            mock_ai_service.chat.assert_called_once_with(long_conversation)
    
    def test_chat_endpoint_response_format(self):
        """Test that chat endpoint returns properly formatted response"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = self.sample_ai_response
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make request
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': self.valid_conversation}),
                                      content_type='application/json')
            
            # Verify response format
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            
            data = json.loads(response.data)
            
            # Check required fields
            required_fields = ['message', 'timestamp', 'model']
            for field in required_fields:
                self.assertIn(field, data)
            
            # Check field types and values
            self.assertIsInstance(data['message'], str)
            self.assertIsInstance(data['timestamp'], str)
            self.assertIsInstance(data['model'], str)
            
            # Verify timestamp is valid ISO format
            try:
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                self.fail("Timestamp is not in valid ISO format")
            
            # Verify model matches configuration
            self.assertEqual(data['model'], 'llama3:8b')

if __name__ == '__main__':
    unittest.main()