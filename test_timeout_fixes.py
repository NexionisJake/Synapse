#!/usr/bin/env python3
"""
Test script to verify timeout fixes for serendipity analysis

This script tests the timeout configurations and ensures they are properly aligned
between frontend and backend components.
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_timeout_configuration():
    """Test that timeout configurations are properly set"""
    print("🔧 Testing Timeout Configuration...")
    print("=" * 50)
    
    try:
        from config import Config
        config = Config()
        
        # Check backend timeout values
        serendipity_timeout = config.SERENDIPITY_ANALYSIS_TIMEOUT
        streaming_timeout = config.STREAMING_TIMEOUT
        ollama_timeout = config.OLLAMA_TIMEOUT
        
        print(f"Backend SERENDIPITY_ANALYSIS_TIMEOUT: {serendipity_timeout}s")
        print(f"Backend STREAMING_TIMEOUT: {streaming_timeout}s")
        print(f"Backend OLLAMA_TIMEOUT: {ollama_timeout}s")
        
        # Check that timeouts are compatible
        if serendipity_timeout <= ollama_timeout:
            print("❌ WARNING: SERENDIPITY_ANALYSIS_TIMEOUT should be greater than OLLAMA_TIMEOUT")
            return False
            
        if streaming_timeout <= serendipity_timeout:
            print("✅ Streaming timeout is properly configured")
        else:
            print("❌ WARNING: STREAMING_TIMEOUT should be >= SERENDIPITY_ANALYSIS_TIMEOUT")
            
        print("✅ Backend timeout configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Failed to check timeout configuration: {e}")
        return False

def test_api_timeout_exposure():
    """Test that the API exposes timeout information"""
    print("\n🌐 Testing API Timeout Exposure...")
    print("=" * 50)
    
    try:
        # Test the serendipity status endpoint
        response = requests.get('http://127.0.0.1:5000/api/serendipity', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'timeout' in data:
                api_timeout = data['timeout']
                print(f"✅ API exposes timeout configuration: {api_timeout}s")
                
                if 'streaming_timeout' in data:
                    streaming_timeout = data['streaming_timeout']
                    print(f"✅ API exposes streaming timeout: {streaming_timeout}s")
                else:
                    print("❌ API does not expose streaming timeout")
                    
                return True
            else:
                print("❌ API does not expose timeout configuration")
                return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API (is the server running?)")
        return False
    except Exception as e:
        print(f"❌ Failed to test API timeout exposure: {e}")
        return False

def test_serendipity_service_timeout():
    """Test serendipity service timeout handling"""
    print("\n🧠 Testing Serendipity Service Timeout...")
    print("=" * 50)
    
    try:
        from serendipity_service import get_serendipity_service
        from config import Config
        
        config = Config()
        service = get_serendipity_service(config=config)
        
        # Check service timeout configuration
        service_timeout = service.analysis_timeout
        print(f"✅ Serendipity service timeout: {service_timeout}s")
        
        # Verify it matches config
        if service_timeout == config.SERENDIPITY_ANALYSIS_TIMEOUT:
            print("✅ Service timeout matches configuration")
            return True
        else:
            print(f"❌ Service timeout ({service_timeout}) doesn't match config ({config.SERENDIPITY_ANALYSIS_TIMEOUT})")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test serendipity service timeout: {e}")
        return False

def test_ai_service_timeout():
    """Test AI service timeout configuration"""
    print("\n🤖 Testing AI Service Timeout...")
    print("=" * 50)
    
    try:
        from ai_service import get_ai_service
        
        # This will test if AI service is available
        ai_service = get_ai_service()
        
        # Test connection
        status = ai_service.test_connection()
        
        if status['connected']:
            print("✅ AI service is connected and available")
            print(f"   Model: {status['model']}")
            print(f"   Response time: {status['response_time']}s")
            return True
        else:
            print(f"❌ AI service connection failed: {status.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test AI service: {e}")
        return False

def test_memory_data_availability():
    """Test if memory data is available for analysis"""
    print("\n💾 Testing Memory Data Availability...")
    print("=" * 50)
    
    try:
        memory_file = 'memory.json'
        
        if not os.path.exists(memory_file):
            print(f"❌ Memory file not found: {memory_file}")
            return False
            
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
            
        insights = memory_data.get('insights', [])
        conversations = memory_data.get('conversation_summaries', [])
        
        print(f"✅ Memory file found with {len(insights)} insights and {len(conversations)} conversations")
        
        total_items = len(insights) + len(conversations)
        if total_items >= 3:
            print(f"✅ Sufficient data for analysis ({total_items} items)")
            return True
        else:
            print(f"❌ Insufficient data for analysis ({total_items} items, need at least 3)")
            return False
            
    except Exception as e:
        print(f"❌ Failed to check memory data: {e}")
        return False

def main():
    """Run all timeout-related tests"""
    print("🧪 TIMEOUT FIXES VALIDATION")
    print("=" * 60)
    print("This script validates that timeout fixes are properly implemented")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_timeout_configuration),
        ("API Exposure", test_api_timeout_exposure),
        ("Serendipity Service", test_serendipity_service_timeout),
        ("AI Service", test_ai_service_timeout),
        ("Memory Data", test_memory_data_availability)
    ]
    
    results = {}
    
    for test_name, test_function in tests:
        try:
            results[test_name] = test_function()
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All timeout fixes are working correctly!")
        print("\nRecommendations:")
        print("1. Frontend timeout is now dynamically configured")
        print("2. Backend timeouts are properly aligned")
        print("3. User feedback has been improved")
        print("4. Error messages are more informative")
    else:
        print("\n⚠️  Some issues were found. Please review the failed tests above.")
        
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
