#!/usr/bin/env python3
"""
Manual test script for streaming functionality

This script demonstrates the streaming endpoint in action and can be used
for manual testing and debugging.
"""

import json
import time
import sys
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.append('.')

from app import app, generate_streaming_response
from ai_service import AIService

def test_streaming_generator():
    """Test the streaming response generator directly"""
    print("Testing streaming response generator...")
    print("-" * 50)
    
    # Mock AI service with sample streaming data
    mock_ai_service = Mock()
    sample_chunks = [
        {"content": "Streaming", "full_content": "Streaming", "chunk_id": 1, "done": False},
        {"content": " responses", "full_content": "Streaming responses", "chunk_id": 2, "done": False},
        {"content": " work", "full_content": "Streaming responses work", "chunk_id": 3, "done": False},
        {"content": " perfectly!", "full_content": "Streaming responses work perfectly!", "chunk_id": 4, "done": True}
    ]
    mock_ai_service.chat.return_value = iter(sample_chunks)
    
    # Test conversation
    conversation = [
        {"role": "user", "content": "Test streaming"}
    ]
    
    # Generate streaming response
    print("Generating streaming response chunks:")
    chunk_count = 0
    
    for chunk in generate_streaming_response(mock_ai_service, conversation):
        chunk_count += 1
        print(f"Chunk {chunk_count}:")
        print(f"  Raw: {chunk[:100]}...")  # Show first 100 chars
        
        # Parse the JSON data
        if chunk.startswith('data: '):
            json_data = chunk[6:-2]  # Remove 'data: ' and '\n\n'
            try:
                parsed = json.loads(json_data)
                print(f"  Content: '{parsed.get('content', '')}'")
                print(f"  Full: '{parsed.get('full_content', '')}'")
                print(f"  Done: {parsed.get('done', False)}")
                if 'streaming_stats' in parsed:
                    stats = parsed['streaming_stats']
                    print(f"  Stats: {stats['total_chunks']} chunks, {stats['total_characters']} chars")
                print()
            except json.JSONDecodeError as e:
                print(f"  JSON Error: {e}")
        
        if chunk_count >= 10:  # Safety limit
            break
    
    print(f"Generated {chunk_count} chunks successfully!")
    print()

def test_flask_app_streaming():
    """Test streaming through Flask app"""
    print("Testing Flask app streaming endpoint...")
    print("-" * 50)
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Mock the AI service
    with patch('app.get_ai_service') as mock_get_ai_service:
        mock_ai_service = Mock()
        sample_chunks = [
            {"content": "Flask", "full_content": "Flask", "chunk_id": 1, "done": False},
            {"content": " streaming", "full_content": "Flask streaming", "chunk_id": 2, "done": False},
            {"content": " works!", "full_content": "Flask streaming works!", "chunk_id": 3, "done": True}
        ]
        mock_ai_service.chat.return_value = iter(sample_chunks)
        mock_get_ai_service.return_value = mock_ai_service
        
        # Make streaming request
        response = client.post('/chat',
            json={
                'conversation': [
                    {"role": "user", "content": "Test Flask streaming"}
                ],
                'stream': True
            },
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers:")
        for key, value in response.headers:
            print(f"  {key}: {value}")
        print()
        
        # Process response data
        response_data = response.get_data(as_text=True)
        lines = response_data.strip().split('\n')
        data_lines = [line for line in lines if line.startswith('data: ')]
        
        print(f"Received {len(data_lines)} data chunks:")
        for i, line in enumerate(data_lines, 1):
            json_data = line[6:]  # Remove 'data: '
            try:
                parsed = json.loads(json_data)
                print(f"  Chunk {i}: '{parsed.get('content', '')}' (done: {parsed.get('done', False)})")
            except json.JSONDecodeError as e:
                print(f"  Chunk {i}: JSON Error - {e}")
        
        print()

def test_cors_headers():
    """Test CORS headers for browser compatibility"""
    print("Testing CORS headers...")
    print("-" * 50)
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Test OPTIONS request
    response = client.options('/chat')
    print(f"OPTIONS response status: {response.status_code}")
    print("CORS headers:")
    cors_headers = [
        'Access-Control-Allow-Origin',
        'Access-Control-Allow-Methods',
        'Access-Control-Allow-Headers'
    ]
    
    for header in cors_headers:
        value = response.headers.get(header, 'Not set')
        print(f"  {header}: {value}")
    
    print()

def test_error_handling():
    """Test streaming error handling"""
    print("Testing streaming error handling...")
    print("-" * 50)
    
    # Mock AI service that raises an error
    mock_ai_service = Mock()
    mock_ai_service.chat.side_effect = Exception("Simulated AI service error")
    
    conversation = [{"role": "user", "content": "This will cause an error"}]
    
    print("Generating error response:")
    chunk_count = 0
    
    for chunk in generate_streaming_response(mock_ai_service, conversation):
        chunk_count += 1
        print(f"Error chunk {chunk_count}:")
        
        if chunk.startswith('data: '):
            json_data = chunk[6:-2]
            try:
                parsed = json.loads(json_data)
                print(f"  Error: {parsed.get('error', 'No error field')}")
                print(f"  Done: {parsed.get('done', False)}")
                break
            except json.JSONDecodeError as e:
                print(f"  JSON Error: {e}")
    
    print("Error handling test completed!")
    print()

def main():
    """Run all manual tests"""
    print("=" * 60)
    print("STREAMING FUNCTIONALITY MANUAL TEST")
    print("=" * 60)
    print()
    
    try:
        test_streaming_generator()
        test_flask_app_streaming()
        test_cors_headers()
        test_error_handling()
        
        print("=" * 60)
        print("ALL MANUAL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Manual test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())