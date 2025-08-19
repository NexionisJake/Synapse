#!/usr/bin/env python3
"""
Simple Test Runner for Synapse AI Web Application

This script runs a subset of tests to verify the comprehensive test suite is working.
"""

import unittest
import sys
import os

def run_test_subset():
    """Run a subset of tests to verify functionality"""
    print("Running Synapse AI Test Suite - Subset")
    print("=" * 50)
    
    # Test modules to run
    test_modules = [
        'test_fixtures',
        'test_additional_coverage.TestDataValidation',
        'test_comprehensive_integration.TestCompleteConversationFlow.test_complete_chat_to_memory_flow',
        'test_ai_service.TestAIService.test_ai_service_initialization_success',
        'test_memory_service.TestMemoryService.test_memory_service_initialization',
        'test_chat_endpoint.TestChatEndpoint.test_chat_endpoint_success'
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_module in test_modules:
        print(f"\nRunning {test_module}...")
        try:
            # Load and run the test
            loader = unittest.TestLoader()
            if '.' in test_module:
                # Specific test class or method
                suite = loader.loadTestsFromName(test_module)
            else:
                # Entire module
                suite = loader.loadTestsFromName(test_module)
            
            runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout, buffer=True)
            result = runner.run(suite)
            
            total_tests += result.testsRun
            passed_tests += result.testsRun - len(result.failures) - len(result.errors)
            failed_tests += len(result.failures) + len(result.errors)
            
            if result.failures or result.errors:
                print(f"❌ {test_module} - {len(result.failures)} failures, {len(result.errors)} errors")
            else:
                print(f"✅ {test_module} - All tests passed")
                
        except Exception as e:
            print(f"❌ {test_module} - Error loading tests: {e}")
            failed_tests += 1
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All tests in subset passed!")
        print("\nComprehensive test suite is ready!")
        print("\nTo run all tests, use:")
        print("  python test_runner.py")
        print("  python -m unittest discover -v")
        return True
    else:
        print(f"\n❌ {failed_tests} tests failed")
        return False

if __name__ == '__main__':
    success = run_test_subset()
    sys.exit(0 if success else 1)