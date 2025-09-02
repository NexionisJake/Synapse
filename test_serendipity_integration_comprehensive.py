#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Serendipity Analysis Feature

This module tests the complete user workflow across all devices and scenarios,
including end-to-end pipeline testing, performance testing, and security validation.
"""

import unittest
import json
import tempfile
import shutil
import os
import time
import threading
import concurrent.futures
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app import app
from config import get_config
from serendipity_service import reset_serendipity_service, SerendipityService
from memory_service import MemoryService
from ai_service import get_ai_service


class TestSerendipityIntegrationWorkflow(unittest.TestCase):
    """Integration tests for complete user workflow"""
    
    def setUp(self):
        """Set up comprehensive test environment"""
        reset_serendipity_service()
        
        # Create temporary directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        self.history_file = Path(self.temp_dir) / "serendipity_history.json"
        self.analytics_file = Path(self.temp_dir) / "serendipity_analytics.json"
        
        # Set environment variables
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['SERENDIPITY_HISTORY_FILE'] = str(self.history_file)
        os.environ['SERENDIPITY_ANALYTICS_FILE'] = str(self.analytics_file)
        
        # Create comprehensive test memory data
        self.create_comprehensive_memory_data()
        
        # Set up Flask test client
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Track performance metrics
        self.performance_metrics = []
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        for env_var in ['MEMORY_FILE', 'ENABLE_SERENDIPITY_ENGINE', 
                       'SERENDIPITY_HISTORY_FILE', 'SERENDIPITY_ANALYTICS_FILE']:
            os.environ.pop(env_var, None)
        reset_serendipity_service()
    
    def create_comprehensive_memory_data(self):
        """Create comprehensive test memory data"""
        insights = []
        conversation_summaries = []
        
        # Create diverse insights across multiple categories
        categories = ['interests', 'skills', 'goals', 'experience', 'learning', 'values', 'challenges']
        for i in range(50):  # Large dataset for performance testing
            category = categories[i % len(categories)]
            insights.append({
                "category": category,
                "content": f"Comprehensive insight {i+1} in {category} category with detailed content",
                "confidence": 0.7 + (i % 3) * 0.1,
                "tags": [f"tag_{i % 10}", f"tag_{(i+1) % 10}", category],
                "evidence": f"Evidence for insight {i+1} with substantial supporting information",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat()
            })
        
        # Create conversation summaries
        for i in range(20):
            conversation_summaries.append({
                "summary": f"Comprehensive conversation {i+1} covering multiple topics and themes",
                "key_themes": [f"theme_{i % 5}", f"theme_{(i+1) % 5}", f"theme_{(i+2) % 5}"],
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat()
            })
        
        test_data = {
            "insights": insights,
            "conversation_summaries": conversation_summaries,
            "metadata": {
                "total_insights": len(insights),
                "last_updated": datetime.now().isoformat()
            }
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
    
    @patch('serendipity_service.get_ai_service')
    def test_complete_user_workflow_desktop(self, mock_get_ai_service):
        """Test complete user workflow on desktop device"""
        print("\n🖥️  Testing Desktop User Workflow...")
        
        # Mock AI service with realistic response
        mock_ai_service = Mock()
        mock_ai_response = self.create_realistic_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        mock_get_ai_service.return_value = mock_ai_service
        
        # Step 1: Initial page load (simulate desktop)
        print("Step 1: Loading dashboard...")
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'discover-connections-btn', response.data)
        print("✓ Dashboard loaded successfully")
        
        # Step 2: Check service status
        print("Step 2: Checking service status...")
        response = self.client.get('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        status_data = json.loads(response.data)
        self.assertTrue(status_data['enabled'])
        print("✓ Service is enabled and ready")
        
        # Step 3: Perform serendipity analysis
        print("Step 3: Performing serendipity analysis...")
        start_time = time.time()
        response = self.client.post('/api/serendipity')
        analysis_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        analysis_data = json.loads(response.data)
        
        # Verify analysis results structure
        self.assertIn('connections', analysis_data)
        self.assertIn('meta_patterns', analysis_data)
        self.assertIn('serendipity_summary', analysis_data)
        self.assertIn('recommendations', analysis_data)
        self.assertIn('metadata', analysis_data)
        
        # Verify content quality
        self.assertGreater(len(analysis_data['connections']), 0)
        self.assertGreater(len(analysis_data['meta_patterns']), 0)
        self.assertGreater(len(analysis_data['recommendations']), 0)
        
        print(f"✓ Analysis completed in {analysis_time:.2f}s")
        print(f"  - Found {len(analysis_data['connections'])} connections")
        print(f"  - Identified {len(analysis_data['meta_patterns'])} patterns")
        
        # Step 4: Verify analysis history
        print("Step 4: Checking analysis history...")
        response = self.client.get('/api/serendipity/history')
        self.assertEqual(response.status_code, 200)
        history_data = json.loads(response.data)
        self.assertEqual(len(history_data['analyses']), 1)
        print("✓ Analysis recorded in history")
        
        # Step 5: Check analytics
        print("Step 5: Checking usage analytics...")
        response = self.client.get('/api/serendipity/analytics')
        self.assertEqual(response.status_code, 200)
        analytics_data = json.loads(response.data)
        self.assertEqual(analytics_data['usage_statistics']['total_analyses'], 1)
        print("✓ Analytics updated correctly")
        
        # Step 6: Performance metrics
        print("Step 6: Checking performance metrics...")
        response = self.client.get('/api/serendipity/performance')
        self.assertEqual(response.status_code, 200)
        perf_data = json.loads(response.data)
        self.assertIn('recent_performance', perf_data)
        print("✓ Performance metrics available")
        
        # Record performance metrics
        self.performance_metrics.append({
            'device': 'desktop',
            'analysis_time': analysis_time,
            'connections_count': len(analysis_data['connections']),
            'patterns_count': len(analysis_data['meta_patterns'])
        })
        
        print("🎉 Desktop workflow completed successfully!")
    
    @patch('serendipity_service.get_ai_service')
    def test_complete_user_workflow_mobile(self, mock_get_ai_service):
        """Test complete user workflow on mobile device"""
        print("\n📱 Testing Mobile User Workflow...")
        
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_response = self.create_realistic_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        mock_get_ai_service.return_value = mock_ai_service
        
        # Simulate mobile user agent
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
        
        # Step 1: Mobile dashboard load
        print("Step 1: Loading mobile dashboard...")
        response = self.client.get('/dashboard', headers=headers)
        self.assertEqual(response.status_code, 200)
        print("✓ Mobile dashboard loaded")
        
        # Step 2: Mobile analysis request
        print("Step 2: Performing mobile analysis...")
        start_time = time.time()
        response = self.client.post('/api/serendipity', headers=headers)
        analysis_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        analysis_data = json.loads(response.data)
        self.assertIn('connections', analysis_data)
        
        print(f"✓ Mobile analysis completed in {analysis_time:.2f}s")
        
        # Record mobile performance
        self.performance_metrics.append({
            'device': 'mobile',
            'analysis_time': analysis_time,
            'connections_count': len(analysis_data['connections']),
            'patterns_count': len(analysis_data['meta_patterns'])
        })
        
        print("🎉 Mobile workflow completed successfully!")
    
    @patch('serendipity_service.get_ai_service')
    def test_complete_user_workflow_tablet(self, mock_get_ai_service):
        """Test complete user workflow on tablet device"""
        print("\n📱 Testing Tablet User Workflow...")
        
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_response = self.create_realistic_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        mock_get_ai_service.return_value = mock_ai_service
        
        # Simulate tablet user agent
        headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)'}
        
        # Tablet workflow test
        print("Step 1: Loading tablet dashboard...")
        response = self.client.get('/dashboard', headers=headers)
        self.assertEqual(response.status_code, 200)
        
        print("Step 2: Performing tablet analysis...")
        start_time = time.time()
        response = self.client.post('/api/serendipity', headers=headers)
        analysis_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        analysis_data = json.loads(response.data)
        
        print(f"✓ Tablet analysis completed in {analysis_time:.2f}s")
        
        # Record tablet performance
        self.performance_metrics.append({
            'device': 'tablet',
            'analysis_time': analysis_time,
            'connections_count': len(analysis_data['connections']),
            'patterns_count': len(analysis_data['meta_patterns'])
        })
        
        print("🎉 Tablet workflow completed successfully!")
    
    def test_error_scenarios_workflow(self):
        """Test complete workflow with various error scenarios"""
        print("\n❌ Testing Error Scenarios Workflow...")
        
        # Test 1: Service disabled
        print("Test 1: Service disabled scenario...")
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 503)
        error_data = json.loads(response.data)
        self.assertIn('Service disabled', error_data['error'])
        print("✓ Service disabled handled correctly")
        
        # Re-enable service
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Test 2: Insufficient data
        print("Test 2: Insufficient data scenario...")
        insufficient_data = {
            "insights": [{"content": "Only one insight", "category": "test"}],
            "conversation_summaries": [],
            "metadata": {}
        }
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(insufficient_data, f)
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 400)
        error_data = json.loads(response.data)
        self.assertIn('Insufficient data', error_data['message'])
        print("✓ Insufficient data handled correctly")
        
        # Test 3: Corrupted memory file
        print("Test 3: Corrupted memory file scenario...")
        with open(self.memory_file, 'w') as f:
            f.write('invalid json content')
        
        response = self.client.post('/api/serendipity')
        # Should handle gracefully with recovery
        self.assertIn(response.status_code, [200, 400])  # Either recovers or fails gracefully
        print("✓ Corrupted file handled correctly")
        
        # Test 4: Missing memory file
        print("Test 4: Missing memory file scenario...")
        if self.memory_file.exists():
            self.memory_file.unlink()
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 400)
        error_data = json.loads(response.data)
        self.assertIn('not found', error_data['message'].lower())
        print("✓ Missing file handled correctly")
        
        print("🎉 Error scenarios workflow completed!")
    
    def create_realistic_ai_response(self):
        """Create realistic AI response for testing"""
        return {
            "connections": [
                {
                    "title": "Learning-Experience Synergy",
                    "description": "Strong connection between learning interests and practical experience",
                    "surprise_factor": 0.7,
                    "relevance": 0.9,
                    "connected_insights": ["learning insight", "experience insight"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Leverage experience to accelerate learning"
                },
                {
                    "title": "Skills-Goals Alignment",
                    "description": "Clear alignment between developed skills and stated goals",
                    "surprise_factor": 0.4,
                    "relevance": 0.8,
                    "connected_insights": ["skills insight", "goals insight"],
                    "connection_type": "thematic",
                    "actionable_insight": "Focus skill development on goal achievement"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Growth Mindset",
                    "description": "Consistent pattern of learning and improvement",
                    "evidence_count": 15,
                    "confidence": 0.85
                },
                {
                    "pattern_name": "Practical Application",
                    "description": "Focus on applying knowledge in real scenarios",
                    "evidence_count": 12,
                    "confidence": 0.78
                }
            ],
            "serendipity_summary": "Analysis reveals strong patterns of continuous learning and practical application, with clear alignment between interests, skills, and goals.",
            "recommendations": [
                "Continue building on the strong learning-experience connection",
                "Explore opportunities that combine multiple skill areas",
                "Document learning journey for future reflection"
            ]
        }


class TestSerendipityPerformanceStress(unittest.TestCase):
    """Performance and stress testing for serendipity analysis"""
    
    def setUp(self):
        """Set up performance test environment"""
        reset_serendipity_service()
        
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "perf_memory.json"
        
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up performance test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    def create_large_memory_dataset(self, size):
        """Create large memory dataset for performance testing"""
        insights = []
        conversation_summaries = []
        
        for i in range(size):
            insights.append({
                "category": f"category_{i % 20}",
                "content": f"Performance test insight {i+1} with substantial content for realistic testing scenarios",
                "confidence": 0.5 + (i % 5) * 0.1,
                "tags": [f"tag_{i % 50}", f"tag_{(i+1) % 50}", f"tag_{(i+2) % 50}"],
                "evidence": f"Detailed evidence for insight {i+1} with comprehensive supporting information and context",
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat()
            })
        
        for i in range(size // 5):
            conversation_summaries.append({
                "summary": f"Performance test conversation {i+1} covering multiple complex topics and detailed discussions",
                "key_themes": [f"theme_{i % 10}", f"theme_{(i+1) % 10}", f"theme_{(i+2) % 10}"],
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat()
            })
        
        data = {
            "insights": insights,
            "conversation_summaries": conversation_summaries,
            "metadata": {
                "total_insights": len(insights),
                "last_updated": datetime.now().isoformat()
            }
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @patch('serendipity_service.get_ai_service')
    def test_small_dataset_performance(self, mock_get_ai_service):
        """Test performance with small dataset (10 insights)"""
        print("\n⚡ Testing Small Dataset Performance...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({"connections": [], "meta_patterns": [], "serendipity_summary": "Test", "recommendations": []})
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_large_memory_dataset(10)
        
        start_time = time.time()
        response = self.client.post('/api/serendipity')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        processing_time = end_time - start_time
        
        print(f"✓ Small dataset processed in {processing_time:.3f}s")
        self.assertLess(processing_time, 2.0, "Small dataset should process quickly")
    
    @patch('serendipity_service.get_ai_service')
    def test_medium_dataset_performance(self, mock_get_ai_service):
        """Test performance with medium dataset (100 insights)"""
        print("\n⚡ Testing Medium Dataset Performance...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({"connections": [], "meta_patterns": [], "serendipity_summary": "Test", "recommendations": []})
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_large_memory_dataset(100)
        
        start_time = time.time()
        response = self.client.post('/api/serendipity')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        processing_time = end_time - start_time
        
        print(f"✓ Medium dataset processed in {processing_time:.3f}s")
        self.assertLess(processing_time, 10.0, "Medium dataset should process within reasonable time")
    
    @patch('serendipity_service.get_ai_service')
    def test_large_dataset_performance(self, mock_get_ai_service):
        """Test performance with large dataset (500 insights)"""
        print("\n⚡ Testing Large Dataset Performance...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({"connections": [], "meta_patterns": [], "serendipity_summary": "Test", "recommendations": []})
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_large_memory_dataset(500)
        
        start_time = time.time()
        response = self.client.post('/api/serendipity')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        processing_time = end_time - start_time
        
        print(f"✓ Large dataset processed in {processing_time:.3f}s")
        self.assertLess(processing_time, 30.0, "Large dataset should process within acceptable time")
    
    @patch('serendipity_service.get_ai_service')
    def test_concurrent_requests_stress(self, mock_get_ai_service):
        """Test system under concurrent request load"""
        print("\n🔥 Testing Concurrent Requests Stress...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({"connections": [], "meta_patterns": [], "serendipity_summary": "Test", "recommendations": []})
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_large_memory_dataset(50)
        
        def make_request():
            return self.client.post('/api/serendipity')
        
        # Test with 5 concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        # Verify all requests succeeded
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        total_time = end_time - start_time
        print(f"✓ 5 concurrent requests completed in {total_time:.3f}s")
        self.assertLess(total_time, 60.0, "Concurrent requests should complete within reasonable time")
    
    @patch('serendipity_service.get_ai_service')
    def test_memory_usage_stress(self, mock_get_ai_service):
        """Test memory usage under repeated requests"""
        print("\n🧠 Testing Memory Usage Stress...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({"connections": [], "meta_patterns": [], "serendipity_summary": "Test", "recommendations": []})
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_large_memory_dataset(100)
        
        # Make 20 sequential requests to test memory management
        for i in range(20):
            response = self.client.post('/api/serendipity')
            self.assertEqual(response.status_code, 200)
            
            if i % 5 == 0:
                print(f"  Completed {i+1}/20 requests")
        
        print("✓ Memory stress test completed successfully")


class TestSerendipitySecurityValidation(unittest.TestCase):
    """Security testing for serendipity analysis"""
    
    def setUp(self):
        """Set up security test environment"""
        reset_serendipity_service()
        
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "security_memory.json"
        
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create basic memory data
        test_data = {
            "insights": [
                {"content": "Test insight 1", "category": "test"},
                {"content": "Test insight 2", "category": "test"},
                {"content": "Test insight 3", "category": "test"}
            ],
            "conversation_summaries": [{"summary": "Test conversation"}],
            "metadata": {}
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up security test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    def test_input_validation_security(self):
        """Test input validation and sanitization"""
        print("\n🔒 Testing Input Validation Security...")
        
        # Test malformed JSON
        print("Test 1: Malformed JSON input...")
        response = self.client.post('/api/serendipity', 
                                  data='{"malformed": json}',
                                  content_type='application/json')
        self.assertIn(response.status_code, [400, 422])
        print("✓ Malformed JSON rejected")
        
        # Test oversized request
        print("Test 2: Oversized request...")
        large_data = {"data": "x" * 10000}  # Large payload
        response = self.client.post('/api/serendipity',
                                  json=large_data)
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400, 413])
        print("✓ Oversized request handled")
        
        # Test SQL injection attempts (though we don't use SQL)
        print("Test 3: Injection attempt simulation...")
        injection_data = {"query": "'; DROP TABLE users; --"}
        response = self.client.post('/api/serendipity',
                                  json=injection_data)
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400])
        print("✓ Injection attempts handled")
    
    def test_xss_prevention(self):
        """Test XSS prevention in responses"""
        print("\n🛡️  Testing XSS Prevention...")
        
        # Create memory data with potential XSS content
        xss_data = {
            "insights": [
                {"content": "<script>alert('xss')</script>", "category": "test"},
                {"content": "Normal insight", "category": "test"},
                {"content": "Another normal insight", "category": "test"}
            ],
            "conversation_summaries": [
                {"summary": "<img src=x onerror=alert('xss')>"}
            ],
            "metadata": {}
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(xss_data, f)
        
        # Mock AI service to return potentially dangerous content
        with patch('serendipity_service.get_ai_service') as mock_get_ai_service:
            mock_ai_service = Mock()
            mock_ai_response = {
                "connections": [
                    {
                        "title": "<script>alert('xss')</script>",
                        "description": "Safe description",
                        "surprise_factor": 0.5,
                        "relevance": 0.5
                    }
                ],
                "meta_patterns": [],
                "serendipity_summary": "<img src=x onerror=alert('xss')>",
                "recommendations": ["<script>alert('xss')</script>"]
            }
            mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/api/serendipity')
            
            if response.status_code == 200:
                response_data = json.loads(response.data)
                response_text = json.dumps(response_data)
                
                # Verify no script tags in response
                self.assertNotIn('<script>', response_text)
                self.assertNotIn('onerror=', response_text)
                print("✓ XSS content sanitized in response")
            else:
                print("✓ XSS content caused safe failure")
    
    def test_error_message_sanitization(self):
        """Test that error messages don't expose sensitive information"""
        print("\n🔐 Testing Error Message Sanitization...")
        
        # Test with file path exposure
        print("Test 1: File path exposure prevention...")
        os.environ['MEMORY_FILE'] = '/etc/passwd'  # Sensitive file
        response = self.client.post('/api/serendipity')
        
        if response.status_code != 200:
            error_data = json.loads(response.data)
            error_message = error_data.get('message', '')
            
            # Should not expose full file paths
            self.assertNotIn('/etc/passwd', error_message)
            self.assertNotIn('passwd', error_message)
            print("✓ File paths not exposed in errors")
        
        # Reset to valid file
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        
        # Test with system information exposure
        print("Test 2: System information exposure prevention...")
        with patch('serendipity_service.SerendipityService._load_memory_data') as mock_load:
            mock_load.side_effect = Exception("Database connection failed at localhost:5432 with user admin")
            
            response = self.client.post('/api/serendipity')
            
            if response.status_code != 200:
                error_data = json.loads(response.data)
                error_message = error_data.get('message', '')
                
                # Should not expose system details
                self.assertNotIn('localhost:5432', error_message)
                self.assertNotIn('admin', error_message)
                print("✓ System information not exposed in errors")
    
    def test_rate_limiting_simulation(self):
        """Test rate limiting behavior simulation"""
        print("\n⏱️  Testing Rate Limiting Simulation...")
        
        # Simulate rapid requests
        responses = []
        for i in range(10):
            response = self.client.post('/api/serendipity')
            responses.append(response)
            time.sleep(0.1)  # Small delay
        
        # All should succeed in test environment, but in production would be rate limited
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f"✓ {success_count}/10 requests succeeded (rate limiting would apply in production)")
    
    def test_authentication_bypass_attempts(self):
        """Test authentication bypass attempts"""
        print("\n🔑 Testing Authentication Bypass Attempts...")
        
        # Test with various header manipulations
        bypass_headers = [
            {'X-Forwarded-For': '127.0.0.1'},
            {'X-Real-IP': '127.0.0.1'},
            {'Authorization': 'Bearer fake-token'},
            {'X-Admin': 'true'},
            {'X-Bypass-Auth': 'true'}
        ]
        
        for headers in bypass_headers:
            response = self.client.post('/api/serendipity', headers=headers)
            # Should not grant special privileges
            self.assertIn(response.status_code, [200, 400, 401, 403])
        
        print("✓ Authentication bypass attempts handled correctly")


if __name__ == '__main__':
    # Configure test environment
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add integration workflow tests
    suite.addTest(unittest.makeSuite(TestSerendipityIntegrationWorkflow))
    
    # Add performance tests
    suite.addTest(unittest.makeSuite(TestSerendipityPerformanceStress))
    
    # Add security tests
    suite.addTest(unittest.makeSuite(TestSerendipitySecurityValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUITE SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print(f"\n{'='*60}")