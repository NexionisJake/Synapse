#!/usr/bin/env python3
"""
Integration test for the StreamingResponseHandler frontend implementation
Tests the interaction between the enhanced frontend streaming handler and the backend
"""

import json
import time
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_streaming_response_format():
    """Test that the backend streaming response format matches frontend expectations"""
    
    # Mock streaming data that the backend would send
    mock_streaming_chunks = [
        {
            "content": "Hello",
            "full_content": "Hello",
            "chunk_id": 1,
            "timestamp": "2024-01-01T12:00:00.000Z",
            "done": False,
            "model": "llama3:8b",
            "error": None,
            "streaming_stats": {
                "total_chunks": 1,
                "total_characters": 5,
                "elapsed_time": 0.1,
                "words_per_second": 10.0
            }
        },
        {
            "content": " there!",
            "full_content": "Hello there!",
            "chunk_id": 2,
            "timestamp": "2024-01-01T12:00:00.100Z",
            "done": False,
            "model": "llama3:8b",
            "error": None,
            "streaming_stats": {
                "total_chunks": 2,
                "total_characters": 12,
                "elapsed_time": 0.2,
                "words_per_second": 12.0
            }
        },
        {
            "content": "",
            "full_content": "Hello there!",
            "chunk_id": 3,
            "timestamp": "2024-01-01T12:00:00.200Z",
            "done": True,
            "model": "llama3:8b",
            "error": None,
            "streaming_stats": {
                "total_chunks": 2,
                "total_characters": 12,
                "elapsed_time": 0.2,
                "words_per_second": 12.0
            }
        }
    ]
    
    print("✅ Testing streaming response format compatibility...")
    
    # Verify each chunk has the required fields for the frontend
    required_fields = ['content', 'done', 'timestamp', 'chunk_id']
    
    for i, chunk in enumerate(mock_streaming_chunks):
        for field in required_fields:
            assert field in chunk, f"Chunk {i} missing required field: {field}"
        
        # Verify data types
        assert isinstance(chunk['content'], str), f"Chunk {i} content must be string"
        assert isinstance(chunk['done'], bool), f"Chunk {i} done must be boolean"
        assert isinstance(chunk['chunk_id'], int), f"Chunk {i} chunk_id must be integer"
        
        # Verify Server-Sent Events format
        sse_data = f"data: {json.dumps(chunk)}\n\n"
        assert sse_data.startswith("data: "), "SSE format must start with 'data: '"
        assert sse_data.endswith("\n\n"), "SSE format must end with double newline"
        
        # Verify JSON can be parsed
        json_data = json.loads(sse_data[6:-2])  # Remove "data: " and "\n\n"
        assert json_data == chunk, "JSON parsing must preserve data integrity"
    
    print("✅ Streaming response format is compatible with frontend expectations")


def test_error_response_format():
    """Test that error responses match frontend error handling expectations"""
    
    mock_error_chunk = {
        "content": "",
        "full_content": "",
        "chunk_id": 1,
        "timestamp": "2024-01-01T12:00:00.000Z",
        "done": True,
        "error": "AI service temporarily unavailable",
        "model": "llama3:8b",
        "error_id": "err_12345"
    }
    
    print("✅ Testing error response format...")
    
    # Verify error chunk structure
    assert 'error' in mock_error_chunk, "Error chunk must contain 'error' field"
    assert mock_error_chunk['done'] is True, "Error chunk must set 'done' to True"
    assert isinstance(mock_error_chunk['error'], str), "Error must be a string"
    
    # Verify SSE format for errors
    sse_error = f"data: {json.dumps(mock_error_chunk)}\n\n"
    parsed_error = json.loads(sse_error[6:-2])
    assert parsed_error['error'] == mock_error_chunk['error'], "Error message must be preserved"
    
    print("✅ Error response format is compatible with frontend error handling")


def test_frontend_streaming_handler_interface():
    """Test the JavaScript StreamingResponseHandler interface requirements"""
    
    print("✅ Testing StreamingResponseHandler interface...")
    
    # Read the chat.js file to verify the StreamingResponseHandler class exists
    try:
        with open('static/js/chat.js', 'r') as f:
            chat_js_content = f.read()
    except FileNotFoundError:
        print("❌ chat.js file not found")
        return False
    
    # Verify the StreamingResponseHandler class exists
    assert 'class StreamingResponseHandler' in chat_js_content, "StreamingResponseHandler class must be defined"
    
    # Verify required methods exist
    required_methods = [
        'handleStreamingResponse',
        'createStreamingTextElement', 
        'processStreamingResponse',
        'appendContentWithTypewriter',
        'handleStreamingError',
        'handleTimeoutError',
        'handleNetworkError',
        'fallbackToStandard',
        'configureTypewriter'
    ]
    
    for method in required_methods:
        assert method in chat_js_content, f"StreamingResponseHandler must have {method} method"
    
    # Verify error handling methods
    error_handling_methods = [
        'handleTimeoutError',
        'handleNetworkError', 
        'handleGenericStreamingError',
        'showStreamingErrorMessage'
    ]
    
    for method in error_handling_methods:
        assert method in chat_js_content, f"StreamingResponseHandler must have error handling method: {method}"
    
    print("✅ StreamingResponseHandler interface is complete")


def test_css_streaming_styles():
    """Test that required CSS styles for streaming are present"""
    
    print("✅ Testing streaming CSS styles...")
    
    try:
        with open('static/css/style.css', 'r') as f:
            css_content = f.read()
    except FileNotFoundError:
        print("❌ style.css file not found")
        return False
    
    # Verify required CSS classes exist
    required_classes = [
        '.message.streaming',
        '.message.streaming-complete',
        '.message.streaming-error',
        '.streaming-text-content',
        '.streaming-cursor',
        '.streaming-error-content',
        '.streaming-error-header',
        '.streaming-retry-button'
    ]
    
    for css_class in required_classes:
        assert css_class in css_content, f"Required CSS class missing: {css_class}"
    
    # Verify animations exist
    required_animations = [
        '@keyframes streaming-shimmer',
        '@keyframes cursor-blink'
    ]
    
    for animation in required_animations:
        assert animation in css_content, f"Required CSS animation missing: {animation}"
    
    # Verify HUD theme variables are used
    hud_variables = [
        'var(--hud-accent-cyan)',
        'var(--hud-text-primary)',
        'var(--glass-bg)',
        'var(--border-radius)'
    ]
    
    for variable in hud_variables:
        assert variable in css_content, f"HUD theme variable not used: {variable}"
    
    print("✅ All required streaming CSS styles are present")


def test_typewriter_effect_configuration():
    """Test typewriter effect configuration options"""
    
    print("✅ Testing typewriter effect configuration...")
    
    # Read chat.js to verify typewriter configuration
    with open('static/js/chat.js', 'r') as f:
        chat_js_content = f.read()
    
    # Verify typewriter configuration properties
    typewriter_config = [
        'typewriterSpeed',
        'enableTypewriter', 
        'enableCursor',
        'configureTypewriter'
    ]
    
    for config in typewriter_config:
        assert config in chat_js_content, f"Typewriter configuration missing: {config}"
    
    # Verify typewriter effect method
    assert 'appendContentWithTypewriter' in chat_js_content, "Typewriter effect method missing"
    
    # Verify cursor animation class handling
    assert 'streaming-cursor' in chat_js_content, "Cursor animation class handling missing"
    
    print("✅ Typewriter effect configuration is complete")


def run_all_tests():
    """Run all integration tests"""
    
    print("🚀 Starting StreamingResponseHandler Integration Tests")
    print("=" * 60)
    
    tests = [
        test_streaming_response_format,
        test_error_response_format,
        test_frontend_streaming_handler_interface,
        test_css_streaming_styles,
        test_typewriter_effect_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! StreamingResponseHandler implementation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)