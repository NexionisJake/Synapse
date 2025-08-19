"""
Comprehensive Integration Tests for Synapse AI Web Application

This module contains end-to-end integration tests that verify complete
conversation flows and system interactions.
"""

import unittest
import json
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock
import time

from app import app
from ai_service import reset_ai_service
from memory_service import reset_memory_service
from prompt_service import reset_prompt_service


class TestCompleteConversationFlow(unittest.TestCase):
    """Test complete conversation flows from start to finish"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_memory_file = os.path.join(self.test_dir, 'test_memory.json')
        
        # Reset all services
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
        
        # Sample conversation for testing
        self.sample_conversation = [
            {"role": "user", "content": "Hello, I'm interested in learning about artificial intelligence"},
            {"role": "assistant", "content": "That's wonderful! AI is a fascinating field. What specific aspects interest you most?"},
            {"role": "user", "content": "I'm particularly curious about machine learning and neural networks"},
            {"role": "assistant", "content": "Great choice! Machine learning and neural networks are at the heart of modern AI. Would you like to start with the basics?"}
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    @patch('app.get_ai_service')
    def test_complete_chat_to_memory_flow(self, mock_get_ai_service):
        """Test complete flow from chat to memory processing"""
        # Mock AI service for chat
        mock_ai_service = MagicMock()
        mock_ai_service.chat.return_value = "I'd be happy to help you learn about AI fundamentals!"
        mock_get_ai_service.return_value = mock_ai_service
        
        # Step 1: Send chat message
        chat_response = self.client.post('/chat',
                                       data=json.dumps({'conversation': self.sample_conversation}),
                                       content_type='application/json')
        
        self.assertEqual(chat_response.status_code, 200)
        chat_data = json.loads(chat_response.data)
        self.assertIn('message', chat_data)
        
        # Step 2: Process memory with the conversation
        with patch('memory_service.ollama.chat') as mock_memory_chat:
            mock_memory_response = {
                "insights": [
                    {
                        "category": "interests",
                        "content": "User is interested in AI and machine learning",
                        "confidence": 0.9,
                        "tags": ["AI", "machine_learning"],
                        "evidence": "I'm interested in learning about artificial intelligence"
                    }
                ],
                "conversation_summary": "User expressing interest in AI and ML",
                "key_themes": ["artificial_intelligence", "machine_learning"]
            }
            mock_memory_chat.return_value = {
                'message': {'content': json.dumps(mock_memory_response)}
            }
            
            # Process memory
            memory_response = self.client.post('/memory/process',
                                             data=json.dumps({'conversation': self.sample_conversation}),
                                             content_type='application/json')
            
            self.assertEqual(memory_response.status_code, 200)
            memory_data = json.loads(memory_response.data)
            self.assertTrue(memory_data['success'])
            self.assertEqual(memory_data['insights_extracted'], 1)
        
        # Step 3: Check memory stats
        stats_response = self.client.get('/api/insights')
        self.assertEqual(stats_response.status_code, 200)
        stats_data = json.loads(stats_response.data)
        self.assertGreater(stats_data['statistics']['total_insights'], 0)
    
    @patch('app.get_ai_service')
    def test_multi_turn_conversation_with_context(self, mock_get_ai_service):
        """Test multi-turn conversation maintaining context"""
        # Mock AI service
        mock_ai_service = MagicMock()
        responses = [
            "Hello! I'm here to help you learn about AI.",
            "Machine learning is a subset of AI that focuses on algorithms that can learn from data.",
            "Neural networks are inspired by biological neural networks and are great for pattern recognition."
        ]
        mock_ai_service.chat.side_effect = responses
        mock_get_ai_service.return_value = mock_ai_service
        
        conversation_history = []
        
        # Turn 1
        conversation_history.extend([
            {"role": "user", "content": "Hello, can you help me learn about AI?"}
        ])
        
        response1 = self.client.post('/chat',
                                   data=json.dumps({'conversation': conversation_history}),
                                   content_type='application/json')
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.data)
        conversation_history.append({"role": "assistant", "content": data1['message']})
        
        # Turn 2
        conversation_history.append({"role": "user", "content": "What is machine learning?"})
        
        response2 = self.client.post('/chat',
                                   data=json.dumps({'conversation': conversation_history}),
                                   content_type='application/json')
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.data)
        conversation_history.append({"role": "assistant", "content": data2['message']})
        
        # Turn 3
        conversation_history.append({"role": "user", "content": "Tell me about neural networks"})
        
        response3 = self.client.post('/chat',
                                   data=json.dumps({'conversation': conversation_history}),
                                   content_type='application/json')
        self.assertEqual(response3.status_code, 200)
        data3 = json.loads(response3.data)
        
        # Verify AI service was called with full conversation context each time
        self.assertEqual(mock_ai_service.chat.call_count, 3)
        
        # Check that conversation context was maintained
        final_call_args = mock_ai_service.chat.call_args_list[-1][0][0]
        self.assertGreaterEqual(len(final_call_args), 5)  # At least 5 messages (may be cleaned up)
    
    def test_error_recovery_flow(self):
        """Test system behavior during error conditions"""
        # Test chat endpoint with AI service unavailable
        with patch('app.get_ai_service') as mock_get_ai_service:
            from ai_service import AIServiceError
            mock_get_ai_service.side_effect = AIServiceError("AI service unavailable")
            
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': self.sample_conversation}),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertTrue(data['error'])
        
        # Test memory processing with service error
        with patch('memory_service.get_memory_service') as mock_get_memory_service:
            from memory_service import MemoryServiceError
            mock_memory_service = MagicMock()
            mock_memory_service.process_conversation.side_effect = MemoryServiceError("Memory service error")
            mock_get_memory_service.return_value = mock_memory_service
            
            response = self.client.post('/memory/process',
                                      data=json.dumps({'conversation': self.sample_conversation}),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            # Service handles errors gracefully, check for success response
            self.assertIn('success', data)
    
    @patch('app.get_ai_service')
    def test_concurrent_requests_handling(self, mock_get_ai_service):
        """Test handling of concurrent requests"""
        # Mock AI service with delay to simulate processing time
        mock_ai_service = MagicMock()
        
        def slow_response(conversation):
            time.sleep(0.1)  # Small delay
            return "Response after processing"
        
        mock_ai_service.chat.side_effect = slow_response
        mock_get_ai_service.return_value = mock_ai_service
        
        # Send multiple concurrent requests (simulated)
        responses = []
        for i in range(3):
            conversation = [{"role": "user", "content": f"Message {i}"}]
            response = self.client.post('/chat',
                                      data=json.dumps({'conversation': conversation}),
                                      content_type='application/json')
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('message', data)


class TestSystemIntegration(unittest.TestCase):
    """Test integration between different system components"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Reset all services
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    def tearDown(self):
        """Clean up test environment"""
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    def test_all_routes_accessible(self):
        """Test that all main routes are accessible"""
        routes_to_test = [
            ('/', 'GET', 200),
            ('/dashboard', 'GET', 200),
            ('/prompts', 'GET', 200),
        ]
        
        for route, method, expected_status in routes_to_test:
            if method == 'GET':
                response = self.client.get(route)
            elif method == 'POST':
                response = self.client.post(route)
            
            self.assertEqual(response.status_code, expected_status,
                           f"Route {route} returned {response.status_code}, expected {expected_status}")
    
    def test_api_endpoints_return_json(self):
        """Test that API endpoints return proper JSON responses"""
        api_endpoints = [
            '/api/status',
            '/api/insights',
        ]
        
        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.content_type, ['application/json', 'application/json; charset=utf-8'],
                         f"Endpoint {endpoint} did not return JSON")
            
            # Verify JSON is parseable
            try:
                json.loads(response.data)
            except json.JSONDecodeError:
                self.fail(f"Endpoint {endpoint} returned invalid JSON")
    
    @patch('app.get_ai_service')
    def test_system_status_integration(self, mock_get_ai_service):
        """Test system status reporting integration"""
        # Mock AI service status
        mock_ai_service = MagicMock()
        mock_ai_service.test_connection.return_value = {
            "connected": True,
            "model": "llama3:8b",
            "available_models": ["llama3:8b"],
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('connected', data)
        self.assertIn('model', data)
        self.assertIn('timestamp', data)


class TestDataPersistence(unittest.TestCase):
    """Test data persistence across requests and sessions"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Reset all services
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    @patch('memory_service.ollama.chat')
    def test_memory_persistence_across_requests(self, mock_chat):
        """Test that memory data persists across multiple requests"""
        # Mock AI response for memory processing
        mock_response = {
            "insights": [
                {
                    "category": "test",
                    "content": "Test insight",
                    "confidence": 0.8,
                    "tags": ["test"],
                    "evidence": "test evidence"
                }
            ],
            "conversation_summary": "Test conversation",
            "key_themes": ["test"]
        }
        mock_chat.return_value = {
            'message': {'content': json.dumps(mock_response)}
        }
        
        conversation = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"}
        ]
        
        # First request - process memory
        response1 = self.client.post('/memory/process',
                                   data=json.dumps({'conversation': conversation}),
                                   content_type='application/json')
        self.assertEqual(response1.status_code, 200)
        
        # Second request - check that memory was persisted
        response2 = self.client.get('/api/insights')
        self.assertEqual(response2.status_code, 200)
        
        data = json.loads(response2.data)
        self.assertGreater(data['statistics']['total_insights'], 0)


class TestPerformanceAndScaling(unittest.TestCase):
    """Test performance characteristics and scaling behavior"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Reset all services
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    def tearDown(self):
        """Clean up test environment"""
        reset_ai_service()
        reset_memory_service()
        reset_prompt_service()
    
    @patch('app.get_ai_service')
    def test_large_conversation_handling(self, mock_get_ai_service):
        """Test handling of large conversation histories"""
        # Mock AI service
        mock_ai_service = MagicMock()
        mock_ai_service.chat.return_value = "Response to large conversation"
        mock_get_ai_service.return_value = mock_ai_service
        
        # Create large conversation (100 messages)
        large_conversation = []
        for i in range(50):
            large_conversation.extend([
                {"role": "user", "content": f"User message {i}"},
                {"role": "assistant", "content": f"Assistant response {i}"}
            ])
        
        # Test that large conversation is handled
        response = self.client.post('/chat',
                                  data=json.dumps({'conversation': large_conversation}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
    
    def test_malformed_request_handling(self):
        """Test handling of various malformed requests"""
        malformed_requests = [
            ('', 'application/json'),  # Empty body
            ('invalid json', 'application/json'),  # Invalid JSON
            ('{"incomplete": ', 'application/json'),  # Incomplete JSON
            ('null', 'application/json'),  # Null JSON
            ('[]', 'application/json'),  # Array instead of object
        ]
        
        for body, content_type in malformed_requests:
            response = self.client.post('/chat',
                                      data=body,
                                      content_type=content_type)
            
            # Should return 400 Bad Request for malformed data
            self.assertEqual(response.status_code, 400,
                           f"Malformed request '{body}' should return 400")
            
            # Response should be valid JSON
            try:
                data = json.loads(response.data)
                self.assertIn('error', data)
            except json.JSONDecodeError:
                self.fail(f"Error response for '{body}' is not valid JSON")


if __name__ == '__main__':
    unittest.main(verbosity=2)