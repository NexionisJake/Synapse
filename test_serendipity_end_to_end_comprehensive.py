#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Serendipity Analysis Pipeline

This module tests the complete serendipity analysis pipeline from start to finish,
including all components, integrations, and user workflows.
"""

import unittest
import json
import tempfile
import shutil
import os
import time
import threading
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from app import app
from config import get_config
from serendipity_service import reset_serendipity_service, SerendipityService
from memory_service import MemoryService
from ai_service import get_ai_service
from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity


class TestSerendipityEndToEndPipeline(unittest.TestCase):
    """End-to-end tests for complete serendipity analysis pipeline"""
    
    def setUp(self):
        """Set up comprehensive end-to-end test environment"""
        reset_serendipity_service()
        
        # Create temporary directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "e2e_memory.json"
        self.history_file = Path(self.temp_dir) / "e2e_history.json"
        self.analytics_file = Path(self.temp_dir) / "e2e_analytics.json"
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Set environment variables
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['SERENDIPITY_HISTORY_FILE'] = str(self.history_file)
        os.environ['SERENDIPITY_ANALYTICS_FILE'] = str(self.analytics_file)
        os.environ['SERENDIPITY_CACHE_DIR'] = str(self.cache_dir)
        
        # Create comprehensive test data
        self.create_comprehensive_test_data()
        
        # Set up Flask test client
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Track pipeline metrics
        self.pipeline_metrics = {
            'start_time': None,
            'end_time': None,
            'stages': {},
            'errors': [],
            'warnings': []
        }
    
    def tearDown(self):
        """Clean up end-to-end test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        for env_var in ['MEMORY_FILE', 'ENABLE_SERENDIPITY_ENGINE', 
                       'SERENDIPITY_HISTORY_FILE', 'SERENDIPITY_ANALYTICS_FILE',
                       'SERENDIPITY_CACHE_DIR']:
            os.environ.pop(env_var, None)
        reset_serendipity_service()
    
    def create_comprehensive_test_data(self):
        """Create comprehensive test data for end-to-end testing"""
        # Create realistic memory data with diverse content
        insights = []
        conversation_summaries = []
        
        # Technology insights
        tech_insights = [
            "User is passionate about artificial intelligence and machine learning applications",
            "Strong interest in sustainable technology and green energy solutions",
            "Experience with Python programming and data analysis frameworks",
            "Fascination with blockchain technology and decentralized systems",
            "Interest in quantum computing and its potential applications"
        ]
        
        # Personal development insights
        personal_insights = [
            "Values continuous learning and skill development",
            "Believes in the importance of work-life balance",
            "Interested in mindfulness and meditation practices",
            "Values authentic relationships and meaningful connections",
            "Committed to personal growth and self-improvement"
        ]
        
        # Career insights
        career_insights = [
            "Wants to combine technical skills with positive social impact",
            "Interested in leadership roles in technology companies",
            "Values collaborative work environments and team dynamics",
            "Seeks opportunities for mentoring and knowledge sharing",
            "Interested in entrepreneurship and startup culture"
        ]
        
        all_insight_texts = tech_insights + personal_insights + career_insights
        categories = ['technology', 'personal_development', 'career']
        
        for i, insight_text in enumerate(all_insight_texts):
            category = categories[i // 5] if i < 15 else categories[i % 3]
            insights.append({
                "category": category,
                "content": insight_text,
                "confidence": 0.7 + (i % 4) * 0.075,  # Vary confidence
                "tags": self.generate_tags_for_insight(insight_text),
                "evidence": f"Evidence from conversation analysis: {insight_text[:50]}...",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat()
            })
        
        # Create conversation summaries
        conversation_topics = [
            "Discussion about AI ethics and responsible technology development",
            "Conversation about sustainable living and environmental impact",
            "Talk about career transitions and professional development",
            "Discussion about work-life balance and personal well-being",
            "Conversation about emerging technologies and future trends",
            "Talk about leadership styles and team management",
            "Discussion about learning strategies and skill acquisition",
            "Conversation about entrepreneurship and innovation",
            "Talk about mindfulness and stress management techniques",
            "Discussion about networking and professional relationships"
        ]
        
        for i, topic in enumerate(conversation_topics):
            conversation_summaries.append({
                "summary": topic,
                "key_themes": self.extract_themes_from_topic(topic),
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "duration_minutes": 15 + (i % 10) * 5,
                "participants": ["user", "assistant"]
            })
        
        # Create comprehensive memory data
        memory_data = {
            "insights": insights,
            "conversation_summaries": conversation_summaries,
            "metadata": {
                "total_insights": len(insights),
                "total_conversations": len(conversation_summaries),
                "last_updated": datetime.now().isoformat(),
                "data_quality_score": 0.85,
                "categories": list(set(insight["category"] for insight in insights))
            }
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, indent=2)
    
    def generate_tags_for_insight(self, insight_text):
        """Generate relevant tags for an insight"""
        tag_mapping = {
            'artificial intelligence': ['AI', 'machine_learning', 'technology'],
            'machine learning': ['ML', 'AI', 'data_science'],
            'sustainable': ['sustainability', 'environment', 'green_tech'],
            'Python': ['programming', 'coding', 'development'],
            'blockchain': ['crypto', 'decentralized', 'technology'],
            'quantum': ['quantum_computing', 'advanced_tech', 'research'],
            'learning': ['education', 'growth', 'development'],
            'balance': ['wellness', 'lifestyle', 'health'],
            'mindfulness': ['meditation', 'wellness', 'mental_health'],
            'leadership': ['management', 'career', 'professional'],
            'entrepreneurship': ['startup', 'business', 'innovation']
        }
        
        tags = []
        for keyword, tag_list in tag_mapping.items():
            if keyword.lower() in insight_text.lower():
                tags.extend(tag_list)
        
        return list(set(tags))[:5]  # Limit to 5 unique tags
    
    def extract_themes_from_topic(self, topic):
        """Extract key themes from conversation topic"""
        theme_mapping = {
            'AI ethics': ['ethics', 'AI', 'responsibility'],
            'sustainable': ['sustainability', 'environment'],
            'career': ['career', 'professional', 'development'],
            'work-life': ['balance', 'wellness', 'lifestyle'],
            'technology': ['tech', 'innovation', 'future'],
            'leadership': ['leadership', 'management', 'team'],
            'learning': ['education', 'skills', 'growth'],
            'entrepreneurship': ['business', 'startup', 'innovation'],
            'mindfulness': ['wellness', 'mental_health', 'stress'],
            'networking': ['relationships', 'professional', 'connections']
        }
        
        themes = []
        for keyword, theme_list in theme_mapping.items():
            if keyword.lower() in topic.lower():
                themes.extend(theme_list)
        
        return list(set(themes))[:4]  # Limit to 4 unique themes
    
    @patch('serendipity_service.get_ai_service')
    def test_complete_pipeline_success_flow(self, mock_get_ai_service):
        """Test complete successful pipeline from start to finish"""
        print("\n🚀 Testing Complete Pipeline Success Flow...")
        
        self.pipeline_metrics['start_time'] = time.time()
        
        # Stage 1: Setup and Initialization
        print("Stage 1: Service initialization...")
        stage_start = time.time()
        
        mock_ai_service = Mock()
        mock_ai_response = self.create_comprehensive_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        mock_ai_service.test_connection.return_value = {"connected": True, "model": "llama3:8b"}
        mock_get_ai_service.return_value = mock_ai_service
        
        self.pipeline_metrics['stages']['initialization'] = time.time() - stage_start
        print(f"✓ Initialization completed in {self.pipeline_metrics['stages']['initialization']:.3f}s")
        
        # Stage 2: Service Status Check
        print("Stage 2: Service status verification...")
        stage_start = time.time()
        
        response = self.client.get('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        status_data = json.loads(response.data)
        self.assertTrue(status_data['enabled'])
        self.assertIn('model', status_data)
        
        self.pipeline_metrics['stages']['status_check'] = time.time() - stage_start
        print(f"✓ Status check completed in {self.pipeline_metrics['stages']['status_check']:.3f}s")
        
        # Stage 3: Memory Data Loading and Validation
        print("Stage 3: Memory data processing...")
        stage_start = time.time()
        
        # Verify memory file exists and is valid
        self.assertTrue(self.memory_file.exists())
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
        
        self.assertGreater(len(memory_data['insights']), 10)
        self.assertGreater(len(memory_data['conversation_summaries']), 5)
        
        self.pipeline_metrics['stages']['memory_processing'] = time.time() - stage_start
        print(f"✓ Memory processing completed in {self.pipeline_metrics['stages']['memory_processing']:.3f}s")
        print(f"  - Loaded {len(memory_data['insights'])} insights")
        print(f"  - Loaded {len(memory_data['conversation_summaries'])} conversations")
        
        # Stage 4: AI Analysis Execution
        print("Stage 4: AI analysis execution...")
        stage_start = time.time()
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        analysis_data = json.loads(response.data)
        
        # Verify analysis results structure
        required_keys = ['connections', 'meta_patterns', 'serendipity_summary', 'recommendations', 'metadata']
        for key in required_keys:
            self.assertIn(key, analysis_data)
        
        # Verify content quality
        self.assertGreater(len(analysis_data['connections']), 0)
        self.assertGreater(len(analysis_data['meta_patterns']), 0)
        self.assertGreater(len(analysis_data['recommendations']), 0)
        self.assertGreater(len(analysis_data['serendipity_summary']), 50)
        
        # Verify metadata
        metadata = analysis_data['metadata']
        self.assertIn('analysis_id', metadata)
        self.assertIn('timestamp', metadata)
        self.assertIn('model_used', metadata)
        self.assertIn('insights_analyzed', metadata)
        self.assertIn('analysis_duration', metadata)
        
        self.pipeline_metrics['stages']['ai_analysis'] = time.time() - stage_start
        print(f"✓ AI analysis completed in {self.pipeline_metrics['stages']['ai_analysis']:.3f}s")
        print(f"  - Found {len(analysis_data['connections'])} connections")
        print(f"  - Identified {len(analysis_data['meta_patterns'])} patterns")
        print(f"  - Generated {len(analysis_data['recommendations'])} recommendations")
        
        # Stage 5: History and Analytics Update
        print("Stage 5: History and analytics update...")
        stage_start = time.time()
        
        # Check history
        response = self.client.get('/api/serendipity/history')
        self.assertEqual(response.status_code, 200)
        history_data = json.loads(response.data)
        self.assertEqual(len(history_data['analyses']), 1)
        self.assertEqual(history_data['analyses'][0]['analysis_id'], metadata['analysis_id'])
        
        # Check analytics
        response = self.client.get('/api/serendipity/analytics')
        self.assertEqual(response.status_code, 200)
        analytics_data = json.loads(response.data)
        self.assertEqual(analytics_data['usage_statistics']['total_analyses'], 1)
        self.assertEqual(analytics_data['usage_statistics']['total_connections_discovered'], 
                        len(analysis_data['connections']))
        
        self.pipeline_metrics['stages']['history_analytics'] = time.time() - stage_start
        print(f"✓ History and analytics updated in {self.pipeline_metrics['stages']['history_analytics']:.3f}s")
        
        # Stage 6: Performance Metrics Collection
        print("Stage 6: Performance metrics collection...")
        stage_start = time.time()
        
        response = self.client.get('/api/serendipity/performance')
        self.assertEqual(response.status_code, 200)
        perf_data = json.loads(response.data)
        
        self.assertIn('recent_performance', perf_data)
        self.assertIn('cache_performance', perf_data)
        self.assertIn('service_status', perf_data)
        
        self.pipeline_metrics['stages']['performance_metrics'] = time.time() - stage_start
        print(f"✓ Performance metrics collected in {self.pipeline_metrics['stages']['performance_metrics']:.3f}s")
        
        # Stage 7: Cache Management Verification
        print("Stage 7: Cache management verification...")
        stage_start = time.time()
        
        # Test cache clearing
        response = self.client.delete('/api/serendipity/cache?type=all')
        self.assertEqual(response.status_code, 200)
        cache_data = json.loads(response.data)
        self.assertIn('cleared_counts', cache_data)
        
        self.pipeline_metrics['stages']['cache_management'] = time.time() - stage_start
        print(f"✓ Cache management verified in {self.pipeline_metrics['stages']['cache_management']:.3f}s")
        
        # Pipeline completion
        self.pipeline_metrics['end_time'] = time.time()
        total_time = self.pipeline_metrics['end_time'] - self.pipeline_metrics['start_time']
        
        print(f"\n🎉 Complete Pipeline Success Flow Completed!")
        print(f"Total pipeline time: {total_time:.3f}s")
        print(f"Stages breakdown:")
        for stage, duration in self.pipeline_metrics['stages'].items():
            percentage = (duration / total_time) * 100
            print(f"  - {stage}: {duration:.3f}s ({percentage:.1f}%)")
        
        # Verify overall performance
        self.assertLess(total_time, 30.0, "Complete pipeline should finish within 30 seconds")
        
        return analysis_data
    
    @patch('serendipity_service.get_ai_service')
    def test_pipeline_error_recovery_flow(self, mock_get_ai_service):
        """Test pipeline error recovery and resilience"""
        print("\n🔧 Testing Pipeline Error Recovery Flow...")
        
        # Test 1: AI Service Failure Recovery
        print("Test 1: AI service failure recovery...")
        mock_ai_service = Mock()
        mock_ai_service.chat.side_effect = Exception("AI service temporarily unavailable")
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.post('/api/serendipity')
        self.assertIn(response.status_code, [500, 503])  # Should handle gracefully
        
        error_data = json.loads(response.data)
        self.assertIn('error', error_data)
        print("✓ AI service failure handled gracefully")
        
        # Test 2: Recovery after AI service restoration
        print("Test 2: Recovery after service restoration...")
        mock_ai_service.chat.side_effect = None
        mock_ai_response = self.create_comprehensive_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        print("✓ Service recovery successful")
        
        # Test 3: Partial Data Corruption Recovery
        print("Test 3: Partial data corruption recovery...")
        
        # Corrupt part of the memory file
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
        
        # Remove some insights but keep enough for analysis
        memory_data['insights'] = memory_data['insights'][:5]  # Reduce to minimum
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f)
        
        response = self.client.post('/api/serendipity')
        # Should either succeed with reduced data or fail gracefully
        self.assertIn(response.status_code, [200, 400])
        print("✓ Partial data corruption handled")
        
        # Test 4: Network Timeout Simulation
        print("Test 4: Network timeout simulation...")
        
        def slow_ai_response(*args, **kwargs):
            time.sleep(2)  # Simulate slow response
            return json.dumps(self.create_comprehensive_ai_response())
        
        mock_ai_service.chat.side_effect = slow_ai_response
        
        start_time = time.time()
        response = self.client.post('/api/serendipity')
        end_time = time.time()
        
        # Should complete but may take longer
        self.assertIn(response.status_code, [200, 408, 504])
        print(f"✓ Timeout scenario handled (took {end_time - start_time:.2f}s)")
        
        print("🎉 Pipeline Error Recovery Flow Completed!")
    
    @patch('serendipity_service.get_ai_service')
    def test_pipeline_concurrent_load(self, mock_get_ai_service):
        """Test pipeline under concurrent load"""
        print("\n⚡ Testing Pipeline Concurrent Load...")
        
        mock_ai_service = Mock()
        mock_ai_response = self.create_comprehensive_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        mock_get_ai_service.return_value = mock_ai_service
        
        def make_analysis_request():
            return self.client.post('/api/serendipity')
        
        # Test with 3 concurrent requests
        print("Testing 3 concurrent analysis requests...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_analysis_request) for _ in range(3)]
            responses = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests completed
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f"✓ {success_count}/3 concurrent requests succeeded")
        print(f"✓ Total time for concurrent requests: {total_time:.3f}s")
        
        # Verify analytics reflect all successful analyses
        if success_count > 0:
            response = self.client.get('/api/serendipity/analytics')
            analytics_data = json.loads(response.data)
            self.assertGreaterEqual(analytics_data['usage_statistics']['total_analyses'], success_count)
        
        print("🎉 Pipeline Concurrent Load Test Completed!")
    
    @patch('serendipity_service.get_ai_service')
    def test_pipeline_data_quality_validation(self, mock_get_ai_service):
        """Test pipeline data quality validation and handling"""
        print("\n🔍 Testing Pipeline Data Quality Validation...")
        
        mock_ai_service = Mock()
        mock_ai_response = self.create_comprehensive_ai_response()
        mock_ai_service.chat.return_value = json.dumps(mock_ai_response)
        mock_get_ai_service.return_value = mock_ai_service
        
        # Test 1: High-quality data
        print("Test 1: High-quality data processing...")
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        analysis_data = json.loads(response.data)
        
        # Should produce high-quality results
        self.assertGreater(len(analysis_data['connections']), 3)
        self.assertGreater(len(analysis_data['meta_patterns']), 1)
        print("✓ High-quality data processed successfully")
        
        # Test 2: Low-quality data (sparse insights)
        print("Test 2: Low-quality data handling...")
        sparse_data = {
            "insights": [
                {"content": "Short insight", "category": "test"},
                {"content": "Another short one", "category": "test"},
                {"content": "Third insight", "category": "test"}
            ],
            "conversation_summaries": [
                {"summary": "Brief conversation"}
            ],
            "metadata": {}
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(sparse_data, f)
        
        response = self.client.post('/api/serendipity')
        # Should handle gracefully, possibly with fewer results
        self.assertIn(response.status_code, [200, 400])
        
        if response.status_code == 200:
            analysis_data = json.loads(response.data)
            # Results may be limited but should be valid
            self.assertIsInstance(analysis_data['connections'], list)
            print("✓ Low-quality data handled gracefully")
        else:
            print("✓ Low-quality data rejected appropriately")
        
        # Test 3: Mixed quality data
        print("Test 3: Mixed quality data processing...")
        mixed_data = {
            "insights": [
                {"content": "Detailed insight about artificial intelligence and its applications in healthcare", "category": "technology"},
                {"content": "Short", "category": "test"},
                {"content": "Another comprehensive insight about sustainable energy solutions and their environmental impact", "category": "environment"},
                {"content": "Brief note", "category": "test"},
                {"content": "Extensive insight about career development and professional growth strategies", "category": "career"}
            ],
            "conversation_summaries": [
                {"summary": "Detailed conversation about technology trends and future implications"},
                {"summary": "Brief chat"}
            ],
            "metadata": {}
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(mixed_data, f)
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 200)
        analysis_data = json.loads(response.data)
        
        # Should focus on high-quality insights
        self.assertGreater(len(analysis_data['connections']), 0)
        print("✓ Mixed quality data processed with quality filtering")
        
        print("🎉 Pipeline Data Quality Validation Completed!")
    
    def create_comprehensive_ai_response(self):
        """Create comprehensive AI response for testing"""
        return {
            "connections": [
                {
                    "title": "Technology-Impact Synergy",
                    "description": "Strong connection between technology interests and desire for positive social impact",
                    "surprise_factor": 0.8,
                    "relevance": 0.95,
                    "connected_insights": ["AI/ML interest", "social impact goals"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Explore AI applications in social good projects"
                },
                {
                    "title": "Learning-Leadership Pipeline",
                    "description": "Clear progression from continuous learning to leadership aspirations",
                    "surprise_factor": 0.6,
                    "relevance": 0.88,
                    "connected_insights": ["continuous learning", "leadership interest"],
                    "connection_type": "developmental",
                    "actionable_insight": "Develop teaching and mentoring skills"
                },
                {
                    "title": "Sustainability-Technology Integration",
                    "description": "Intersection of environmental consciousness and technical expertise",
                    "surprise_factor": 0.7,
                    "relevance": 0.92,
                    "connected_insights": ["sustainability interest", "technical skills"],
                    "connection_type": "thematic",
                    "actionable_insight": "Focus on green technology solutions"
                },
                {
                    "title": "Wellness-Performance Balance",
                    "description": "Sophisticated understanding of work-life integration for optimal performance",
                    "surprise_factor": 0.5,
                    "relevance": 0.85,
                    "connected_insights": ["mindfulness practice", "career ambitions"],
                    "connection_type": "balancing",
                    "actionable_insight": "Integrate wellness practices into professional development"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Conscious Technology Leadership",
                    "description": "Emerging pattern of technology expertise combined with ethical awareness and social responsibility",
                    "evidence_count": 8,
                    "confidence": 0.89
                },
                {
                    "pattern_name": "Integrated Growth Mindset",
                    "description": "Holistic approach to development encompassing technical, personal, and professional dimensions",
                    "evidence_count": 12,
                    "confidence": 0.92
                },
                {
                    "pattern_name": "Future-Oriented Innovation",
                    "description": "Consistent focus on emerging technologies and their potential for positive change",
                    "evidence_count": 6,
                    "confidence": 0.78
                }
            ],
            "serendipity_summary": "Analysis reveals a sophisticated individual with a rare combination of deep technical expertise, strong ethical foundation, and genuine commitment to positive impact. The convergence of AI/ML interests with sustainability concerns and leadership aspirations suggests potential for significant contributions to conscious technology development. The integration of mindfulness practices with ambitious career goals indicates mature self-awareness and sustainable success strategies.",
            "recommendations": [
                "Explore leadership roles in AI ethics and responsible technology development",
                "Consider founding or joining organizations focused on technology for social good",
                "Develop expertise in sustainable AI and green computing practices",
                "Build a portfolio of projects demonstrating technology-impact integration",
                "Engage with communities working on conscious technology and ethical AI",
                "Consider advanced education or certification in AI ethics and sustainability",
                "Mentor others interested in combining technology with positive impact",
                "Document and share insights about balancing technical excellence with social responsibility"
            ]
        }


class TestSerendipityPipelineStressTest(unittest.TestCase):
    """Stress testing for serendipity analysis pipeline"""
    
    def setUp(self):
        """Set up stress test environment"""
        reset_serendipity_service()
        
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "stress_memory.json"
        
        os.environ['MEMORY_FILE'] = str(self.memory_file)
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up stress test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop('MEMORY_FILE', None)
        os.environ.pop('ENABLE_SERENDIPITY_ENGINE', None)
        reset_serendipity_service()
    
    def create_stress_test_data(self, size):
        """Create large dataset for stress testing"""
        insights = []
        conversation_summaries = []
        
        # Generate large number of insights
        for i in range(size):
            insights.append({
                "category": f"category_{i % 20}",
                "content": f"Stress test insight {i+1}: " + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 3,
                "confidence": 0.5 + (i % 10) * 0.05,
                "tags": [f"tag_{i % 100}", f"tag_{(i+1) % 100}", f"tag_{(i+2) % 100}"],
                "evidence": f"Comprehensive evidence for insight {i+1} with detailed supporting information and extensive context that simulates real-world data complexity.",
                "timestamp": (datetime.now() - timedelta(hours=i % 24, minutes=i % 60)).isoformat()
            })
        
        # Generate conversation summaries
        for i in range(size // 10):
            conversation_summaries.append({
                "summary": f"Stress test conversation {i+1}: Comprehensive discussion covering multiple complex topics with detailed analysis and extensive dialogue that represents realistic conversation data.",
                "key_themes": [f"theme_{i % 20}", f"theme_{(i+1) % 20}", f"theme_{(i+2) % 20}"],
                "timestamp": (datetime.now() - timedelta(hours=i % 24)).isoformat(),
                "duration_minutes": 10 + (i % 50),
                "participants": ["user", "assistant"]
            })
        
        data = {
            "insights": insights,
            "conversation_summaries": conversation_summaries,
            "metadata": {
                "total_insights": len(insights),
                "total_conversations": len(conversation_summaries),
                "last_updated": datetime.now().isoformat(),
                "data_quality_score": 0.8
            }
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @patch('serendipity_service.get_ai_service')
    def test_large_dataset_stress(self, mock_get_ai_service):
        """Test pipeline with large dataset (1000 insights)"""
        print("\n🔥 Testing Large Dataset Stress (1000 insights)...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({
            "connections": [{"title": "Test", "description": "Test", "surprise_factor": 0.5, "relevance": 0.5}],
            "meta_patterns": [{"pattern_name": "Test", "description": "Test", "confidence": 0.5, "evidence_count": 1}],
            "serendipity_summary": "Stress test summary",
            "recommendations": ["Test recommendation"]
        })
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_stress_test_data(1000)
        
        start_time = time.time()
        response = self.client.post('/api/serendipity')
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"✓ Large dataset processed in {processing_time:.3f}s")
        
        # Verify memory usage didn't explode
        if hasattr(self, 'process'):
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"  Memory usage: {memory_mb:.1f} MB")
            self.assertLess(memory_mb, 500, "Memory usage should stay reasonable")
        
        self.assertLess(processing_time, 60.0, "Large dataset should process within 60 seconds")
    
    @patch('serendipity_service.get_ai_service')
    def test_rapid_sequential_requests(self, mock_get_ai_service):
        """Test rapid sequential requests"""
        print("\n⚡ Testing Rapid Sequential Requests...")
        
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = json.dumps({
            "connections": [], "meta_patterns": [], "serendipity_summary": "Test", "recommendations": []
        })
        mock_get_ai_service.return_value = mock_ai_service
        
        self.create_stress_test_data(50)
        
        # Make 10 rapid sequential requests
        start_time = time.time()
        responses = []
        
        for i in range(10):
            response = self.client.post('/api/serendipity')
            responses.append(response)
            print(f"  Request {i+1}/10: {response.status_code}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f"✓ {success_count}/10 requests succeeded in {total_time:.3f}s")
        print(f"  Average time per request: {total_time/10:.3f}s")
        
        # At least 80% should succeed
        self.assertGreaterEqual(success_count, 8, "At least 8/10 rapid requests should succeed")


if __name__ == '__main__':
    # Configure test environment
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Create comprehensive test suite
    suite = unittest.TestSuite()
    
    # Add end-to-end pipeline tests
    suite.addTest(unittest.makeSuite(TestSerendipityEndToEndPipeline))
    
    # Add stress tests
    suite.addTest(unittest.makeSuite(TestSerendipityPipelineStressTest))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("END-TO-END PIPELINE TEST SUITE SUMMARY")
    print(f"{'='*80}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Pipeline is highly robust and reliable!")
        elif success_rate >= 75:
            print("✅ GOOD: Pipeline is stable with minor issues")
        elif success_rate >= 60:
            print("⚠️  FAIR: Pipeline has some reliability concerns")
        else:
            print("❌ POOR: Pipeline needs significant improvements")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"{i}. {test}")
            print(f"   {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 ERRORS ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
            print(f"   {traceback.split('Exception:')[-1].strip()}")
    
    print(f"\n{'='*80}")