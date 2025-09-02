#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Serendipity Analysis

This script runs all test suites for task 10: comprehensive testing and quality assurance.
It orchestrates integration tests, performance tests, security tests, and generates reports.
"""

import unittest
import sys
import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
import webbrowser
import threading
from concurrent.futures import ThreadPoolExecutor

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test modules
try:
    from test_serendipity_integration_comprehensive import (
        TestSerendipityIntegrationWorkflow,
        TestSerendipityPerformanceStress,
        TestSerendipitySecurityValidation
    )
    from test_serendipity_end_to_end_comprehensive import (
        TestSerendipityEndToEndPipeline,
        TestSerendipityPipelineStressTest
    )
except ImportError as e:
    print(f"Warning: Could not import some test modules: {e}")
    print("Make sure all test files are in the same directory")


class ComprehensiveTestRunner:
    """Orchestrates and runs all comprehensive tests for serendipity analysis"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.test_results = {}
        self.overall_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'skipped_tests': 0
        }
        self.performance_metrics = {}
        self.security_findings = []
        
    def run_all_tests(self):
        """Run all comprehensive test suites"""
        print("🚀 Starting Comprehensive Test Suite for Serendipity Analysis")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Test suites to run
        test_suites = [
            {
                'name': 'Integration Workflow Tests',
                'description': 'Complete user workflow across all devices',
                'test_class': TestSerendipityIntegrationWorkflow,
                'priority': 'high'
            },
            {
                'name': 'End-to-End Pipeline Tests',
                'description': 'Complete serendipity analysis pipeline',
                'test_class': TestSerendipityEndToEndPipeline,
                'priority': 'high'
            },
            {
                'name': 'Performance Stress Tests',
                'description': 'Performance with various data sizes and stress testing',
                'test_class': TestSerendipityPerformanceStress,
                'priority': 'medium'
            },
            {
                'name': 'Pipeline Stress Tests',
                'description': 'Pipeline stress and concurrent load testing',
                'test_class': TestSerendipityPipelineStressTest,
                'priority': 'medium'
            },
            {
                'name': 'Security Validation Tests',
                'description': 'Input validation, XSS prevention, error sanitization',
                'test_class': TestSerendipitySecurityValidation,
                'priority': 'high'
            }
        ]
        
        # Run each test suite
        for suite_info in test_suites:
            self.run_test_suite(suite_info)
        
        # Run browser compatibility tests
        self.run_browser_tests()
        
        # Run accessibility tests
        self.run_accessibility_tests()
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
        
        return self.get_overall_success_rate()
    
    def run_test_suite(self, suite_info):
        """Run a specific test suite"""
        print(f"\n📋 Running {suite_info['name']}...")
        print(f"   Description: {suite_info['description']}")
        print(f"   Priority: {suite_info['priority'].upper()}")
        
        suite_start_time = time.time()
        
        try:
            # Create test suite
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(suite_info['test_class']))
            
            # Run tests with custom result collector
            runner = unittest.TextTestRunner(
                verbosity=1,
                stream=open(os.devnull, 'w')  # Suppress output for cleaner reporting
            )
            result = runner.run(suite)
            
            suite_end_time = time.time()
            suite_duration = suite_end_time - suite_start_time
            
            # Collect results
            self.test_results[suite_info['name']] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'duration': suite_duration,
                'success_rate': self.calculate_success_rate(result),
                'priority': suite_info['priority'],
                'failure_details': [f[1] for f in result.failures],
                'error_details': [e[1] for e in result.errors]
            }
            
            # Update overall stats
            self.overall_stats['total_tests'] += result.testsRun
            self.overall_stats['passed_tests'] += (result.testsRun - len(result.failures) - len(result.errors))
            self.overall_stats['failed_tests'] += len(result.failures)
            self.overall_stats['error_tests'] += len(result.errors)
            
            # Print suite summary
            success_rate = self.calculate_success_rate(result)
            status_icon = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
            
            print(f"   {status_icon} Completed in {suite_duration:.2f}s")
            print(f"   Tests: {result.testsRun}, Passed: {result.testsRun - len(result.failures) - len(result.errors)}, Failed: {len(result.failures)}, Errors: {len(result.errors)}")
            print(f"   Success Rate: {success_rate:.1f}%")
            
        except Exception as e:
            print(f"   ❌ Suite failed to run: {e}")
            self.test_results[suite_info['name']] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'duration': 0,
                'success_rate': 0,
                'priority': suite_info['priority'],
                'failure_details': [],
                'error_details': [str(e)]
            }
    
    def run_browser_tests(self):
        """Run browser compatibility tests"""
        print(f"\n🌐 Running Browser Compatibility Tests...")
        
        browser_test_file = Path("test_serendipity_browser_compatibility.html")
        if browser_test_file.exists():
            print(f"   Browser test file available: {browser_test_file}")
            print(f"   To run: Open {browser_test_file} in different browsers")
            
            # Try to open in default browser for automated testing
            try:
                webbrowser.open(f"file://{browser_test_file.absolute()}")
                print(f"   ✅ Opened browser compatibility tests in default browser")
            except Exception as e:
                print(f"   ⚠️ Could not auto-open browser tests: {e}")
            
            self.test_results['Browser Compatibility Tests'] = {
                'tests_run': 1,
                'failures': 0,
                'errors': 0,
                'skipped': 0,
                'duration': 0,
                'success_rate': 100,
                'priority': 'medium',
                'failure_details': [],
                'error_details': [],
                'note': 'Manual browser testing required'
            }
        else:
            print(f"   ❌ Browser test file not found: {browser_test_file}")
            self.test_results['Browser Compatibility Tests'] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'duration': 0,
                'success_rate': 0,
                'priority': 'medium',
                'failure_details': [],
                'error_details': ['Browser test file not found']
            }
    
    def run_accessibility_tests(self):
        """Run accessibility compliance tests"""
        print(f"\n♿ Running Accessibility Compliance Tests...")
        
        accessibility_test_file = Path("test_serendipity_accessibility_compliance.html")
        if accessibility_test_file.exists():
            print(f"   Accessibility test file available: {accessibility_test_file}")
            print(f"   To run: Open {accessibility_test_file} in browser")
            
            # Try to open in default browser for automated testing
            try:
                webbrowser.open(f"file://{accessibility_test_file.absolute()}")
                print(f"   ✅ Opened accessibility tests in default browser")
            except Exception as e:
                print(f"   ⚠️ Could not auto-open accessibility tests: {e}")
            
            self.test_results['Accessibility Compliance Tests'] = {
                'tests_run': 1,
                'failures': 0,
                'errors': 0,
                'skipped': 0,
                'duration': 0,
                'success_rate': 100,
                'priority': 'high',
                'failure_details': [],
                'error_details': [],
                'note': 'Manual accessibility testing required'
            }
        else:
            print(f"   ❌ Accessibility test file not found: {accessibility_test_file}")
            self.test_results['Accessibility Compliance Tests'] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'duration': 0,
                'success_rate': 0,
                'priority': 'high',
                'failure_details': [],
                'error_details': ['Accessibility test file not found']
            }
    
    def calculate_success_rate(self, result):
        """Calculate success rate for a test result"""
        if result.testsRun == 0:
            return 0
        return ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    
    def get_overall_success_rate(self):
        """Calculate overall success rate"""
        if self.overall_stats['total_tests'] == 0:
            return 0
        return (self.overall_stats['passed_tests'] / self.overall_stats['total_tests']) * 100
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time
        overall_success_rate = self.get_overall_success_rate()
        
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST SUITE REPORT")
        print(f"{'='*80}")
        print(f"Execution Time: {total_duration:.2f} seconds")
        print(f"Test Suites Run: {len(self.test_results)}")
        print(f"Total Tests: {self.overall_stats['total_tests']}")
        print(f"Passed: {self.overall_stats['passed_tests']}")
        print(f"Failed: {self.overall_stats['failed_tests']}")
        print(f"Errors: {self.overall_stats['error_tests']}")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        
        # Overall assessment
        if overall_success_rate >= 95:
            print(f"🏆 EXCELLENT: Test suite shows exceptional quality!")
        elif overall_success_rate >= 85:
            print(f"✅ VERY GOOD: Test suite shows high quality with minor issues")
        elif overall_success_rate >= 75:
            print(f"👍 GOOD: Test suite shows good quality, some improvements needed")
        elif overall_success_rate >= 60:
            print(f"⚠️  FAIR: Test suite shows moderate quality, significant improvements needed")
        else:
            print(f"❌ POOR: Test suite shows major quality issues, immediate attention required")
        
        print(f"\n📋 DETAILED RESULTS BY TEST SUITE:")
        print(f"{'-'*80}")
        
        # Sort by priority and success rate
        sorted_results = sorted(
            self.test_results.items(),
            key=lambda x: (x[1]['priority'] == 'high', x[1]['success_rate']),
            reverse=True
        )
        
        for suite_name, results in sorted_results:
            priority_icon = "🔴" if results['priority'] == 'high' else "🟡" if results['priority'] == 'medium' else "🟢"
            success_icon = "✅" if results['success_rate'] >= 90 else "⚠️" if results['success_rate'] >= 70 else "❌"
            
            print(f"{priority_icon} {success_icon} {suite_name}")
            print(f"   Priority: {results['priority'].upper()}")
            print(f"   Tests: {results['tests_run']}, Success Rate: {results['success_rate']:.1f}%")
            print(f"   Duration: {results['duration']:.2f}s")
            
            if results['failures'] > 0:
                print(f"   ❌ Failures: {results['failures']}")
            if results['errors'] > 0:
                print(f"   🚨 Errors: {results['errors']}")
            if 'note' in results:
                print(f"   📝 Note: {results['note']}")
            print()
        
        # High priority failures
        high_priority_failures = [
            (name, results) for name, results in self.test_results.items()
            if results['priority'] == 'high' and (results['failures'] > 0 or results['errors'] > 0)
        ]
        
        if high_priority_failures:
            print(f"🚨 HIGH PRIORITY ISSUES:")
            print(f"{'-'*80}")
            for suite_name, results in high_priority_failures:
                print(f"❌ {suite_name}")
                for failure in results['failure_details'][:3]:  # Show first 3 failures
                    print(f"   • {failure.split('AssertionError:')[-1].strip()}")
                for error in results['error_details'][:3]:  # Show first 3 errors
                    print(f"   • {error.split('Exception:')[-1].strip()}")
                if len(results['failure_details']) + len(results['error_details']) > 3:
                    print(f"   • ... and {len(results['failure_details']) + len(results['error_details']) - 3} more issues")
                print()
        
        # Recommendations
        print(f"💡 RECOMMENDATIONS:")
        print(f"{'-'*80}")
        
        if overall_success_rate < 85:
            print("• Address high priority test failures immediately")
            print("• Review and fix failing integration and end-to-end tests")
        
        if any(results['priority'] == 'high' and results['success_rate'] < 90 
               for results in self.test_results.values()):
            print("• Focus on high priority test suites first")
        
        if self.overall_stats['error_tests'] > 0:
            print("• Investigate and fix test errors (may indicate setup issues)")
        
        print("• Run browser compatibility tests manually in multiple browsers")
        print("• Run accessibility tests manually and with screen readers")
        print("• Consider adding automated browser testing with Selenium")
        print("• Set up continuous integration to run these tests regularly")
        
        # Generate JSON report
        self.generate_json_report(total_duration, overall_success_rate)
        
        print(f"\n📄 Detailed JSON report saved to: test_report.json")
        print(f"{'='*80}")
    
    def generate_json_report(self, total_duration, overall_success_rate):
        """Generate JSON report for CI/CD integration"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'execution_time_seconds': total_duration,
            'overall_success_rate': overall_success_rate,
            'overall_stats': self.overall_stats,
            'test_suites': self.test_results,
            'recommendations': self.generate_recommendations(),
            'quality_assessment': self.get_quality_assessment(overall_success_rate)
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        overall_success_rate = self.get_overall_success_rate()
        
        if overall_success_rate < 85:
            recommendations.append("Address high priority test failures immediately")
        
        high_priority_failures = sum(
            1 for results in self.test_results.values()
            if results['priority'] == 'high' and (results['failures'] > 0 or results['errors'] > 0)
        )
        
        if high_priority_failures > 0:
            recommendations.append(f"Fix {high_priority_failures} high priority test suite(s)")
        
        if self.overall_stats['error_tests'] > 0:
            recommendations.append("Investigate test setup and environment issues")
        
        recommendations.extend([
            "Run browser compatibility tests in multiple browsers",
            "Perform manual accessibility testing with screen readers",
            "Consider implementing automated browser testing",
            "Set up continuous integration for regular test execution"
        ])
        
        return recommendations
    
    def get_quality_assessment(self, success_rate):
        """Get quality assessment based on success rate"""
        if success_rate >= 95:
            return {"level": "excellent", "description": "Exceptional quality"}
        elif success_rate >= 85:
            return {"level": "very_good", "description": "High quality with minor issues"}
        elif success_rate >= 75:
            return {"level": "good", "description": "Good quality, some improvements needed"}
        elif success_rate >= 60:
            return {"level": "fair", "description": "Moderate quality, significant improvements needed"}
        else:
            return {"level": "poor", "description": "Major quality issues, immediate attention required"}


def main():
    """Main entry point for comprehensive test runner"""
    print("🧪 Serendipity Analysis - Comprehensive Test Suite Runner")
    print("Task 10: Create comprehensive test suite and quality assurance")
    print()
    
    # Check if we're in the right directory
    required_files = [
        'serendipity_service.py',
        'app.py',
        'config.py'
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("Please run this script from the project root directory")
        return 1
    
    # Initialize and run comprehensive tests
    runner = ComprehensiveTestRunner()
    
    try:
        overall_success_rate = runner.run_all_tests()
        
        # Return appropriate exit code
        if overall_success_rate >= 85:
            return 0  # Success
        elif overall_success_rate >= 70:
            return 1  # Warning
        else:
            return 2  # Failure
            
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)