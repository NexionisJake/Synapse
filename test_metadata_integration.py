#!/usr/bin/env python3
"""
Integration test for serendipity metadata and performance tracking.
This test verifies the complete workflow without requiring Ollama.
"""

import unittest
import json
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from serendipity_service import SerendipityService, reset_serendipity_service
from config import get_config


class TestMetadataIntegration(unittest.TestCase):
    """Integration test for metadata tracking"""
    
    def setUp(self):
        """Set up test environment"""
        reset_serendipity_service()
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        
        # Set environment variables
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create test memory data
        test_data = {
            "insights": [
                {
                    "content": "AI is transforming healthcare through predictive analytics",
                    "category": "technology",
                    "confidence": 0.9,
                    "tags": ["AI", "healthcare", "analytics"],
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "content": "Effective leadership requires emotional intelligence",
                    "category": "leadership",
                    "confidence": 0.8,
                    "tags": ["leadership", "emotional intelligence"],
                    "timestamp": "2024-01-16T14:20:00Z"
                },
                {
                    "content": "Sustainable business practices drive long-term success",
                    "category": "business",
                    "confidence": 0.85,
                    "tags": ["sustainability", "business"],
                    "timestamp": "2024-01-17T09:15:00Z"
                }
            ],
            "conversation_summaries": [
                {
                    "summary": "Discussion about AI applications in healthcare",
                    "key_themes": ["AI", "healthcare"],
                    "timestamp": "2024-01-15T16:00:00Z"
                },
                {
                    "summary": "Conversation about leadership development",
                    "key_themes": ["leadership", "development"],
                    "timestamp": "2024-01-16T11:30:00Z"
                }
            ],
            "metadata": {
                "total_insights": 3,
                "last_updated": "2024-01-17T09:15:00Z"
            }
        }
        
        # Save test data
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Get config (service will be created in test method)
        self.config = get_config()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    @patch('serendipity_service.get_ai_service')
    @patch('ai_service.get_ai_service')
    def test_complete_metadata_workflow(self, mock_ai_service_module, mock_get_ai_service):
        """Test complete metadata tracking workflow"""
        # Mock AI service response
        mock_ai_service = Mock()
        
        # Set up mocks before creating service
        mock_get_ai_service.return_value = mock_ai_service
        mock_ai_service_module.return_value = mock_ai_service
        
        # Now create the service with mocked AI service
        self.service = SerendipityService(config=self.config)
        mock_ai_response = json.dumps({
            "connections": [
                {
                    "title": "AI and Healthcare Innovation",
                    "description": "Connection between AI technology and healthcare applications",
                    "surprise_factor": 0.8,
                    "relevance": 0.9,
                    "connected_insights": ["AI insight", "Healthcare insight"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Explore AI healthcare applications"
                },
                {
                    "title": "Leadership and Business Success",
                    "description": "Link between leadership skills and business outcomes",
                    "surprise_factor": 0.6,
                    "relevance": 0.8,
                    "connected_insights": ["Leadership insight", "Business insight"],
                    "connection_type": "thematic",
                    "actionable_insight": "Develop leadership skills for business growth"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Innovation and Growth",
                    "description": "Recurring theme of innovation driving growth",
                    "evidence_count": 3,
                    "confidence": 0.85
                }
            ],
            "serendipity_summary": "Analysis reveals strong patterns connecting innovation, leadership, and sustainable growth across different domains.",
            "recommendations": [
                "Explore AI applications in your field",
                "Develop leadership skills for better outcomes",
                "Focus on sustainable practices for long-term success"
            ]
        })
        
        mock_ai_service.chat.return_value = mock_ai_response
        
        # Perform analysis
        print("Performing serendipity analysis...")
        results = self.service.analyze_memory()
        
        # Verify basic results structure
        self.assertIn("connections", results)
        self.assertIn("meta_patterns", results)
        self.assertIn("metadata", results)
        
        print(f"✓ Analysis completed with {len(results['connections'])} connections")
        
        # Verify comprehensive metadata
        metadata = results["metadata"]
        required_metadata_keys = [
            "analysis_id", "analysis_timestamp", "model_used", "service_version",
            "analysis_duration", "memory_statistics", "processing_metadata",
            "results_metadata", "performance_metrics", "system_context", "configuration"
        ]
        
        for key in required_metadata_keys:
            self.assertIn(key, metadata, f"Missing metadata key: {key}")
        
        print("✓ Comprehensive metadata generated")
        
        # Verify memory statistics
        memory_stats = metadata["memory_statistics"]
        self.assertEqual(memory_stats["insights_analyzed"], 3)
        self.assertEqual(memory_stats["conversations_analyzed"], 2)
        self.assertEqual(memory_stats["total_items_analyzed"], 5)
        
        # Verify categories were extracted
        categories = memory_stats["memory_categories"]
        self.assertIn("technology", categories)
        self.assertIn("leadership", categories)
        self.assertIn("business", categories)
        
        print("✓ Memory statistics calculated correctly")
        
        # Verify results metadata
        results_meta = metadata["results_metadata"]
        self.assertEqual(results_meta["connections_discovered"], 2)
        self.assertEqual(results_meta["meta_patterns_identified"], 1)
        self.assertEqual(results_meta["recommendations_generated"], 3)
        
        # Verify connection type analysis
        conn_types = results_meta["connection_types"]
        self.assertEqual(conn_types["cross_domain"], 1)
        self.assertEqual(conn_types["thematic"], 1)
        
        print("✓ Results metadata analyzed correctly")
        
        # Verify performance metrics
        perf_metrics = metadata["performance_metrics"]
        self.assertIn("analysis_speed", perf_metrics)
        self.assertIn("efficiency_metrics", perf_metrics)
        self.assertIn("resource_usage", perf_metrics)
        
        # Check that performance calculations are reasonable
        analysis_speed = perf_metrics["analysis_speed"]
        self.assertGreater(analysis_speed["items_per_second"], 0)
        self.assertGreater(analysis_speed["connections_per_second"], 0)
        
        print("✓ Performance metrics calculated")
        
        # Verify history was stored
        history_file = Path(self.temp_dir) / "serendipity_history.json"
        self.assertTrue(history_file.exists(), "History file should be created")
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        self.assertIn("analyses", history)
        self.assertEqual(len(history["analyses"]), 1)
        
        history_entry = history["analyses"][0]
        self.assertEqual(history_entry["analysis_id"], metadata["analysis_id"])
        self.assertIn("summary", history_entry)
        self.assertIn("performance_snapshot", history_entry)
        self.assertIn("results_preview", history_entry)
        
        print("✓ Analysis history stored")
        
        # Verify analytics were tracked
        analytics_file = Path(self.temp_dir) / "serendipity_analytics.json"
        self.assertTrue(analytics_file.exists(), "Analytics file should be created")
        
        with open(analytics_file, 'r', encoding='utf-8') as f:
            analytics = json.load(f)
        
        # Verify analytics structure
        required_analytics_keys = [
            "usage_statistics", "daily_usage", "performance_trends",
            "model_usage", "connection_type_distribution", "metadata"
        ]
        
        for key in required_analytics_keys:
            self.assertIn(key, analytics, f"Missing analytics key: {key}")
        
        # Verify usage statistics
        usage_stats = analytics["usage_statistics"]
        self.assertEqual(usage_stats["total_analyses"], 1)
        self.assertEqual(usage_stats["total_connections_discovered"], 2)
        self.assertEqual(usage_stats["total_patterns_identified"], 1)
        
        # Verify daily usage tracking
        today = datetime.now().date().isoformat()
        self.assertIn(today, analytics["daily_usage"])
        daily_stats = analytics["daily_usage"][today]
        self.assertEqual(daily_stats["analyses_count"], 1)
        self.assertEqual(daily_stats["connections_discovered"], 2)
        
        # Verify performance trends
        perf_trends = analytics["performance_trends"]
        self.assertEqual(len(perf_trends["analysis_durations"]), 1)
        self.assertEqual(len(perf_trends["items_per_second"]), 1)
        
        # Verify model usage tracking
        self.assertIn("llama3:8b", analytics["model_usage"])
        self.assertEqual(analytics["model_usage"]["llama3:8b"], 1)
        
        # Verify connection type distribution
        conn_dist = analytics["connection_type_distribution"]
        self.assertEqual(conn_dist["cross_domain"], 1)
        self.assertEqual(conn_dist["thematic"], 1)
        
        print("✓ Usage analytics tracked")
        
        # Test retrieval methods
        retrieved_history = self.service.get_analysis_history()
        self.assertEqual(len(retrieved_history["analyses"]), 1)
        
        retrieved_analytics = self.service.get_usage_analytics()
        self.assertEqual(retrieved_analytics["usage_statistics"]["total_analyses"], 1)
        
        performance_metrics = self.service.get_performance_metrics()
        self.assertIn("recent_performance", performance_metrics)
        self.assertIn("cache_performance", performance_metrics)
        
        print("✓ Data retrieval methods work")
        
        print("\n🎉 Complete metadata workflow test passed!")
        print(f"   Analysis ID: {metadata['analysis_id']}")
        print(f"   Duration: {metadata['analysis_duration']}s")
        print(f"   Connections: {len(results['connections'])}")
        print(f"   Patterns: {len(results['meta_patterns'])}")
        print(f"   History entries: {len(retrieved_history['analyses'])}")
        print(f"   Total analyses tracked: {retrieved_analytics['usage_statistics']['total_analyses']}")


if __name__ == '__main__':
    unittest.main(verbosity=2)