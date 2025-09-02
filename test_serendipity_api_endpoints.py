#!/usr/bin/env python3
"""
Test suite for serendipity API endpoints including metadata and analytics.

This module tests the new API endpoints for accessing serendipity analysis
history, usage analytics, performance metrics, and cache management.
"""

import unittest
import json
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch

from app import app
from config import get_config
from serendipity_service import reset_serendipity_service


class TestSerendipityAPIEndpoints(unittest.TestCase):
    """Test serendipity API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Reset service
        reset_serendipity_service()
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        self.history_file = Path(self.temp_dir) / "serendipity_history.json"
        self.analytics_file = Path(self.temp_dir) / "serendipity_analytics.json"
        
        # Set environment variables
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create test memory data
        test_data = {
            "insights": [
                {"content": "Test insight 1", "category": "test"},
                {"content": "Test insight 2", "category": "test"}
            ],
            "conversation_summaries": [
                {"summary": "Test conversation"}
            ],
            "metadata": {}
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Create test history data
        test_history = {
            "analyses": [
                {
                    "analysis_id": "test_analysis_1",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "summary": {
                        "connections_count": 2,
                        "patterns_count": 1,
                        "analysis_duration": 1.5
                    },
                    "context": {
                        "model_used": "llama3:8b"
                    }
                }
            ],
            "metadata": {
                "total_analyses": 1,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(test_history, f)
        
        # Create test analytics data
        test_analytics = {
            "usage_statistics": {
                "total_analyses": 5,
                "total_connections_discovered": 12,
                "total_patterns_identified": 3
            },
            "daily_usage": {
                "2024-01-15": {
                    "analyses_count": 2,
                    "connections_discovered": 5
                }
            },
            "performance_trends": {
                "analysis_durations": [1.2, 1.5, 0.8],
                "items_per_second": [3.2, 2.8, 4.1]
            },
            "model_usage": {
                "llama3:8b": 5
            },
            "metadata": {
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
        
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(test_analytics, f)
        
        # Set up Flask test client
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    def test_serendipity_history_endpoint(self):
        """Test /api/serendipity/history endpoint"""
        # Test successful history retrieval
        response = self.client.get('/api/serendipity/history')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('analyses', data)
        self.assertIn('metadata', data)
        self.assertEqual(len(data['analyses']), 1)
        self.assertEqual(data['analyses'][0]['analysis_id'], 'test_analysis_1')
        
        # Test with limit parameter
        response = self.client.get('/api/serendipity/history?limit=0')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['analyses']), 0)
        
        # Test with invalid limit (should still work)
        response = self.client.get('/api/serendipity/history?limit=invalid')
        self.assertEqual(response.status_code, 200)
    
    def test_serendipity_analytics_endpoint(self):
        """Test /api/serendipity/analytics endpoint"""
        # Test successful analytics retrieval
        response = self.client.get('/api/serendipity/analytics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('usage_statistics', data)
        self.assertIn('daily_usage', data)
        self.assertIn('performance_trends', data)
        self.assertIn('model_usage', data)
        
        # Verify usage statistics
        usage_stats = data['usage_statistics']
        self.assertEqual(usage_stats['total_analyses'], 5)
        self.assertEqual(usage_stats['total_connections_discovered'], 12)
        
        # Verify model usage
        self.assertIn('llama3:8b', data['model_usage'])
        self.assertEqual(data['model_usage']['llama3:8b'], 5)
    
    @patch('serendipity_service.get_ai_service')
    def test_serendipity_performance_endpoint(self, mock_get_ai_service):
        """Test /api/serendipity/performance endpoint"""
        # Mock AI service
        mock_ai_service = Mock()
        mock_get_ai_service.return_value = mock_ai_service
        
        # Test successful performance metrics retrieval
        response = self.client.get('/api/serendipity/performance')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('recent_performance', data)
        self.assertIn('cache_performance', data)
        self.assertIn('service_status', data)
        self.assertIn('timestamp', data)
        
        # Verify cache performance structure
        cache_perf = data['cache_performance']
        self.assertIn('memory_cache', cache_perf)
        self.assertIn('analysis_cache', cache_perf)
        self.assertIn('formatted_cache', cache_perf)
        
        # Verify service status
        service_status = data['service_status']
        self.assertIn('enabled', service_status)
        self.assertIn('model', service_status)
    
    @patch('serendipity_service.get_ai_service')
    def test_serendipity_cache_clear_endpoint(self, mock_get_ai_service):
        """Test /api/serendipity/cache DELETE endpoint"""
        # Mock AI service
        mock_ai_service = Mock()
        mock_get_ai_service.return_value = mock_ai_service
        
        # Test clearing all caches
        response = self.client.delete('/api/serendipity/cache')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('cleared_counts', data)
        self.assertIn('cache_type', data)
        self.assertEqual(data['cache_type'], 'all')
        
        # Test clearing specific cache type
        response = self.client.delete('/api/serendipity/cache?type=memory')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['cache_type'], 'memory')
        
        # Test invalid cache type
        response = self.client.delete('/api/serendipity/cache?type=invalid')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Cache type must be one of', data['message'])
    
    def test_endpoints_when_service_disabled(self):
        """Test all endpoints when serendipity service is disabled"""
        # Disable serendipity engine
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        endpoints = [
            '/api/serendipity/history',
            '/api/serendipity/analytics',
            '/api/serendipity/performance'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 503)
            
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('Service disabled', data['error'])
        
        # Test cache clear endpoint when disabled
        response = self.client.delete('/api/serendipity/cache')
        self.assertEqual(response.status_code, 503)
    
    def test_error_handling(self):
        """Test error handling in endpoints"""
        # Remove history file to trigger error
        if self.history_file.exists():
            self.history_file.unlink()
        
        # Create invalid JSON in analytics file
        with open(self.analytics_file, 'w') as f:
            f.write('invalid json')
        
        # Test history endpoint with missing file (should still work with defaults)
        response = self.client.get('/api/serendipity/history')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('analyses', data)
        self.assertEqual(len(data['analyses']), 0)  # Should return empty history
        
        # Test analytics endpoint with invalid JSON (should return default structure)
        response = self.client.get('/api/serendipity/analytics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('usage_statistics', data)
        # Should have default values
        self.assertEqual(data['usage_statistics']['total_analyses'], 0)
    
    def test_content_type_and_headers(self):
        """Test response content types and headers"""
        endpoints = [
            '/api/serendipity/history',
            '/api/serendipity/analytics',
            '/api/serendipity/performance'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.content_type, 'application/json')
            
            # Verify JSON is valid
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
    
    def test_endpoint_methods(self):
        """Test that endpoints only accept correct HTTP methods"""
        # History endpoint should only accept GET
        response = self.client.post('/api/serendipity/history')
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        response = self.client.delete('/api/serendipity/history')
        self.assertEqual(response.status_code, 405)
        
        # Analytics endpoint should only accept GET
        response = self.client.post('/api/serendipity/analytics')
        self.assertEqual(response.status_code, 405)
        
        # Performance endpoint should only accept GET
        response = self.client.post('/api/serendipity/performance')
        self.assertEqual(response.status_code, 405)
        
        # Cache endpoint should only accept DELETE
        response = self.client.get('/api/serendipity/cache')
        self.assertEqual(response.status_code, 405)
        
        response = self.client.post('/api/serendipity/cache')
        self.assertEqual(response.status_code, 405)


class TestSerendipityAPIIntegration(unittest.TestCase):
    """Integration tests for serendipity API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        reset_serendipity_service()
        
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create test memory data
        test_data = {
            "insights": [
                {"content": "AI transforms healthcare", "category": "technology"},
                {"content": "Leadership requires empathy", "category": "leadership"}
            ],
            "conversation_summaries": [
                {"summary": "Discussion about AI in healthcare"}
            ],
            "metadata": {}
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    @patch('serendipity_service.get_ai_service')
    def test_full_workflow_with_api_endpoints(self, mock_get_ai_service):
        """Test full workflow: analysis -> history -> analytics -> performance"""
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_response = json.dumps({
            "connections": [
                {
                    "title": "AI and Healthcare",
                    "description": "Connection between AI and healthcare",
                    "surprise_factor": 0.8,
                    "relevance": 0.9,
                    "connection_type": "cross_domain",
                    "actionable_insight": "Explore AI healthcare apps"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Innovation Theme",
                    "description": "Focus on innovation",
                    "evidence_count": 2,
                    "confidence": 0.8
                }
            ],
            "serendipity_summary": "Strong innovation patterns found",
            "recommendations": ["Explore AI applications"]
        })
        
        mock_ai_service.chat.return_value = mock_ai_response
        mock_get_ai_service.return_value = mock_ai_service
        
        # Step 1: Perform analysis
        print("Step 1: Performing serendipity analysis...")
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        
        analysis_data = json.loads(response.data)
        self.assertIn('connections', analysis_data)
        self.assertIn('metadata', analysis_data)
        
        analysis_id = analysis_data['metadata']['analysis_id']
        print(f"✓ Analysis completed with ID: {analysis_id}")
        
        # Step 2: Check history
        print("Step 2: Checking analysis history...")
        response = self.client.get('/api/serendipity/history')
        self.assertEqual(response.status_code, 200)
        
        history_data = json.loads(response.data)
        self.assertEqual(len(history_data['analyses']), 1)
        self.assertEqual(history_data['analyses'][0]['analysis_id'], analysis_id)
        print("✓ History contains the analysis")
        
        # Step 3: Check analytics
        print("Step 3: Checking usage analytics...")
        response = self.client.get('/api/serendipity/analytics')
        self.assertEqual(response.status_code, 200)
        
        analytics_data = json.loads(response.data)
        self.assertEqual(analytics_data['usage_statistics']['total_analyses'], 1)
        self.assertEqual(analytics_data['usage_statistics']['total_connections_discovered'], 1)
        print("✓ Analytics show correct usage statistics")
        
        # Step 4: Check performance metrics
        print("Step 4: Checking performance metrics...")
        response = self.client.get('/api/serendipity/performance')
        self.assertEqual(response.status_code, 200)
        
        performance_data = json.loads(response.data)
        self.assertIn('recent_performance', performance_data)
        self.assertGreater(performance_data['recent_performance']['average_duration'], 0)
        print("✓ Performance metrics available")
        
        # Step 5: Clear cache
        print("Step 5: Clearing cache...")
        response = self.client.delete('/api/serendipity/cache?type=all')
        self.assertEqual(response.status_code, 200)
        
        cache_data = json.loads(response.data)
        self.assertIn('cleared_counts', cache_data)
        print("✓ Cache cleared successfully")
        
        print("\n🎉 Full API workflow test passed!")


if __name__ == '__main__':
    unittest.main(verbosity=2)