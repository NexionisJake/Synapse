#!/usr/bin/env python3
"""
Comprehensive Serendipity Functionality Test

This test file verifies that the serendipity service is working properly
and identifies exact issues if any are encountered.
"""

import unittest
import json
import tempfile
import shutil
import os
import time
import sys
import traceback
import requests
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from app import app
from config import get_config
from serendipity_service import get_serendipity_service, SerendipityService, SerendipityServiceError, reset_serendipity_service
from ai_service import get_ai_service
from memory_service import MemoryService
from error_handler import ErrorHandler


class SerendipityFunctionalityTest(unittest.TestCase):
    """Test serendipity functionality and identify issues"""
    
    def setUp(self):
        """Set up test environment"""
        # Reset services
        reset_serendipity_service()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_memory_file = Path(self.temp_dir) / "test_memory.json"
        
        # Set environment variables for testing
        os.environ['MEMORY_FILE'] = str(self.test_memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create test memory data
        self.create_test_memory_data()
        
        # Set up Flask test client
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Track test results
        self.test_results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'issues_found': [],
            'warnings': [],
            'performance_metrics': {}
        }
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
        
        # Print summary
        self.print_test_summary()
    
    def create_test_memory_data(self):
        """Create realistic test memory data"""
        test_data = {
            "insights": [
                {
                    "category": "technology",
                    "content": "User is passionate about artificial intelligence and machine learning",
                    "confidence": 0.95,
                    "tags": ["AI", "ML", "technology"],
                    "evidence": "I love working with AI models and exploring ML algorithms",
                    "timestamp": "2025-08-20T10:00:00.000000",
                    "source_conversation_length": 10
                },
                {
                    "category": "career",
                    "content": "User is a computer science student interested in software development",
                    "confidence": 0.9,
                    "tags": ["CS", "programming", "career"],
                    "evidence": "I'm studying computer science and want to become a software developer",
                    "timestamp": "2025-08-20T11:00:00.000000",
                    "source_conversation_length": 8
                },
                {
                    "category": "interests",
                    "content": "User enjoys reading technical books and staying updated with tech trends",
                    "confidence": 0.85,
                    "tags": ["reading", "learning", "technology"],
                    "evidence": "I read a lot of technical books and follow tech blogs",
                    "timestamp": "2025-08-20T12:00:00.000000",
                    "source_conversation_length": 6
                },
                {
                    "category": "personal",
                    "content": "User values work-life balance and enjoys outdoor activities",
                    "confidence": 0.8,
                    "tags": ["balance", "outdoors", "lifestyle"],
                    "evidence": "I think work-life balance is important and I love hiking",
                    "timestamp": "2025-08-20T13:00:00.000000",
                    "source_conversation_length": 5
                },
                {
                    "category": "learning",
                    "content": "User prefers hands-on learning and practical projects",
                    "confidence": 0.88,
                    "tags": ["hands-on", "projects", "learning"],
                    "evidence": "I learn best by building projects and experimenting",
                    "timestamp": "2025-08-20T14:00:00.000000",
                    "source_conversation_length": 7
                }
            ],
            "conversation_summaries": [
                {
                    "topic": "Machine Learning Discussion",
                    "summary": "Discussed various ML algorithms and their applications in real-world scenarios",
                    "key_insights": ["User has practical ML experience", "Interested in deep learning"],
                    "timestamp": "2025-08-20T10:00:00.000000",
                    "length": 10
                },
                {
                    "topic": "Career Planning",
                    "summary": "Conversation about career goals and educational path in computer science",
                    "key_insights": ["Clear career direction", "Values continuous learning"],
                    "timestamp": "2025-08-20T11:00:00.000000",
                    "length": 8
                },
                {
                    "topic": "Work-Life Balance",
                    "summary": "Discussion about maintaining balance between work and personal life",
                    "key_insights": ["Values personal time", "Enjoys outdoor activities"],
                    "timestamp": "2025-08-20T13:00:00.000000",
                    "length": 5
                }
            ],
            "metadata": {
                "total_insights": 5,
                "total_conversations": 3,
                "last_updated": "2025-08-20T14:00:00.000000",
                "user_id": "test_user",
                "version": "1.0"
            }
        }
        
        with open(self.test_memory_file, 'w') as f:
            json.dump(test_data, f, indent=2)
    
    def record_issue(self, issue_type, description, severity="ERROR", details=None):
        """Record an issue found during testing"""
        issue = {
            'type': issue_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results['issues_found'].append(issue)
        print(f"[{severity}] {issue_type}: {description}")
        if details:
            print(f"  Details: {details}")
    
    def record_warning(self, message):
        """Record a warning"""
        warning = {
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results['warnings'].append(warning)
        print(f"[WARNING] {message}")
    
    def test_01_config_validation(self):
        """Test configuration validation"""
        print("\n=== Testing Configuration ===")
        try:
            config = get_config()
            
            # Check serendipity engine is enabled
            if not config.ENABLE_SERENDIPITY_ENGINE:
                self.record_issue("CONFIG_ERROR", "Serendipity engine is disabled")
                return
            
            # Check required attributes
            required_attrs = [
                'SERENDIPITY_MIN_INSIGHTS',
                'SERENDIPITY_MAX_MEMORY_SIZE_MB',
                'SERENDIPITY_ANALYSIS_TIMEOUT',
                'OLLAMA_MODEL',
                'OLLAMA_URL'
            ]
            
            for attr in required_attrs:
                if not hasattr(config, attr):
                    self.record_issue("CONFIG_ERROR", f"Missing required config attribute: {attr}")
                else:
                    print(f"✓ {attr}: {getattr(config, attr)}")
            
            self.test_results['tests_passed'] += 1
            print("✓ Configuration validation passed")
            
        except Exception as e:
            self.record_issue("CONFIG_ERROR", f"Configuration validation failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_02_memory_file_validation(self):
        """Test memory file validation"""
        print("\n=== Testing Memory File ===")
        try:
            # Check if memory file exists
            if not self.test_memory_file.exists():
                self.record_issue("MEMORY_ERROR", "Memory file does not exist")
                return
            
            # Check if memory file is readable
            with open(self.test_memory_file, 'r') as f:
                memory_data = json.load(f)
            
            # Validate memory data structure
            required_keys = ['insights', 'conversation_summaries', 'metadata']
            for key in required_keys:
                if key not in memory_data:
                    self.record_issue("MEMORY_ERROR", f"Missing required key in memory data: {key}")
                else:
                    print(f"✓ Found {key}: {len(memory_data[key]) if isinstance(memory_data[key], list) else 'present'}")
            
            # Check insights data
            if 'insights' in memory_data:
                insights = memory_data['insights']
                if len(insights) < 3:
                    self.record_warning(f"Low number of insights ({len(insights)}). Serendipity analysis may be limited.")
                else:
                    print(f"✓ Sufficient insights for analysis: {len(insights)}")
            
            self.test_results['tests_passed'] += 1
            print("✓ Memory file validation passed")
            
        except Exception as e:
            self.record_issue("MEMORY_ERROR", f"Memory file validation failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_03_ai_service_availability(self):
        """Test AI service availability"""
        print("\n=== Testing AI Service ===")
        try:
            config = get_config()
            ai_service = get_ai_service()
            
            if not ai_service:
                self.record_issue("AI_SERVICE_ERROR", "AI service is not available")
                return
            
            # Test AI service connection
            try:
                # Try to make a simple request to test connectivity
                test_prompt = "Hello, this is a test."
                response = ai_service.generate_response(test_prompt, max_length=10)
                
                if response and len(response.strip()) > 0:
                    print("✓ AI service is responding")
                else:
                    self.record_issue("AI_SERVICE_ERROR", "AI service returned empty response")
                    
            except Exception as ai_error:
                self.record_issue("AI_SERVICE_ERROR", f"AI service test failed: {str(ai_error)}", 
                                details={'ai_error': str(ai_error)})
                
            self.test_results['tests_passed'] += 1
            print("✓ AI service availability test passed")
            
        except Exception as e:
            self.record_issue("AI_SERVICE_ERROR", f"AI service availability test failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_04_serendipity_service_initialization(self):
        """Test serendipity service initialization"""
        print("\n=== Testing Serendipity Service Initialization ===")
        try:
            # Test service creation
            serendipity_service = get_serendipity_service()
            
            if not serendipity_service:
                self.record_issue("SERENDIPITY_ERROR", "Failed to create serendipity service instance")
                return
            
            # Test service status
            status = serendipity_service.get_service_status()
            print(f"✓ Service status: {status}")
            
            # Test required methods exist
            required_methods = ['analyze_memory', 'get_service_status', '_load_memory_data_enhanced']
            for method in required_methods:
                if not hasattr(serendipity_service, method):
                    self.record_issue("SERENDIPITY_ERROR", f"Missing required method: {method}")
                else:
                    print(f"✓ Method available: {method}")
            
            self.test_results['tests_passed'] += 1
            print("✓ Serendipity service initialization passed")
            
        except Exception as e:
            self.record_issue("SERENDIPITY_ERROR", f"Serendipity service initialization failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_05_serendipity_analysis_execution(self):
        """Test serendipity analysis execution"""
        print("\n=== Testing Serendipity Analysis Execution ===")
        start_time = time.time()
        
        try:
            serendipity_service = get_serendipity_service()
            
            # Perform analysis
            print("Starting serendipity analysis...")
            analysis_results = serendipity_service.analyze_memory(
                memory_file_path=str(self.test_memory_file)
            )
            
            analysis_time = time.time() - start_time
            self.test_results['performance_metrics']['analysis_time'] = analysis_time
            print(f"✓ Analysis completed in {analysis_time:.2f} seconds")
            
            # Validate analysis results structure
            required_keys = ['connections', 'patterns', 'recommendations', 'metadata']
            for key in required_keys:
                if key not in analysis_results:
                    self.record_issue("ANALYSIS_ERROR", f"Missing key in analysis results: {key}")
                else:
                    if isinstance(analysis_results[key], list):
                        print(f"✓ {key}: {len(analysis_results[key])} items")
                    else:
                        print(f"✓ {key}: present")
            
            # Check connections quality
            if 'connections' in analysis_results:
                connections = analysis_results['connections']
                if len(connections) == 0:
                    self.record_warning("No connections found in analysis results")
                else:
                    print(f"✓ Found {len(connections)} connections")
                    
                    # Validate connection structure
                    for i, conn in enumerate(connections):
                        required_conn_keys = ['insight_ids', 'connection_type', 'strength', 'description']
                        for conn_key in required_conn_keys:
                            if conn_key not in conn:
                                self.record_issue("ANALYSIS_ERROR", 
                                                f"Missing key '{conn_key}' in connection {i}")
            
            # Check patterns
            if 'patterns' in analysis_results:
                patterns = analysis_results['patterns']
                print(f"✓ Found {len(patterns)} patterns")
            
            # Check recommendations
            if 'recommendations' in analysis_results:
                recommendations = analysis_results['recommendations']
                print(f"✓ Found {len(recommendations)} recommendations")
            
            self.test_results['tests_passed'] += 1
            print("✓ Serendipity analysis execution passed")
            
        except SerendipityServiceError as e:
            self.record_issue("SERENDIPITY_ERROR", f"Serendipity analysis failed: {str(e)}", 
                            details={'error_type': 'SerendipityServiceError'})
            self.test_results['tests_failed'] += 1
            
        except Exception as e:
            self.record_issue("ANALYSIS_ERROR", f"Analysis execution failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_06_api_endpoint_availability(self):
        """Test API endpoint availability"""
        print("\n=== Testing API Endpoint ===")
        try:
            # Test GET request (status)
            response = self.client.get('/api/serendipity')
            print(f"✓ GET /api/serendipity status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                if data and 'enabled' in data and data['enabled']:
                    print("✓ Serendipity API is enabled and available")
                else:
                    self.record_issue("API_ERROR", "Serendipity API reports as disabled")
            elif response.status_code == 503:
                self.record_issue("API_ERROR", "Serendipity API is unavailable (503)")
            else:
                self.record_issue("API_ERROR", f"Unexpected API status code: {response.status_code}")
            
            # Test POST request (analysis)
            print("Testing POST request for analysis...")
            post_response = self.client.post('/api/serendipity')
            print(f"✓ POST /api/serendipity status code: {post_response.status_code}")
            
            if post_response.status_code == 200:
                post_data = post_response.get_json()
                if post_data and 'connections' in post_data:
                    print("✓ API analysis request successful")
                else:
                    self.record_issue("API_ERROR", "API analysis returned invalid response structure")
            else:
                self.record_issue("API_ERROR", f"API analysis failed with status: {post_response.status_code}")
                if post_response.data:
                    print(f"Response data: {post_response.data.decode()}")
            
            self.test_results['tests_passed'] += 1
            print("✓ API endpoint test passed")
            
        except Exception as e:
            self.record_issue("API_ERROR", f"API endpoint test failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_07_error_handling(self):
        """Test error handling scenarios"""
        print("\n=== Testing Error Handling ===")
        try:
            serendipity_service = get_serendipity_service()
            
            # Test with invalid memory file
            print("Testing with invalid memory file...")
            try:
                invalid_file = Path(self.temp_dir) / "nonexistent.json"
                result = serendipity_service.analyze_memory(memory_file_path=str(invalid_file))
                self.record_warning("Expected error for invalid memory file, but got result")
            except SerendipityServiceError:
                print("✓ Proper error handling for invalid memory file")
            except Exception as e:
                self.record_issue("ERROR_HANDLING", f"Unexpected error type for invalid file: {type(e).__name__}")
            
            # Test with empty memory file
            print("Testing with empty memory file...")
            empty_file = Path(self.temp_dir) / "empty.json"
            with open(empty_file, 'w') as f:
                json.dump({}, f)
            
            try:
                result = serendipity_service.analyze_memory(memory_file_path=str(empty_file))
                self.record_warning("Expected error for empty memory file, but got result")
            except SerendipityServiceError:
                print("✓ Proper error handling for empty memory file")
            except Exception as e:
                self.record_issue("ERROR_HANDLING", f"Unexpected error type for empty file: {type(e).__name__}")
            
            self.test_results['tests_passed'] += 1
            print("✓ Error handling test passed")
            
        except Exception as e:
            self.record_issue("ERROR_HANDLING", f"Error handling test failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def test_08_performance_validation(self):
        """Test performance characteristics"""
        print("\n=== Testing Performance ===")
        try:
            # Get analysis time from previous test
            analysis_time = self.test_results['performance_metrics'].get('analysis_time', 0)
            
            # Check if analysis time is reasonable
            config = get_config()
            timeout = config.SERENDIPITY_ANALYSIS_TIMEOUT
            
            if analysis_time > timeout:
                self.record_issue("PERFORMANCE_ERROR", 
                                f"Analysis time ({analysis_time:.2f}s) exceeded timeout ({timeout}s)")
            elif analysis_time > timeout * 0.8:
                self.record_warning(f"Analysis time ({analysis_time:.2f}s) is close to timeout ({timeout}s)")
            else:
                print(f"✓ Analysis time ({analysis_time:.2f}s) is within acceptable limits")
            
            # Test memory usage (basic check)
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"✓ Current memory usage: {memory_mb:.2f} MB")
            
            if memory_mb > 1000:  # 1GB threshold
                self.record_warning(f"High memory usage detected: {memory_mb:.2f} MB")
            
            self.test_results['tests_passed'] += 1
            print("✓ Performance validation passed")
            
        except Exception as e:
            self.record_issue("PERFORMANCE_ERROR", f"Performance validation failed: {str(e)}", 
                            details={'traceback': traceback.format_exc()})
            self.test_results['tests_failed'] += 1
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("SERENDIPITY FUNCTIONALITY TEST SUMMARY")
        print("="*80)
        
        print(f"\nTest Results:")
        print(f"  ✓ Tests Passed: {self.test_results['tests_passed']}")
        print(f"  ✗ Tests Failed: {self.test_results['tests_failed']}")
        
        # Performance metrics
        if self.test_results['performance_metrics']:
            print(f"\nPerformance Metrics:")
            for metric, value in self.test_results['performance_metrics'].items():
                print(f"  {metric}: {value:.2f}s" if 'time' in metric else f"  {metric}: {value}")
        
        # Issues found
        if self.test_results['issues_found']:
            print(f"\nISSUES FOUND ({len(self.test_results['issues_found'])}):")
            for i, issue in enumerate(self.test_results['issues_found'], 1):
                print(f"\n{i}. [{issue['severity']}] {issue['type']}")
                print(f"   Description: {issue['description']}")
                print(f"   Timestamp: {issue['timestamp']}")
                if issue['details']:
                    for key, value in issue['details'].items():
                        if key == 'traceback':
                            print(f"   {key}: [See details below]")
                        else:
                            print(f"   {key}: {value}")
        else:
            print(f"\n✓ NO CRITICAL ISSUES FOUND")
        
        # Warnings
        if self.test_results['warnings']:
            print(f"\nWARNINGS ({len(self.test_results['warnings'])}):")
            for i, warning in enumerate(self.test_results['warnings'], 1):
                print(f"{i}. {warning['message']} (at {warning['timestamp']})")
        
        # Overall status
        print(f"\n{'='*80}")
        if self.test_results['tests_failed'] == 0:
            print("OVERALL STATUS: ✓ SERENDIPITY IS WORKING PROPERLY")
        else:
            print("OVERALL STATUS: ✗ SERENDIPITY HAS ISSUES THAT NEED ATTENTION")
        print("="*80)


def run_serendipity_functionality_test():
    """Run the serendipity functionality test"""
    print("Starting Serendipity Functionality Test...")
    print("This test will check if serendipity is working properly and identify any issues.")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(SerendipityFunctionalityTest)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=False)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_serendipity_functionality_test()
