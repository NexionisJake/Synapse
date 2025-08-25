#!/usr/bin/env python3
"""
Serendipity Issues Analysis Report

This script analyzes the specific issues found during the comprehensive test
and provides detailed diagnostics and recommendations.
"""

import json
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from serendipity_service import get_serendipity_service, SerendipityService


def analyze_serendipity_issues():
    """Analyze specific serendipity issues identified during testing"""
    
    print("="*80)
    print("SERENDIPITY ISSUES ANALYSIS REPORT")
    print("="*80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues_found = []
    
    # Issue 1: Check Config Attributes
    print("1. CONFIGURATION ANALYSIS")
    print("-" * 40)
    try:
        config = get_config()
        
        # Check OLLAMA_URL attribute
        if not hasattr(config, 'OLLAMA_URL'):
            print("❌ ISSUE: Missing OLLAMA_URL config attribute")
            print("   Impact: AI service may not know where to connect")
            print("   Status: NON-CRITICAL (OLLAMA_HOST is used instead)")
            print(f"   Current OLLAMA_HOST: {getattr(config, 'OLLAMA_HOST', 'Not found')}")
            issues_found.append({
                'type': 'CONFIG_MISSING_ATTRIBUTE',
                'severity': 'LOW',
                'description': 'OLLAMA_URL attribute missing (OLLAMA_HOST used instead)',
                'impact': 'None - fallback works'
            })
        else:
            print("✅ OLLAMA_URL config attribute found")
        
        # Check AI Service Method
        print("\n   AI Service Method Check:")
        from ai_service import get_ai_service
        ai_service = get_ai_service()
        
        if hasattr(ai_service, 'generate_response'):
            print("   ✅ AI service has generate_response method")
        else:
            print("   ❌ AI service missing generate_response method")
            available_methods = [method for method in dir(ai_service) if not method.startswith('_')]
            print(f"   Available methods: {available_methods}")
            
            # Check for alternative methods
            if hasattr(ai_service, 'chat'):
                print("   ✅ Alternative 'chat' method found")
            elif hasattr(ai_service, 'generate'):
                print("   ✅ Alternative 'generate' method found")
            else:
                print("   ❌ No suitable generation method found")
                issues_found.append({
                    'type': 'AI_SERVICE_METHOD_MISSING',
                    'severity': 'MEDIUM',
                    'description': 'AI service missing expected generate_response method',
                    'impact': 'Test failures, but service may work with alternative methods'
                })
        
    except Exception as e:
        print(f"❌ ERROR during config analysis: {e}")
        issues_found.append({
            'type': 'CONFIG_ANALYSIS_ERROR',
            'severity': 'HIGH',
            'description': f'Failed to analyze configuration: {e}',
            'impact': 'Cannot determine configuration status'
        })
    
    # Issue 2: Check Serendipity Analysis Response Structure
    print(f"\n2. SERENDIPITY ANALYSIS RESPONSE STRUCTURE")
    print("-" * 40)
    try:
        # Check what keys are actually returned
        print("   Checking actual analysis response structure...")
        serendipity_service = get_serendipity_service()
        
        # Create minimal test data
        test_dir = "/tmp/serendipity_test"
        os.makedirs(test_dir, exist_ok=True)
        test_memory_file = Path(test_dir) / "test_memory.json"
        
        minimal_data = {
            "insights": [
                {
                    "category": "test",
                    "content": "Test insight 1",
                    "confidence": 0.9,
                    "tags": ["test"],
                    "evidence": "Test evidence",
                    "timestamp": "2025-08-25T10:00:00.000000"
                },
                {
                    "category": "test",
                    "content": "Test insight 2", 
                    "confidence": 0.8,
                    "tags": ["test"],
                    "evidence": "Test evidence 2",
                    "timestamp": "2025-08-25T11:00:00.000000"
                },
                {
                    "category": "test",
                    "content": "Test insight 3",
                    "confidence": 0.7,
                    "tags": ["test"],
                    "evidence": "Test evidence 3",
                    "timestamp": "2025-08-25T12:00:00.000000"
                }
            ],
            "conversation_summaries": [],
            "metadata": {"total_insights": 3}
        }
        
        with open(test_memory_file, 'w') as f:
            json.dump(minimal_data, f)
        
        print("   Running quick analysis to check response structure...")
        try:
            # Run with shorter timeout to avoid long waits
            os.environ['SERENDIPITY_ANALYSIS_TIMEOUT'] = '30'
            result = serendipity_service.analyze_memory(memory_file_path=str(test_memory_file))
            
            print(f"   ✅ Analysis completed successfully")
            print(f"   Response keys: {list(result.keys())}")
            
            # Check for missing expected keys
            expected_keys = ['connections', 'patterns', 'recommendations', 'metadata']
            missing_keys = []
            
            for key in expected_keys:
                if key not in result:
                    missing_keys.append(key)
                    print(f"   ❌ Missing key: {key}")
                else:
                    if isinstance(result[key], list):
                        print(f"   ✅ {key}: {len(result[key])} items")
                    else:
                        print(f"   ✅ {key}: present")
            
            if missing_keys:
                issues_found.append({
                    'type': 'ANALYSIS_RESPONSE_STRUCTURE',
                    'severity': 'MEDIUM',
                    'description': f'Analysis response missing keys: {missing_keys}',
                    'impact': 'Tests may fail, but core functionality works'
                })
            
            # Check analysis quality
            connections = result.get('connections', [])
            if len(connections) == 0:
                print("   ⚠️  WARNING: No connections found in analysis")
                print("   This could indicate:")
                print("      - AI model needs better prompting")
                print("      - Insufficient or low-quality test data")
                print("      - Response parsing issues")
                issues_found.append({
                    'type': 'NO_CONNECTIONS_FOUND',
                    'severity': 'MEDIUM', 
                    'description': 'Analysis returns no connections',
                    'impact': 'Users may not see meaningful serendipity insights'
                })
            
        except Exception as analysis_error:
            print(f"   ❌ Analysis failed: {analysis_error}")
            issues_found.append({
                'type': 'ANALYSIS_EXECUTION_ERROR',
                'severity': 'HIGH',
                'description': f'Analysis execution failed: {analysis_error}',
                'impact': 'Serendipity analysis is not functional'
            })
        
        finally:
            # Clean up
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            os.environ.pop('SERENDIPITY_ANALYSIS_TIMEOUT', None)
            
    except Exception as e:
        print(f"   ❌ ERROR during response structure analysis: {e}")
        issues_found.append({
            'type': 'RESPONSE_ANALYSIS_ERROR',
            'severity': 'HIGH',
            'description': f'Failed to analyze response structure: {e}',
            'impact': 'Cannot determine response quality'
        })
    
    # Issue 3: Check Performance Issues
    print(f"\n3. PERFORMANCE ANALYSIS")
    print("-" * 40)
    print("   Performance issues identified from test run:")
    print("   ❌ Analysis timeout: 363.53s exceeded 120s limit")
    print("   ❌ High disk usage: 94% detected during test")
    print("   ❌ High CPU usage: 84%+ detected during test")
    print("   ⚠️  Multiple retry attempts due to errors")
    
    issues_found.append({
        'type': 'PERFORMANCE_TIMEOUT',
        'severity': 'HIGH',
        'description': 'Analysis takes too long (363s vs 120s limit)',
        'impact': 'Poor user experience, potential timeouts'
    })
    
    issues_found.append({
        'type': 'RESOURCE_USAGE',
        'severity': 'MEDIUM',
        'description': 'High disk and CPU usage during analysis',
        'impact': 'System performance degradation'
    })
    
    # Issue 4: Check Missing Cache Attribute
    print(f"\n4. CACHE ATTRIBUTE ANALYSIS")
    print("-" * 40)
    try:
        serendipity_service = get_serendipity_service()
        
        if hasattr(serendipity_service, 'analysis_cache_ttl'):
            print("   ✅ analysis_cache_ttl attribute found")
        else:
            print("   ❌ analysis_cache_ttl attribute missing")
            print("   This causes retry errors during analysis")
            issues_found.append({
                'type': 'MISSING_CACHE_ATTRIBUTE',
                'severity': 'MEDIUM',
                'description': "SerendipityService missing 'analysis_cache_ttl' attribute",
                'impact': 'Causes retry failures and longer analysis times'
            })
        
    except Exception as e:
        print(f"   ❌ ERROR during cache analysis: {e}")
    
    # Summary and Recommendations
    print(f"\n{'='*80}")
    print("SUMMARY AND RECOMMENDATIONS")
    print("="*80)
    
    # Categorize issues by severity
    high_issues = [i for i in issues_found if i['severity'] == 'HIGH']
    medium_issues = [i for i in issues_found if i['severity'] == 'MEDIUM']
    low_issues = [i for i in issues_found if i['severity'] == 'LOW']
    
    print(f"Issues Found: {len(issues_found)} total")
    print(f"  🔴 High Severity: {len(high_issues)}")
    print(f"  🟡 Medium Severity: {len(medium_issues)}")
    print(f"  🟢 Low Severity: {len(low_issues)}")
    
    print(f"\nRECOMMENDATIONS:")
    print("-" * 40)
    
    if high_issues:
        print("🔴 CRITICAL FIXES NEEDED:")
        for issue in high_issues:
            print(f"   • {issue['description']}")
    
    if medium_issues:
        print("\n🟡 IMPROVEMENTS RECOMMENDED:")
        for issue in medium_issues:
            print(f"   • {issue['description']}")
    
    print(f"\n📋 SPECIFIC ACTION ITEMS:")
    print("1. Add 'analysis_cache_ttl' attribute to SerendipityService class")
    print("2. Optimize AI prompts to generate proper JSON responses")
    print("3. Implement response validation and structure enforcement")
    print("4. Add performance optimizations to reduce analysis time")
    print("5. Improve error handling and retry logic")
    print("6. Add resource monitoring and throttling")
    
    print(f"\n💡 OVERALL STATUS:")
    if len(high_issues) > 0:
        print("   ❌ SERENDIPITY HAS CRITICAL ISSUES - Immediate attention required")
    elif len(medium_issues) > 0:
        print("   ⚠️  SERENDIPITY WORKS BUT HAS ISSUES - Improvements recommended")
    else:
        print("   ✅ SERENDIPITY IS WORKING WELL - Minor optimizations possible")
    
    print("="*80)
    
    return issues_found


if __name__ == '__main__':
    analyze_serendipity_issues()
