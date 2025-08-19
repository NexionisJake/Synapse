#!/usr/bin/env python3
"""
Validation script to check dashboard integration files and structure
"""

import os
import re
import json

def validate_integration():
    """Validate the dashboard integration implementation"""
    print("Validating Dashboard Integration...")
    print("=" * 50)
    
    # Test 1: Check if templates have been updated
    print("1. Checking template files...")
    
    # Check index.html for integrated layout
    index_path = "templates/index.html"
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            index_content = f.read()
        
        if 'hud-container' in index_content and 'cognitive-dashboard' in index_content:
            print("   ✓ index.html has integrated two-column layout")
        else:
            print("   ✗ index.html missing integrated layout elements")
            
        if 'chat.js' in index_content and 'dashboard.js' in index_content:
            print("   ✓ index.html includes both chat and dashboard scripts")
        else:
            print("   ✗ index.html missing required scripts")
    else:
        print("   ✗ index.html not found")
    
    # Check dashboard.html for updated structure
    dashboard_path = "templates/dashboard.html"
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            dashboard_content = f.read()
        
        if 'hud-container' in dashboard_content:
            print("   ✓ dashboard.html updated with new layout")
        else:
            print("   ✗ dashboard.html not updated with new layout")
    else:
        print("   ✗ dashboard.html not found")
    
    # Test 2: Check JavaScript files
    print("\n2. Checking JavaScript files...")
    
    # Check dashboard.js for integration features
    dashboard_js_path = "static/js/dashboard.js"
    if os.path.exists(dashboard_js_path):
        with open(dashboard_js_path, 'r') as f:
            dashboard_js_content = f.read()
        
        integration_features = [
            'ensureBackwardCompatibility',
            'handleStreamingIntegration',
            'setupIntegratedLayoutFeatures',
            'notifyInsightUpdate'
        ]
        
        missing_features = []
        for feature in integration_features:
            if feature not in dashboard_js_content:
                missing_features.append(feature)
        
        if not missing_features:
            print("   ✓ dashboard.js has all integration features")
        else:
            print(f"   ✗ dashboard.js missing features: {', '.join(missing_features)}")
    else:
        print("   ✗ dashboard.js not found")
    
    # Check if cognitive-charts.js exists
    charts_js_path = "static/js/cognitive-charts.js"
    if os.path.exists(charts_js_path):
        print("   ✓ cognitive-charts.js exists")
    else:
        print("   ✗ cognitive-charts.js not found")
    
    # Test 3: Check app.py for required endpoints
    print("\n3. Checking backend endpoints...")
    
    app_path = "app.py"
    if os.path.exists(app_path):
        with open(app_path, 'r') as f:
            app_content = f.read()
        
        required_endpoints = [
            '/api/insights',
            '/api/serendipity',
            '/dashboard'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in app_content:
                missing_endpoints.append(endpoint)
        
        if not missing_endpoints:
            print("   ✓ All required API endpoints exist")
        else:
            print(f"   ✗ Missing endpoints: {', '.join(missing_endpoints)}")
    else:
        print("   ✗ app.py not found")
    
    # Test 4: Check CSS for HUD theme
    print("\n4. Checking CSS styling...")
    
    css_path = "static/css/style.css"
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        hud_elements = [
            'hud-container',
            'cognitive-dashboard',
            'glass-panel'
        ]
        
        missing_elements = []
        for element in hud_elements:
            if element not in css_content:
                missing_elements.append(element)
        
        if not missing_elements:
            print("   ✓ CSS has HUD theme elements")
        else:
            print(f"   ✗ CSS missing elements: {', '.join(missing_elements)}")
    else:
        print("   ✗ style.css not found")
    
    # Test 5: Check for required JavaScript dependencies
    print("\n5. Checking JavaScript dependencies...")
    
    required_js_files = [
        "static/js/chat.js",
        "static/js/dashboard.js",
        "static/js/cognitive-charts.js",
        "static/js/performance-optimizer.js",
        "static/js/streaming-performance-monitor.js",
        "static/js/loading-feedback.js",
        "static/js/error-handlers.js"
    ]
    
    missing_js = []
    for js_file in required_js_files:
        if not os.path.exists(js_file):
            missing_js.append(js_file)
    
    if not missing_js:
        print("   ✓ All required JavaScript files exist")
    else:
        print(f"   ✗ Missing JavaScript files: {', '.join(missing_js)}")
    
    print("\nValidation Complete!")
    print("=" * 50)

if __name__ == "__main__":
    # Change to synapse-project directory
    if os.path.basename(os.getcwd()) != 'synapse-project':
        if os.path.exists('synapse-project'):
            os.chdir('synapse-project')
        else:
            print("Error: synapse-project directory not found")
            exit(1)
    
    validate_integration()