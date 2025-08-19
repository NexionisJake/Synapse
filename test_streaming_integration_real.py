"""
Real integration test for streaming functionality with actual AI service

This test verifies that streaming works with a real Ollama instance if available.
It's designed to be run manually when Ollama is running.
"""

import unittest
import json
import time
import requests
from datetime import datetime

class TestRealStreamingIntegration(unittest.TestCase):
    """Integration tests with real AI service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:5000"  # Assuming Flask app runs on port 5000
        self.test_conversation = [
            {"role": "user", "content": "Say hello in exactly 3 words"}
        ]
    
    def test_real_streaming_response(self):
        """Test streaming with real AI service (requires Ollama to be running)"""
        try:
            # First check if the service is available
            status_response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if status_response.status_code != 200:
                self.skipTest("AI service not available")
            
            status_data = status_response.json()
            if not status_data.get('connected', False):
                self.skipTest("AI service not connected")
            
            # Make streaming request
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    'conversation': self.test_conversation,
                    'stream': True
                },
                headers={'Content-Type': 'application/json'},
                stream=True,
                timeout=30
            )
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('content-type'), 'text/event-stream; charset=utf-8')
            
            # Process streaming response
            chunks_received = 0
            full_response = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    chunks_received += 1
                    chunk_json = line[6:]  # Remove 'data: ' prefix
                    chunk_data = json.loads(chunk_json)
                    
                    # Verify chunk structure
                    self.assertIn('content', chunk_data)
                    self.assertIn('timestamp', chunk_data)
                    self.assertIn('done', chunk_data)
                    self.assertIn('model', chunk_data)
                    
                    if chunk_data.get('content'):
                        full_response += chunk_data['content']
                    
                    # If this is the final chunk, verify completion
                    if chunk_data.get('done', False):
                        self.assertGreater(len(full_response.strip()), 0)
                        print(f"Received complete response: '{full_response.strip()}'")
                        break
            
            self.assertGreater(chunks_received, 0)
            print(f"Successfully received {chunks_received} chunks")
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Could not connect to Flask app: {e}")
    
    def test_streaming_performance_real(self):
        """Test streaming performance with real AI service"""
        try:
            # Check service availability
            status_response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if status_response.status_code != 200:
                self.skipTest("AI service not available")
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    'conversation': [
                        {"role": "user", "content": "Count from 1 to 5, one number per sentence"}
                    ],
                    'stream': True
                },
                headers={'Content-Type': 'application/json'},
                stream=True,
                timeout=30
            )
            
            first_chunk_time = None
            total_chunks = 0
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                    
                    total_chunks += 1
                    chunk_data = json.loads(line[6:])
                    
                    if chunk_data.get('done', False):
                        break
            
            total_time = time.time() - start_time
            first_byte_time = first_chunk_time - start_time if first_chunk_time else 0
            
            print(f"Performance metrics:")
            print(f"  First byte time: {first_byte_time:.3f}s")
            print(f"  Total response time: {total_time:.3f}s")
            print(f"  Total chunks: {total_chunks}")
            
            # Performance assertions
            self.assertLess(first_byte_time, 10.0, "First byte should arrive within 10 seconds")
            self.assertGreater(total_chunks, 0, "Should receive at least one chunk")
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Could not connect to Flask app: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("REAL STREAMING INTEGRATION TEST")
    print("=" * 60)
    print("This test requires:")
    print("1. Ollama to be running (ollama serve)")
    print("2. Flask app to be running (python app.py)")
    print("3. The llama3:8b model to be available")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2)