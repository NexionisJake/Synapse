#!/usr/bin/env python3
"""
Test suite for serendipity analysis metadata and performance tracking functionality.

This module tests the comprehensive metadata generation, analysis history storage,
and usage analytics tracking features of the serendipity service.
"""

import unittest
import json
import tempfile
import shutil
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serendipity_service import SerendipityService, get_serendipity_service, reset_serendipity_service
from config import get_config


class TestSerendipityMetadataTracking(unittest.TestCase):
    """Test metadata generation and tracking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Reset global service instance
        reset_serendipity_service()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        self.history_file = Path(self.temp_dir) / "serendipity_history.json"
        self.analytics_file = Path(self.temp_dir) / "serendipity_analytics.json"
        
        # Create test configuration using environment variables
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        self.config = get_config()
        
        # Create test memory data
        self.test_memory_data = {
            "insights": [
                {
                    "content": "Machine learning is transforming how we approach data analysis",
                    "category": "technology",
                    "confidence": 0.9,
                    "tags": ["AI", "data", "analysis"],
                    "evidence": "Multiple successful implementations",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "content": "Effective communication requires active listening and empathy",
                    "category": "communication",
                    "confidence": 0.8,
                    "tags": ["listening", "empathy", "skills"],
                    "evidence": "Research on interpersonal effectiveness",
                    "timestamp": "2024-01-16T14:20:00Z"
                },
                {
                    "content": "Sustainable practices are essential for long-term business success",
                    "category": "business",
                    "confidence": 0.85,
                    "tags": ["sustainability", "business", "strategy"],
                    "evidence": "Case studies from leading companies",
                    "timestamp": "2024-01-17T09:15:00Z"
                }
            ],
            "conversation_summaries": [
                {
                    "summary": "Discussion about AI applications in healthcare and their potential impact",
                    "key_themes": ["AI", "healthcare", "innovation"],
                    "timestamp": "2024-01-15T16:00:00Z",
                    "insights_count": 2
                },
                {
                    "summary": "Conversation about team dynamics and leadership styles",
                    "key_themes": ["leadership", "teamwork", "management"],
                    "timestamp": "2024-01-16T11:30:00Z",
                    "insights_count": 1
                }
            ],
            "metadata": {
                "total_insights": 3,
                "last_updated": "2024-01-17T09:15:00Z",
                "version": "1.0"
            }
        }
        
        # Save test memory data
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_memory_data, f, indent=2)
        
        # Create serendipity service
        self.service = SerendipityService(config=self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up environment variables
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    def test_generate_analysis_metadata(self):
        """Test comprehensive metadata generation"""
        # Mock analysis results
        mock_analysis_results = {
            "connections": [
                {
                    "title": "AI and Healthcare Innovation",
                    "description": "Connection between AI technology and healthcare applications",
                    "surprise_factor": 0.7,
                    "relevance": 0.9,
                    "connection_type": "cross_domain"
                },
                {
                    "title": "Leadership and Communication",
                    "description": "Link between effective leadership and communication skills",
                    "surprise_factor": 0.5,
                    "relevance": 0.8,
                    "connection_type": "thematic"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Innovation Focus",
                    "description": "Recurring theme of innovation across different domains",
                    "evidence_count": 3,
                    "confidence": 0.85
                }
            ],
            "recommendations": [
                "Explore AI applications in your field",
                "Develop communication skills for better leadership"
            ]
        }
        
        # Test metadata generation
        start_time = time.time()
        time.sleep(0.1)  # Small delay to ensure measurable duration
        
        metadata = self.service._generate_analysis_metadata(
            self.test_memory_data,
            "formatted memory content",
            start_time,
            mock_analysis_results
        )
        
        # Verify basic metadata structure
        self.assertIn("analysis_timestamp", metadata)
        self.assertIn("analysis_id", metadata)
        self.assertIn("model_used", metadata)
        self.assertIn("service_version", metadata)
        self.assertIn("analysis_duration", metadata)
        
        # Verify memory statistics
        memory_stats = metadata["memory_statistics"]
        self.assertEqual(memory_stats["insights_analyzed"], 3)
        self.assertEqual(memory_stats["conversations_analyzed"], 2)
        self.assertEqual(memory_stats["total_items_analyzed"], 5)
        self.assertIn("technology", memory_stats["memory_categories"])
        self.assertIn("communication", memory_stats["memory_categories"])
        self.assertIn("business", memory_stats["memory_categories"])
        
        # Verify processing metadata
        processing_meta = metadata["processing_metadata"]
        self.assertFalse(processing_meta["chunked_analysis"])
        self.assertEqual(processing_meta["chunks_processed"], 1)
        self.assertGreater(processing_meta["total_content_size"], 0)
        
        # Verify results metadata
        results_meta = metadata["results_metadata"]
        self.assertEqual(results_meta["connections_discovered"], 2)
        self.assertEqual(results_meta["meta_patterns_identified"], 1)
        self.assertEqual(results_meta["recommendations_generated"], 2)
        self.assertIn("cross_domain", results_meta["connection_types"])
        self.assertIn("thematic", results_meta["connection_types"])
        
        # Verify performance metrics
        perf_metrics = metadata["performance_metrics"]
        self.assertIn("analysis_speed", perf_metrics)
        self.assertIn("efficiency_metrics", perf_metrics)
        self.assertIn("resource_usage", perf_metrics)
        self.assertGreater(perf_metrics["analysis_speed"]["items_per_second"], 0)
        
        # Verify system context
        system_context = metadata["system_context"]
        self.assertIn("python_version", system_context)
        self.assertIn("platform", system_context)
        self.assertIn("process_id", system_context)
        
        # Verify configuration snapshot
        config_snapshot = metadata["configuration"]
        self.assertIn("min_insights_required", config_snapshot)
        self.assertIn("cache_ttl_settings", config_snapshot)
    
    def test_analysis_history_storage(self):
        """Test analysis history storage and retrieval"""
        # Create mock analysis results with metadata
        mock_analysis_results = {
            "connections": [
                {"title": "Test Connection", "surprise_factor": 0.8, "relevance": 0.9}
            ],
            "meta_patterns": [
                {"pattern_name": "Test Pattern", "confidence": 0.7}
            ],
            "recommendations": ["Test recommendation"],
            "metadata": {
                "analysis_id": "test_analysis_123",
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_duration": 2.5,
                "model_used": "llama3:8b",
                "memory_statistics": {
                    "total_items_analyzed": 5,
                    "memory_categories": {"test": 1},
                    "date_range": {"earliest": "2024-01-01", "latest": "2024-01-02", "span_days": 1}
                },
                "processing_metadata": {
                    "chunked_analysis": False
                },
                "performance_metrics": {
                    "analysis_speed": {"items_per_second": 2.0},
                    "efficiency_metrics": {"connections_per_insight": 0.5}
                }
            }
        }
        
        # Store analysis in history
        self.service._store_analysis_history(mock_analysis_results)
        
        # Verify history file was created
        self.assertTrue(self.history_file.exists())
        
        # Load and verify history content
        with open(self.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        self.assertIn("analyses", history)
        self.assertIn("metadata", history)
        self.assertEqual(len(history["analyses"]), 1)
        
        # Verify history entry structure
        entry = history["analyses"][0]
        self.assertEqual(entry["analysis_id"], "test_analysis_123")
        self.assertIn("timestamp", entry)
        self.assertIn("summary", entry)
        self.assertIn("performance_snapshot", entry)
        self.assertIn("context", entry)
        self.assertIn("results_preview", entry)
        
        # Verify summary data
        summary = entry["summary"]
        self.assertEqual(summary["connections_count"], 1)
        self.assertEqual(summary["patterns_count"], 1)
        self.assertEqual(summary["analysis_duration"], 2.5)
        
        # Test retrieving history
        retrieved_history = self.service.get_analysis_history()
        self.assertEqual(len(retrieved_history["analyses"]), 1)
        self.assertEqual(retrieved_history["analyses"][0]["analysis_id"], "test_analysis_123")
        
        # Test history limit
        limited_history = self.service.get_analysis_history(limit=0)
        self.assertEqual(len(limited_history["analyses"]), 0)
    
    def test_usage_analytics_tracking(self):
        """Test usage analytics tracking and storage"""
        # Create mock analysis results
        mock_analysis_results = {
            "connections": [
                {"connection_type": "cross_domain"},
                {"connection_type": "thematic"}
            ],
            "meta_patterns": [
                {"pattern_name": "Test Pattern"}
            ],
            "recommendations": ["Test recommendation"],
            "metadata": {
                "analysis_id": "analytics_test_123",
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_duration": 1.5,
                "model_used": "llama3:8b",
                "performance_metrics": {
                    "analysis_speed": {"items_per_second": 3.0},
                    "efficiency_metrics": {"connections_per_insight": 0.8}
                }
            }
        }
        
        # Track usage analytics
        self.service._track_usage_analytics(mock_analysis_results)
        
        # Verify analytics file was created
        self.assertTrue(self.analytics_file.exists())
        
        # Load and verify analytics content
        with open(self.analytics_file, 'r', encoding='utf-8') as f:
            analytics = json.load(f)
        
        # Verify structure
        self.assertIn("usage_statistics", analytics)
        self.assertIn("daily_usage", analytics)
        self.assertIn("performance_trends", analytics)
        self.assertIn("model_usage", analytics)
        self.assertIn("connection_type_distribution", analytics)
        
        # Verify usage statistics
        usage_stats = analytics["usage_statistics"]
        self.assertEqual(usage_stats["total_analyses"], 1)
        self.assertEqual(usage_stats["total_connections_discovered"], 2)
        self.assertEqual(usage_stats["total_patterns_identified"], 1)
        self.assertEqual(usage_stats["total_analysis_time"], 1.5)
        
        # Verify daily usage
        today = datetime.now().date().isoformat()
        self.assertIn(today, analytics["daily_usage"])
        daily_stats = analytics["daily_usage"][today]
        self.assertEqual(daily_stats["analyses_count"], 1)
        self.assertEqual(daily_stats["connections_discovered"], 2)
        
        # Verify performance trends
        perf_trends = analytics["performance_trends"]
        self.assertEqual(len(perf_trends["analysis_durations"]), 1)
        self.assertEqual(perf_trends["analysis_durations"][0], 1.5)
        
        # Verify model usage
        self.assertIn("llama3:8b", analytics["model_usage"])
        self.assertEqual(analytics["model_usage"]["llama3:8b"], 1)
        
        # Verify connection type distribution
        conn_dist = analytics["connection_type_distribution"]
        self.assertEqual(conn_dist["cross_domain"], 1)
        self.assertEqual(conn_dist["thematic"], 1)
        
        # Test retrieving analytics
        retrieved_analytics = self.service.get_usage_analytics()
        self.assertEqual(retrieved_analytics["usage_statistics"]["total_analyses"], 1)
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        # Create test data with various content lengths
        insights = [
            {"content": "Short insight", "category": "test"},
            {"content": "This is a much longer insight with more detailed content that should affect the statistics", "category": "test"},
            {"content": "Medium length insight with some detail", "category": "other"}
        ]
        
        conversations = [
            {"summary": "Brief summary"},
            {"summary": "This is a longer conversation summary with more comprehensive details about the discussion"}
        ]
        
        # Test content statistics calculation
        stats = self.service._calculate_content_statistics(insights, conversations)
        
        self.assertGreater(stats["total_characters"], 0)
        self.assertGreater(stats["total_words"], 0)
        self.assertGreater(stats["average_insight_length"], 0)
        self.assertGreater(stats["average_conversation_length"], 0)
        self.assertGreater(stats["longest_content"], stats["shortest_content"])
        
        # Test memory categories extraction
        categories = self.service._extract_memory_categories(insights)
        self.assertIn("test", categories)
        self.assertIn("other", categories)
        self.assertEqual(categories["test"], 2)
        self.assertEqual(categories["other"], 1)
        
        # Test date range calculation
        insights_with_dates = [
            {"timestamp": "2024-01-01T10:00:00Z"},
            {"timestamp": "2024-01-15T15:30:00Z"},
            {"timestamp": "2024-01-10T12:00:00Z"}
        ]
        
        conversations_with_dates = [
            {"timestamp": "2024-01-05T09:00:00Z"}
        ]
        
        date_range = self.service._calculate_memory_date_range(insights_with_dates, conversations_with_dates)
        self.assertIsNotNone(date_range["earliest"])
        self.assertIsNotNone(date_range["latest"])
        self.assertEqual(date_range["span_days"], 14)  # Jan 1 to Jan 15
    
    def test_connection_analysis_metrics(self):
        """Test connection analysis and metrics calculation"""
        connections = [
            {"surprise_factor": 0.8, "relevance": 0.9, "connection_type": "cross_domain"},
            {"surprise_factor": 0.6, "relevance": 0.7, "connection_type": "thematic"},
            {"surprise_factor": 0.9, "relevance": 0.8, "connection_type": "cross_domain"},
            {"surprise_factor": 0.5, "relevance": 0.6, "connection_type": "temporal"}
        ]
        
        # Test connection type analysis
        conn_types = self.service._analyze_connection_types(connections)
        self.assertEqual(conn_types["cross_domain"], 2)
        self.assertEqual(conn_types["thematic"], 1)
        self.assertEqual(conn_types["temporal"], 1)
        
        # Test average surprise factor calculation
        avg_surprise = self.service._calculate_average_surprise_factor(connections)
        expected_avg = (0.8 + 0.6 + 0.9 + 0.5) / 4
        self.assertAlmostEqual(avg_surprise, expected_avg, places=3)
        
        # Test average relevance calculation
        avg_relevance = self.service._calculate_average_relevance(connections)
        expected_avg_rel = (0.9 + 0.7 + 0.8 + 0.6) / 4
        self.assertAlmostEqual(avg_relevance, expected_avg_rel, places=3)
        
        # Test pattern confidence distribution
        patterns = [
            {"confidence": 0.9},  # high
            {"confidence": 0.7},  # medium
            {"confidence": 0.3},  # low
            {"confidence": 0.85}, # high
            {"confidence": 0.6}   # medium
        ]
        
        distribution = self.service._analyze_pattern_confidence(patterns)
        self.assertEqual(distribution["high"], 2)
        self.assertEqual(distribution["medium"], 2)
        self.assertEqual(distribution["low"], 1)
    
    def test_analytics_structure_validation(self):
        """Test analytics structure validation and migration"""
        # Create incomplete analytics structure
        incomplete_analytics = {
            "usage_statistics": {
                "total_analyses": 5
                # Missing other fields
            },
            "daily_usage": {},
            # Missing other top-level keys
        }
        
        # Test validation
        validated = self.service._validate_analytics_structure(incomplete_analytics)
        
        # Verify all required keys are present
        self.assertIn("usage_statistics", validated)
        self.assertIn("daily_usage", validated)
        self.assertIn("performance_trends", validated)
        self.assertIn("model_usage", validated)
        self.assertIn("connection_type_distribution", validated)
        self.assertIn("metadata", validated)
        
        # Verify nested structure is complete
        usage_stats = validated["usage_statistics"]
        self.assertIn("total_analyses", usage_stats)
        self.assertIn("total_connections_discovered", usage_stats)
        self.assertIn("total_patterns_identified", usage_stats)
        self.assertIn("total_analysis_time", usage_stats)
        
        # Verify original data is preserved
        self.assertEqual(usage_stats["total_analyses"], 5)
    
    def test_history_size_limit(self):
        """Test analysis history size limit enforcement"""
        # Mock config with small history limit
        os.environ['SERENDIPITY_MAX_HISTORY_SIZE'] = '3'
        
        # Create multiple analysis results
        for i in range(5):
            mock_analysis = {
                "connections": [],
                "meta_patterns": [],
                "recommendations": [],
                "metadata": {
                    "analysis_id": f"test_analysis_{i}",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_duration": 1.0,
                    "model_used": "llama3:8b",
                    "memory_statistics": {"total_items_analyzed": 1},
                    "processing_metadata": {"chunked_analysis": False},
                    "performance_metrics": {
                        "analysis_speed": {"items_per_second": 1.0},
                        "efficiency_metrics": {"connections_per_insight": 0.0}
                    }
                }
            }
            self.service._store_analysis_history(mock_analysis)
        
        # Verify history is limited to 3 entries
        history = self.service.get_analysis_history()
        self.assertEqual(len(history["analyses"]), 3)
        
        # Verify we kept the most recent entries
        analysis_ids = [entry["analysis_id"] for entry in history["analyses"]]
        self.assertIn("test_analysis_2", analysis_ids)
        self.assertIn("test_analysis_3", analysis_ids)
        self.assertIn("test_analysis_4", analysis_ids)
        self.assertNotIn("test_analysis_0", analysis_ids)
        self.assertNotIn("test_analysis_1", analysis_ids)
    
    def test_daily_usage_cleanup(self):
        """Test cleanup of old daily usage data"""
        # Create analytics with old daily usage data
        old_date = (datetime.now() - timedelta(days=100)).date().isoformat()
        recent_date = datetime.now().date().isoformat()
        
        mock_analysis = {
            "connections": [],
            "meta_patterns": [],
            "recommendations": [],
            "metadata": {
                "analysis_id": "cleanup_test",
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_duration": 1.0,
                "model_used": "llama3:8b",
                "performance_metrics": {
                    "analysis_speed": {"items_per_second": 1.0},
                    "efficiency_metrics": {"connections_per_insight": 0.0}
                }
            }
        }
        
        # Manually create analytics with old data
        analytics = self.service._create_default_analytics_structure()
        analytics["daily_usage"][old_date] = {"analyses_count": 1}
        analytics["daily_usage"][recent_date] = {"analyses_count": 1}
        
        # Save analytics with old data
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(analytics, f)
        
        # Track new usage (this should trigger cleanup)
        self.service._track_usage_analytics(mock_analysis)
        
        # Verify old data was cleaned up
        updated_analytics = self.service.get_usage_analytics()
        self.assertNotIn(old_date, updated_analytics["daily_usage"])
        self.assertIn(recent_date, updated_analytics["daily_usage"])
    
    @patch('serendipity_service.get_ai_service')
    def test_full_analysis_with_metadata_tracking(self, mock_get_ai_service):
        """Test full analysis workflow with metadata and tracking"""
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_response = json.dumps({
            "connections": [
                {
                    "title": "Technology and Communication",
                    "description": "How technology enhances communication",
                    "surprise_factor": 0.7,
                    "relevance": 0.8,
                    "connected_insights": ["insight1", "insight2"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Explore tech communication tools"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Innovation Theme",
                    "description": "Recurring focus on innovation",
                    "evidence_count": 2,
                    "confidence": 0.8
                }
            ],
            "serendipity_summary": "Analysis reveals strong innovation patterns",
            "recommendations": ["Focus on innovation", "Develop tech skills"]
        })
        
        mock_ai_service.chat.return_value = mock_ai_response
        mock_get_ai_service.return_value = mock_ai_service
        
        # Perform analysis
        results = self.service.analyze_memory()
        
        # Verify results structure
        self.assertIn("connections", results)
        self.assertIn("meta_patterns", results)
        self.assertIn("metadata", results)
        
        # Verify comprehensive metadata
        metadata = results["metadata"]
        self.assertIn("analysis_id", metadata)
        self.assertIn("memory_statistics", metadata)
        self.assertIn("processing_metadata", metadata)
        self.assertIn("results_metadata", metadata)
        self.assertIn("performance_metrics", metadata)
        self.assertIn("system_context", metadata)
        self.assertIn("configuration", metadata)
        
        # Verify history was stored
        self.assertTrue(self.history_file.exists())
        history = self.service.get_analysis_history()
        self.assertEqual(len(history["analyses"]), 1)
        
        # Verify analytics were tracked
        self.assertTrue(self.analytics_file.exists())
        analytics = self.service.get_usage_analytics()
        self.assertEqual(analytics["usage_statistics"]["total_analyses"], 1)
        
        # Verify performance metrics are available
        perf_metrics = self.service.get_performance_metrics()
        self.assertIn("recent_performance", perf_metrics)
        self.assertIn("cache_performance", perf_metrics)
        self.assertIn("service_status", perf_metrics)


class TestSerendipityPerformanceMonitoring(unittest.TestCase):
    """Test performance monitoring functionality"""
    
    def setUp(self):
        """Set up test environment"""
        reset_serendipity_service()
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        self.config = get_config()
        
        # Create minimal test memory data
        test_data = {
            "insights": [{"content": "test", "category": "test"}] * 5,
            "conversation_summaries": [{"summary": "test"}] * 2,
            "metadata": {}
        }
        
        with open(self.memory_file, 'w') as f:
            json.dump(test_data, f)
        
        self.service = SerendipityService(config=self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up environment variables
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        # Get initial cache stats
        initial_stats = self.service.get_cache_stats()
        
        # Verify structure
        self.assertIn("memory_cache", initial_stats)
        self.assertIn("analysis_cache", initial_stats)
        self.assertIn("formatted_cache", initial_stats)
        
        # Verify each cache has required fields
        for cache_name in ["memory_cache", "analysis_cache", "formatted_cache"]:
            cache_stats = initial_stats[cache_name]
            self.assertIn("entries", cache_stats)
            self.assertIn("expired", cache_stats)
            self.assertIn("total_accesses", cache_stats)
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality"""
        # Add some test data to caches (simulate usage)
        # This is a bit tricky since caches are private, but we can trigger cache usage
        
        # Clear all caches
        cleared = self.service.clear_cache()
        self.assertIn("memory", cleared)
        self.assertIn("analysis", cleared)
        self.assertIn("formatted", cleared)
        
        # Test selective cache clearing
        cleared_memory = self.service.clear_cache("memory")
        self.assertIn("memory", cleared_memory)
        self.assertNotIn("analysis", cleared_memory)
        
        # Test expired cache cleanup
        removed = self.service.cleanup_expired_cache()
        self.assertIn("memory", removed)
        self.assertIn("analysis", removed)
        self.assertIn("formatted", removed)
    
    def test_service_status(self):
        """Test service status reporting"""
        status = self.service.get_service_status()
        
        # Verify required fields
        self.assertIn("enabled", status)
        self.assertIn("ai_service_available", status)
        self.assertIn("model", status)
        self.assertIn("min_insights_required", status)
        self.assertIn("max_memory_size_mb", status)
        self.assertIn("analysis_timeout", status)
        self.assertIn("memory_file", status)
        self.assertIn("timestamp", status)
        
        # Verify values
        self.assertTrue(status["enabled"])
        self.assertEqual(status["memory_file"], str(self.memory_file))
    
    def test_performance_trends_tracking(self):
        """Test performance trends tracking over multiple analyses"""
        # This test would require multiple analyses to be meaningful
        # For now, we'll test the structure and basic functionality
        
        analytics = self.service.get_usage_analytics()
        
        # Verify performance trends structure
        perf_trends = analytics["performance_trends"]
        self.assertIn("analysis_durations", perf_trends)
        self.assertIn("items_per_second", perf_trends)
        self.assertIn("connections_per_insight", perf_trends)
        
        # Verify all are lists (even if empty)
        for trend_key in perf_trends:
            self.assertIsInstance(perf_trends[trend_key], list)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)