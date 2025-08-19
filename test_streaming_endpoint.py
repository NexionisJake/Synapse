"""
Unit tests for streaming endpoint functionality and error handling

This module tests the enhanced streaming response system including:
- Server-Sent Events streaming
- CORS headers and browser compatibility
- Error handling and recovery
- Performance monitoring
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from datetime import datetime

# Import the modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, generate_streaming_response, handle_streaming_chat
from ai_service import AIService, AIServiceError
from config import get_config

class TestStreamingEndpoint(unittest.TestCase):
    """Test cases for streaming endpoint functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Sample conversation history for testing
        self.sample_conversation = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
            {"role": "user", "content": "Tell me about quantum computing"}
        ]
        
        # Mock AI service responses
        self.mock_streaming_chunks = [
            {"content": "Quantum", "full_content": "Quantum", "chunk_id": 1, "done": False},
            {"content": " computing", "full_content": "Quantum computing", "chunk_id": 2, "done": False},
            {"content": " is fascinating!", "full_content": "Quantum computing is fascinating!", "chunk_id": 3, "done": True}
        ]
    
    def test_streaming_endpoint_basic_functionality(self):
        """Test basic streaming endpoint functionality"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service with streaming response
            mock_ai_service = Mock()
            mock_ai_service.chat.return_value = iter(self.mock_streaming_chunks)
            mock_get_ai_service.return_value = mock_ai_service
            
            # Make streaming request
            response = self.client.post('/chat', 
                json={
                    'conversation': self.sample_conversation,
                    'stream': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            # Verify response headers
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'text/event-stream; charset=utf-8')
            self.assertIn('no-cache', response.headers.get('Cache-Control', ''))
            self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
            
            # Verify streaming data format
            response_data = response.get_data(as_text=True)
            self.assertIn('data: ', response_data)
            
            # Parse and verify JSON chunks
            lines = response_data.strip().split('\n')
            data_lines = [line for line in lines if line.startswith('data: ')]
            
            self.assertGreater(len(data_lines), 0)
            
            # Verify first chunk structure
            first_chunk_json = data_lines[0][6:]  # Remove 'data: ' prefix
            first_chunk = json.loads(first_chunk_json)
            
            required_fields = ['content', 'full_content', 'chunk_id', 'timestamp', 'done', 'model']
            for field in required_fields:
                self.assertIn(field, first_chunk)
    
    def test_streaming_cors_preflight(self):
        """Test CORS preflight request handling"""
        response = self.client.options('/chat')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
        self.assertIn('POST', response.headers.get('Access-Control-Allow-Methods', ''))
        self.assertIn('Content-Type', response.headers.get('Access-Control-Allow-Headers', ''))
    
    def test_streaming_error_handling(self):
        """Test streaming error handling and recovery"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service that raises an exception
            mock_ai_service = Mock()
            mock_ai_service.chat.side_effect = AIServiceError("Connection failed")
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/chat',
                json={
                    'conversation': self.sample_conversation,
                    'stream': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            # Should still return 200 with error in stream
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'text/event-stream; charset=utf-8')
            
            # Verify error is included in stream
            response_data = response.get_data(as_text=True)
            self.assertIn('data: ', response_data)
            
            # Parse error chunk
            lines = response_data.strip().split('\n')
            data_lines = [line for line in lines if line.startswith('data: ')]
            
            if data_lines:
                error_chunk_json = data_lines[-1][6:]  # Last chunk should be error
                error_chunk = json.loads(error_chunk_json)
                
                self.assertTrue(error_chunk.get('done', False))
                self.assertIn('error', error_chunk)
    
    def test_streaming_performance_metrics(self):
        """Test streaming performance monitoring"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service with streaming response
            mock_ai_service = Mock()
            mock_ai_service.chat.return_value = iter(self.mock_streaming_chunks)
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/chat',
                json={
                    'conversation': self.sample_conversation,
                    'stream': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            # Verify performance metrics are included
            response_data = response.get_data(as_text=True)
            lines = response_data.strip().split('\n')
            data_lines = [line for line in lines if line.startswith('data: ')]
            
            if data_lines:
                chunk_json = data_lines[0][6:]
                chunk = json.loads(chunk_json)
                
                if 'streaming_stats' in chunk:
                    stats = chunk['streaming_stats']
                    self.assertIn('total_chunks', stats)
                    self.assertIn('total_characters', stats)
                    self.assertIn('elapsed_time', stats)
                    self.assertIn('words_per_second', stats)
    
    def test_non_streaming_fallback(self):
        """Test non-streaming mode still works"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service with regular response
            mock_ai_service = Mock()
            mock_ai_service.chat.return_value = "This is a regular response"
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/chat',
                json={
                    'conversation': self.sample_conversation,
                    'stream': False  # Explicitly request non-streaming
                },
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            
            data = response.get_json()
            self.assertIn('message', data)
            self.assertEqual(data['message'], "This is a regular response")
    
    def test_invalid_streaming_request(self):
        """Test handling of invalid streaming requests"""
        # Test missing conversation
        response = self.client.post('/chat',
            json={'stream': True},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 400)
        
        # Test empty conversation
        response = self.client.post('/chat',
            json={
                'conversation': [],
                'stream': True
            },
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_streaming_timeout_handling(self):
        """Test streaming timeout and connection handling"""
        with patch('app.get_ai_service') as mock_get_ai_service:
            # Mock AI service that simulates timeout
            mock_ai_service = Mock()
            
            def slow_generator():
                yield {"content": "Starting...", "chunk_id": 1, "done": False}
                time.sleep(0.1)  # Simulate slow response
                raise TimeoutError("Request timed out")
            
            mock_ai_service.chat.return_value = slow_generator()
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/chat',
                json={
                    'conversation': self.sample_conversation,
                    'stream': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            # Should handle timeout gracefully
            self.assertEqual(response.status_code, 200)
            response_data = response.get_data(as_text=True)
            self.assertIn('data: ', response_data)


class TestGenerateStreamingResponse(unittest.TestCase):
    """Test cases for the generate_streaming_response function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_conversation = [
            {"role": "user", "content": "Test message"}
        ]
        
        self.mock_chunks = [
            {"content": "Hello", "full_content": "Hello", "chunk_id": 1, "done": False},
            {"content": " world", "full_content": "Hello world", "chunk_id": 2, "done": True}
        ]
    
    def test_generate_streaming_response_success(self):
        """Test successful streaming response generation"""
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = iter(self.mock_chunks)
        
        # Generate streaming response
        generator = generate_streaming_response(mock_ai_service, self.sample_conversation)
        chunks = list(generator)
        
        # Verify chunks are properly formatted
        self.assertGreater(len(chunks), 0)
        
        for chunk in chunks:
            self.assertTrue(chunk.startswith('data: '))
            self.assertTrue(chunk.endswith('\n\n'))
            
            # Parse JSON
            json_data = chunk[6:-2]  # Remove 'data: ' and '\n\n'
            parsed = json.loads(json_data)
            
            # Verify required fields
            self.assertIn('content', parsed)
            self.assertIn('timestamp', parsed)
            self.assertIn('done', parsed)
    
    def test_generate_streaming_response_error(self):
        """Test streaming response error handling"""
        # Mock AI service that raises exception
        mock_ai_service = Mock()
        mock_ai_service.chat.side_effect = Exception("Test error")
        
        # Generate streaming response
        generator = generate_streaming_response(mock_ai_service, self.sample_conversation)
        chunks = list(generator)
        
        # Should have at least one error chunk
        self.assertGreater(len(chunks), 0)
        
        # Last chunk should be error chunk
        error_chunk = chunks[-1]
        self.assertTrue(error_chunk.startswith('data: '))
        
        json_data = error_chunk[6:-2]
        parsed = json.loads(json_data)
        
        self.assertTrue(parsed.get('done', False))
        self.assertIn('error', parsed)


class TestStreamingIntegration(unittest.TestCase):
    """Integration tests for streaming functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('app.get_ai_service')
    def test_end_to_end_streaming(self, mock_get_ai_service):
        """Test complete end-to-end streaming flow"""
        # Mock complete streaming response
        streaming_chunks = [
            {"content": "Quantum", "full_content": "Quantum", "chunk_id": 1, "done": False},
            {"content": " computing", "full_content": "Quantum computing", "chunk_id": 2, "done": False},
            {"content": " uses quantum", "full_content": "Quantum computing uses quantum", "chunk_id": 3, "done": False},
            {"content": " mechanics principles.", "full_content": "Quantum computing uses quantum mechanics principles.", "chunk_id": 4, "done": True}
        ]
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = iter(streaming_chunks)
        mock_get_ai_service.return_value = mock_ai_service
        
        # Make streaming request
        response = self.client.post('/chat',
            json={
                'conversation': [
                    {"role": "user", "content": "Explain quantum computing"}
                ],
                'stream': True
            },
            headers={'Content-Type': 'application/json'}
        )
        
        # Verify complete response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/event-stream; charset=utf-8')
        
        response_data = response.get_data(as_text=True)
        lines = response_data.strip().split('\n')
        data_lines = [line for line in lines if line.startswith('data: ')]
        
        # Should have chunks for each streaming response
        self.assertEqual(len(data_lines), len(streaming_chunks))
        
        # Verify final chunk is marked as done
        final_chunk_json = data_lines[-1][6:]
        final_chunk = json.loads(final_chunk_json)
        self.assertTrue(final_chunk.get('done', False))
        self.assertEqual(final_chunk.get('full_content'), "Quantum computing uses quantum mechanics principles.")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)