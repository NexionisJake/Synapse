#!/usr/bin/env python3
"""
Test script to verify dashboard integration with enhanced UI
"""

import requests
import json
import sys
import time

def test_dashboard_integration():
    """Test the dashboard integration functionality"""
    base_url = "http://localhost:5000"
    
    print("Testing Dashboard Integration...")
    print("=" * 50)
    
    # Test 1: Check if main index page loads (integrated layout)
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ Main index page loads successfully")
            # Check if it contains the integrated layout elements
            if 'hud-container' in response.text and 'cognitive-dashboard' in response.text:
                print("✓ Integrated two-column layout detected")
            else:
                print("⚠ Integrated layout elements not found")
        else:
            print(f"✗ Main index page failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Main index page error: {e}")
    
    # Test 2: Check if standalone dashboard page loads
    try:
        response = requests.get(f"{base_url}/dashboard")
        if response.status_code == 200:
            print("✓ Standalone dashboard page loads successfully")
        else:
            print(f"✗ Standalone dashboard page failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Standalone dashboard page error: {e}")
    
    # Test 3: Test insights API endpoint
    try:
        response = requests.get(f"{base_url}/api/insights")
        if response.status_code == 200:
            data = response.json()
            print("✓ Insights API endpoint working")
            print(f"  - Insights count: {len(data.get('insights', []))}")
            print(f"  - Summaries count: {len(data.get('conversation_summaries', []))}")
        else:
            print(f"✗ Insights API failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Insights API error: {e}")
    
    # Test 4: Test serendipity API endpoint
    try:
        response = requests.post(f"{base_url}/api/serendipity", 
                               headers={'Content-Type': 'application/json'},
                               json={})
        if response.status_code in [200, 503]:  # 503 is OK if no data available
            data = response.json()
            print("✓ Serendipity API endpoint working")
            print(f"  - Connections count: {len(data.get('connections', []))}")
            print(f"  - Meta patterns count: {len(data.get('meta_patterns', []))}")
        else:
            print(f"✗ Serendipity API failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Serendipity API error: {e}")
    
    # Test 5: Check AI service status
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            data = response.json()
            print("✓ AI service status endpoint working")
            print(f"  - Status: {data.get('status', 'unknown')}")
        else:
            print(f"✗ AI service status failed: {response.status_code}")
    except Exception as e:
        print(f"✗ AI service status error: {e}")
    
    print("\nDashboard Integration Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    print("Dashboard Integration Test")
    print("Make sure the Synapse server is running on localhost:5000")
    print()
    
    # Wait a moment for user to start server if needed
    input("Press Enter to continue with tests...")
    
    test_dashboard_integration()