#!/usr/bin/env python3
"""
Ollama Connection Diagnostic Script

This script helps diagnose issues with Ollama connection and response format.
"""

import ollama
import json
import sys
import time

def test_ollama_connection():
    """Test basic Ollama connection and response format"""
    print("🔍 Diagnosing Ollama Connection...")
    print("=" * 50)
    
    try:
        # Test 1: Check if Ollama is running
        print("1. Testing Ollama service availability...")
        try:
            models = ollama.list()
            print(f"✅ Ollama is running")
            print(f"   Models response type: {type(models)}")
            print(f"   Models response: {models}")
            
            if isinstance(models, dict) and 'models' in models:
                model_names = []
                for model in models['models']:
                    if isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])
                    else:
                        model_names.append(str(model))
                print(f"   Available models: {model_names}")
            else:
                print(f"   Available models: Could not parse model list")
        except Exception as e:
            print(f"❌ Ollama service not available: {e}")
            return False
        
        # Test 2: Test simple chat request
        print("\n2. Testing simple chat request...")
        try:
            response = ollama.chat(
                model='llama3:8b',
                messages=[
                    {'role': 'user', 'content': 'Hello, respond with just "Hi there!"'}
                ]
            )
            
            print(f"✅ Chat request successful")
            print(f"   Response type: {type(response)}")
            
            # Handle both new typed format and old dict format
            content = None
            if hasattr(response, 'message'):
                # New typed response format
                message = response.message
                print(f"   Message type: {type(message)}")
                if hasattr(message, 'content'):
                    content = message.content
                    print(f"   Content type: {type(content)}")
                    print(f"   Content: '{content[:100]}{'...' if len(content) > 100 else ''}'")
                else:
                    print(f"   ❌ Message missing 'content' attribute")
                    return False
            elif isinstance(response, dict):
                # Old dict format
                print(f"   Response keys: {list(response.keys())}")
                if 'message' in response:
                    message = response['message']
                    print(f"   Message type: {type(message)}")
                    if isinstance(message, dict) and 'content' in message:
                        content = message['content']
                        print(f"   Content type: {type(content)}")
                        print(f"   Content: '{content[:100]}{'...' if len(content) > 100 else ''}'")
                    else:
                        print(f"   ❌ Message missing 'content' field or not a dict")
                        return False
                else:
                    print(f"   ❌ Response missing 'message' field")
                    return False
            else:
                print(f"   ❌ Response format not recognized")
                return False
            
            if not content:
                print(f"   ❌ Could not extract content from response")
                return False
                
        except Exception as e:
            print(f"❌ Chat request failed: {e}")
            print(f"   Error type: {type(e)}")
            return False
        
        # Test 3: Test with system prompt
        print("\n3. Testing chat with system prompt...")
        try:
            response = ollama.chat(
                model='llama3:8b',
                messages=[
                    {'role': 'system', 'content': 'You are a helpful assistant.'},
                    {'role': 'user', 'content': 'Say hello in one word.'}
                ]
            )
            
            # Extract content using the same logic as above
            content = None
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                content = response.message.content
            elif isinstance(response, dict) and 'message' in response and 'content' in response['message']:
                content = response['message']['content']
            
            if content:
                print(f"✅ System prompt test successful")
                print(f"   Response: '{content[:50]}{'...' if len(content) > 50 else ''}'")
            else:
                print(f"❌ System prompt test failed - invalid response format")
                return False
                
        except Exception as e:
            print(f"❌ System prompt test failed: {e}")
            return False
        
        # Test 4: Test response timing
        print("\n4. Testing response timing...")
        try:
            start_time = time.time()
            response = ollama.chat(
                model='llama3:8b',
                messages=[
                    {'role': 'user', 'content': 'Count from 1 to 5.'}
                ]
            )
            response_time = time.time() - start_time
            
            print(f"✅ Timing test successful")
            print(f"   Response time: {response_time:.2f} seconds")
            
            if response_time > 10:
                print(f"   ⚠️  Response time is slow (>{response_time:.1f}s)")
            
        except Exception as e:
            print(f"❌ Timing test failed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All Ollama diagnostic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during diagnostics: {e}")
        return False

def test_ollama_streaming():
    """Test Ollama streaming response"""
    print("\n🔄 Testing Ollama Streaming...")
    print("=" * 50)
    
    try:
        response_parts = []
        for chunk in ollama.chat(
            model='llama3:8b',
            messages=[{'role': 'user', 'content': 'Say "Hello World" and nothing else.'}],
            stream=True
        ):
            response_parts.append(chunk)
            if len(response_parts) > 10:  # Limit for testing
                break
        
        print(f"✅ Streaming test successful")
        print(f"   Received {len(response_parts)} chunks")
        
        if response_parts:
            first_chunk = response_parts[0]
            print(f"   First chunk type: {type(first_chunk)}")
            print(f"   First chunk keys: {list(first_chunk.keys()) if isinstance(first_chunk, dict) else 'Not a dict'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

if __name__ == "__main__":
    print("Ollama Diagnostic Tool")
    print("=" * 50)
    
    # Run diagnostics
    connection_ok = test_ollama_connection()
    
    if connection_ok:
        streaming_ok = test_ollama_streaming()
    
    print("\n" + "=" * 50)
    if connection_ok:
        print("✅ Ollama connection is working correctly")
        print("   The issue may be elsewhere in the application")
    else:
        print("❌ Ollama connection has issues")
        print("   Please check:")
        print("   - Ollama is running (ollama serve)")
        print("   - Model llama3:8b is available (ollama pull llama3:8b)")
        print("   - No firewall blocking localhost:11434")
    
    sys.exit(0 if connection_ok else 1)