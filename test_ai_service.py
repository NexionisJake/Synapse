"""
Unit tests for the AI Service module

These tests verify the functionality of the AI communication service,
including error handling, system prompt management, and Ollama integration.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from ai_service import AIService, AIServiceError, get_ai_service, reset_ai_service

class TestAIService(unittest.TestCase):
    """Test cases for the AIService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_system_prompt = "Test system prompt for AI"
        self.test_model = "llama3:8b"
        
    def tearDown(self):
        """Clean up after tests"""
        reset_ai_service()
    
    @patch('ai_service.ollama.list')
    def test_ai_service_initialization_success(self, mock_list):
        """Test successful AI service initialization"""
        # Mock successful Ollama connection
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}, {'name': 'other-model'}]
        }
        
        service = AIService(model=self.test_model, system_prompt=self.test_system_prompt)
        
        self.assertEqual(service.model, self.test_model)
        self.assertEqual(service.system_prompt, self.test_system_prompt)
        mock_list.assert_called_once()
    
    @patch('ai_service.ollama.list')
    def test_ai_service_initialization_model_not_found(self, mock_list):
        """Test AI service initialization when model is not available"""
        # Mock Ollama connection with different models
        mock_list.return_value = {
            'models': [{'name': 'other-model'}, {'name': 'another-model'}]
        }
        
        with self.assertRaises(AIServiceError) as context:
            AIService(model=self.test_model)
        
        self.assertIn("not available", str(context.exception))
        self.assertGreaterEqual(mock_list.call_count, 1)
    
    @patch('ai_service.ollama.list')
    def test_ai_service_initialization_ollama_not_running(self, mock_list):
        """Test AI service initialization when Ollama is not running"""
        # Mock Ollama connection failure
        mock_list.side_effect = Exception("Connection refused")
        
        with self.assertRaises(AIServiceError) as context:
            AIService(model=self.test_model)
        
        self.assertIn("not available", str(context.exception))
        self.assertGreaterEqual(mock_list.call_count, 1)
    
    @patch('ai_service.ollama.list')
    @patch('ai_service.ollama.chat')
    def test_chat_success(self, mock_chat, mock_list):
        """Test successful chat interaction"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        # Mock successful chat response
        mock_chat.return_value = {
            'message': {'content': 'Hello! How can I help you today?'}
        }
        
        service = AIService(model=self.test_model, system_prompt=self.test_system_prompt)
        
        conversation = [
            {'role': 'user', 'content': 'Hello, how are you?'}
        ]
        
        response = service.chat(conversation)
        
        self.assertEqual(response, 'Hello! How can I help you today?')
        mock_chat.assert_called_once()
        
        # Verify the messages sent to Ollama include system prompt
        call_args = mock_chat.call_args
        messages = call_args[1]['messages']
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[0]['content'], self.test_system_prompt)
        self.assertEqual(messages[1]['role'], 'user')
        self.assertEqual(messages[1]['content'], 'Hello, how are you?')
    
    @patch('ai_service.ollama.list')
    @patch('ai_service.ollama.chat')
    def test_chat_with_invalid_message_format(self, mock_chat, mock_list):
        """Test chat with invalid message format"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        service = AIService(model=self.test_model)
        
        # Include invalid message format
        conversation = [
            {'role': 'user', 'content': 'Valid message'},
            {'invalid': 'format'},  # Invalid message format
            {'role': 'user', 'content': 'Another valid message'}
        ]
        
        # Should raise AIServiceError due to invalid message format
        with self.assertRaises(AIServiceError):
            service.chat(conversation)
    
    @patch('ai_service.ollama.list')
    @patch('ai_service.ollama.chat')
    def test_chat_ollama_error(self, mock_chat, mock_list):
        """Test chat when Ollama returns an error"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        # Mock Ollama error
        from ollama import ResponseError
        mock_chat.side_effect = ResponseError("Model not responding")
        
        service = AIService(model=self.test_model)
        
        conversation = [{'role': 'user', 'content': 'Hello'}]
        
        with self.assertRaises(AIServiceError) as context:
            service.chat(conversation)
        
        self.assertIn("AI", str(context.exception))
    
    @patch('ai_service.ollama.list')
    def test_update_system_prompt(self, mock_list):
        """Test updating the system prompt"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        service = AIService(model=self.test_model)
        original_prompt = service.get_system_prompt()
        
        new_prompt = "Updated system prompt for testing"
        service.update_system_prompt(new_prompt)
        
        self.assertEqual(service.get_system_prompt(), new_prompt)
        self.assertNotEqual(service.get_system_prompt(), original_prompt)
    
    @patch('ai_service.ollama.list')
    def test_update_system_prompt_empty(self, mock_list):
        """Test updating system prompt with empty string"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        service = AIService(model=self.test_model)
        
        with self.assertRaises(AIServiceError) as context:
            service.update_system_prompt("")
        
        self.assertIn("cannot be empty", str(context.exception))
    
    @patch('ai_service.ollama.list')
    def test_test_connection_success(self, mock_list):
        """Test connection test when successful"""
        # Mock successful connection
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}, {'name': 'other-model'}]
        }
        
        service = AIService(model=self.test_model)
        status = service.test_connection()
        
        self.assertTrue(status['connected'])
        self.assertEqual(status['model'], self.test_model)
        self.assertIn('llama3:8b', status['available_models'])
        self.assertIn('timestamp', status)
    
    @patch('ai_service.ollama.list')
    def test_test_connection_failure(self, mock_list):
        """Test connection test when Ollama is not available"""
        # Mock successful initialization first
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        service = AIService(model=self.test_model)
        
        # Now mock failure for test_connection
        mock_list.side_effect = Exception("Connection failed")
        
        status = service.test_connection()
        
        self.assertFalse(status['connected'])
        self.assertIn('error', status)
        self.assertIn('timestamp', status)

class TestAIServiceGlobalInstance(unittest.TestCase):
    """Test cases for global AI service instance management"""
    
    def tearDown(self):
        """Clean up after tests"""
        reset_ai_service()
    
    @patch('ai_service.ollama.list')
    def test_get_ai_service_singleton(self, mock_list):
        """Test that get_ai_service returns the same instance"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        service1 = get_ai_service()
        service2 = get_ai_service()
        
        self.assertIs(service1, service2)
    
    @patch('ai_service.ollama.list')
    def test_reset_ai_service(self, mock_list):
        """Test resetting the global AI service instance"""
        # Mock successful initialization
        mock_list.return_value = {
            'models': [{'name': 'llama3:8b'}]
        }
        
        service1 = get_ai_service()
        reset_ai_service()
        service2 = get_ai_service()
        
        self.assertIsNot(service1, service2)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)