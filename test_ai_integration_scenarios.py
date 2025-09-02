"""
Integration tests for AI analysis engine with mock and real scenarios
Tests for Task 4: Comprehensive tests for AI integration including mock and real scenarios
"""

import pytest
import json
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

from serendipity_service import SerendipityService, SerendipityServiceError
from ai_service import AIService, AIServiceError
from config import get_config


class TestMockAIScenarios:
    """Test AI integration with various mock scenarios"""
    
    @pytest.fixture
    def serendipity_service_with_mock_ai(self):
        """Create serendipity service with fully mocked AI"""
        config = Mock()
        config.ENABLE_SERENDIPITY_ENGINE = True
        config.OLLAMA_MODEL = "llama3:8b"
        config.SERENDIPITY_MIN_INSIGHTS = 3
        config.SERENDIPITY_MAX_MEMORY_SIZE_MB = 50
        config.SERENDIPITY_ANALYSIS_TIMEOUT = 60
        config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
        config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
        config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
        config.MEMORY_FILE = "test_memory.json"
        
        mock_ai_service = Mock()
        
        with patch('serendipity_service.get_ai_service', return_value=mock_ai_service):
            service = SerendipityService(config=config)
            service.ai_service = mock_ai_service
            return service, mock_ai_service
    
    def test_mock_successful_analysis(self):
        """Test successful analysis with mocked AI responses"""
        service, mock_ai = self.serendipity_service_with_mock_ai()
        
        # Mock AI response
        mock_response = json.dumps({
            "connections": [
                {
                    "title": "Mock Connection",
                    "description": "This is a mock connection for testing",
                    "surprise_factor": 0.8,
                    "relevance": 0.9,
                    "connected_insights": ["insight1", "insight2"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Test this connection"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Mock Pattern",
                    "description": "This is a mock pattern",
                    "evidence_count": 3,
                    "confidence": 0.85
                }
            ],
            "serendipity_summary": "Mock analysis completed successfully",
            "recommendations": ["Mock recommendation 1", "Mock recommendation 2"]
        })
        
        mock_ai.chat.return_value = mock_response
        
        formatted_memory = "Mock formatted memory data for testing"
        result = service._discover_connections(formatted_memory)
        
        assert result is not None
        assert len(result["connections"]) == 1
        assert len(result["meta_patterns"]) == 1
        assert result["connections"][0]["title"] == "Mock Connection"
        assert mock_ai.chat.called
    
    def test_mock_partial_json_response(self):
        """Test handling of partial/malformed JSON responses"""
        service, mock_ai = self.serendipity_service_with_mock_ai()
        
        # Mock partial JSON response
        partial_response = """{
            "connections": [
                {
                    "title": "Partial Connection",
                    "description": "This connection is incomplete"
                    // Missing fields
                }
            ],
            "meta_patterns": [],
            "serendipity_summary": "Partial analysis"
            // Missing recommendations
        }"""
        
        mock_ai.chat.return_value = partial_response
        
        result = service._discover_connections("test memory")
        
        # Should handle partial response gracefully
        assert result is not None
        assert "connections" in result
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0  # Should have defaults
    
    def test_mock_streaming_response(self):
        """Test streaming response handling with mocked chunks"""
        service, mock_ai = self.serendipity_service_with_mock_ai()
        
        # Mock streaming chunks
        def mock_streaming_response(*args, **kwargs):
            if kwargs.get('stream'):
                chunks = [
                    {"content": '{"connections": [', "done": False},
                    {"content": '{"title": "Streaming Connection",', "done": False},
                    {"content": '"description": "Test streaming"}],', "done": False},
                    {"content": '"meta_patterns": [],', "done": False},
                    {"content": '"serendipity_summary": "Streaming test",', "done": False},
                    {"content": '"recommendations": ["Stream rec"]}', "done": False},
                    {"content": "", "done": True, "full_content": "complete_response"}
                ]
                for chunk in chunks:
                    yield chunk
            else:
                return "non-streaming response"
        
        mock_ai.chat.side_effect = mock_streaming_response
        
        conversation = [{"role": "user", "content": "test"}]
        result = service._handle_streaming_analysis(conversation, time.time())
        
        assert "Streaming Connection" in result
    
    def test_mock_ai_service_errors(self):
        """Test various AI service error scenarios"""
        service, mock_ai = self.serendipity_service_with_mock_ai()
        
        # Test different error types
        error_scenarios = [
            AIServiceError("Connection timeout"),
            AIServiceError("Model not available"),
            AIServiceError("Invalid request format"),
            Exception("Unexpected error")
        ]
        
        for error in error_scenarios:
            mock_ai.chat.side_effect = error
            
            result = service._discover_connections("test memory")
            
            # Should return fallback response, not raise exception
            assert result is not None
            assert "error" in result["serendipity_summary"].lower() or "failed" in result["serendipity_summary"].lower()
            
            # Reset for next test
            mock_ai.reset_mock()
    
    def test_mock_retry_behavior(self):
        """Test retry behavior with different failure patterns"""
        service, mock_ai = self.serendipity_service_with_mock_ai()
        
        # Test: Fail twice, succeed on third attempt
        success_response = json.dumps({
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Success after retries",
            "recommendations": []
        })
        
        mock_ai.chat.side_effect = [
            AIServiceError("First failure"),
            AIServiceError("Second failure"),
            success_response
        ]
        
        result = service._discover_connections("test memory")
        
        assert result is not None
        assert "Success after retries" in result["serendipity_summary"]
        assert mock_ai.chat.call_count == 3
    
    def test_mock_cache_behavior(self):
        """Test caching behavior with mocked responses"""
        service, mock_ai = self.serendipity_service_with_mock_ai()
        
        mock_response = json.dumps({
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Cached response test",
            "recommendations": []
        })
        
        mock_ai.chat.return_value = mock_response
        
        # First call
        result1 = service._discover_connections("test memory")
        
        # Second call with same memory should use cache
        result2 = service._discover_connections("test memory")
        
        assert result1 == result2
        assert mock_ai.chat.call_count == 1  # Only called once due to caching


class TestRealAIScenarios:
    """Test AI integration with real Ollama service (if available)"""
    
    @pytest.fixture
    def real_ai_service(self):
        """Create real AI service if Ollama is available"""
        try:
            ai_service = AIService(model="llama3:8b")
            # Test connection
            ai_service.test_connection()
            return ai_service
        except Exception:
            pytest.skip("Ollama service not available for real AI tests")
    
    @pytest.fixture
    def serendipity_service_with_real_ai(self, real_ai_service):
        """Create serendipity service with real AI service"""
        config = get_config()
        config.ENABLE_SERENDIPITY_ENGINE = True
        config.SERENDIPITY_ANALYSIS_TIMEOUT = 120  # Longer timeout for real AI
        
        service = SerendipityService(config=config)
        service.ai_service = real_ai_service
        return service
    
    @pytest.mark.integration
    def test_real_ai_simple_analysis(self, serendipity_service_with_real_ai):
        """Test simple analysis with real AI service"""
        service = serendipity_service_with_real_ai
        
        # Simple test memory
        formatted_memory = """
        === INSIGHTS AND KNOWLEDGE ===
        
        LEARNING (2 insights):
        • Programming requires consistent practice and patience (confidence: 0.9)
        • Reading books helps expand knowledge and perspective (confidence: 0.8)
        
        PRODUCTIVITY (1 insights):
        • Time management is crucial for achieving goals (confidence: 0.85)
        
        === CONVERSATION SUMMARIES ===
        
        Conversation 1: Discussion about effective learning strategies and their application
        Key themes: learning, strategies, application
        
        === MEMORY METADATA ===
        Total insights: 3
        Last updated: 2024-01-01
        """
        
        try:
            result = service._discover_connections(formatted_memory)
            
            # Validate structure
            assert result is not None
            assert "connections" in result
            assert "meta_patterns" in result
            assert "serendipity_summary" in result
            assert "recommendations" in result
            
            # Check that AI found some connections
            if len(result["connections"]) > 0:
                conn = result["connections"][0]
                assert "title" in conn
                assert "description" in conn
                assert isinstance(conn.get("surprise_factor", 0), (int, float))
                assert isinstance(conn.get("relevance", 0), (int, float))
            
            print(f"Real AI analysis result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            pytest.fail(f"Real AI analysis failed: {e}")
    
    @pytest.mark.integration
    def test_real_ai_streaming_analysis(self, serendipity_service_with_real_ai):
        """Test streaming analysis with real AI service"""
        service = serendipity_service_with_real_ai
        
        # Larger memory data to trigger streaming
        large_memory = """
        === INSIGHTS AND KNOWLEDGE ===
        
        PROGRAMMING (5 insights):
        • Object-oriented programming helps organize complex code (confidence: 0.9)
        • Functional programming offers different problem-solving approaches (confidence: 0.8)
        • Code reviews improve code quality and team knowledge sharing (confidence: 0.85)
        • Testing is essential for maintaining code reliability (confidence: 0.9)
        • Documentation saves time for future developers (confidence: 0.8)
        
        LEARNING (4 insights):
        • Spaced repetition improves long-term retention (confidence: 0.9)
        • Active learning is more effective than passive reading (confidence: 0.85)
        • Teaching others helps solidify your own understanding (confidence: 0.8)
        • Learning from mistakes is often more valuable than success (confidence: 0.75)
        
        PRODUCTIVITY (3 insights):
        • Deep work requires eliminating distractions (confidence: 0.9)
        • Time blocking helps maintain focus on important tasks (confidence: 0.8)
        • Regular breaks prevent mental fatigue (confidence: 0.85)
        
        === CONVERSATION SUMMARIES ===
        
        Conversation 1: Deep dive into software architecture patterns and their trade-offs
        Key themes: architecture, patterns, trade-offs, scalability
        
        Conversation 2: Discussion about effective learning methodologies for technical skills
        Key themes: learning, methodology, technical skills, practice
        
        Conversation 3: Exploration of productivity techniques for knowledge workers
        Key themes: productivity, focus, time management, efficiency
        """ * 2  # Double the content to ensure it's large enough
        
        try:
            result = service._discover_connections(large_memory, enable_streaming=True)
            
            assert result is not None
            assert "connections" in result
            
            # Should have found multiple connections in this rich dataset
            assert len(result["connections"]) >= 2
            
            print(f"Real AI streaming analysis found {len(result['connections'])} connections")
            
        except Exception as e:
            pytest.fail(f"Real AI streaming analysis failed: {e}")
    
    @pytest.mark.integration
    def test_real_ai_timeout_handling(self, serendipity_service_with_real_ai):
        """Test timeout handling with real AI service"""
        service = serendipity_service_with_real_ai
        service.analysis_timeout = 5  # Very short timeout
        
        # Large complex memory that might take time to analyze
        complex_memory = "Complex analysis data " * 1000
        
        try:
            result = service._discover_connections(complex_memory)
            
            # Should either complete quickly or return fallback response
            assert result is not None
            
        except Exception as e:
            # Timeout is acceptable for this test
            assert "timeout" in str(e).lower() or "timed out" in str(e).lower()
    
    @pytest.mark.integration
    def test_real_ai_json_validation(self, serendipity_service_with_real_ai):
        """Test that real AI produces valid JSON that passes validation"""
        service = serendipity_service_with_real_ai
        
        formatted_memory = """
        === INSIGHTS AND KNOWLEDGE ===
        
        TECHNOLOGY (2 insights):
        • Artificial intelligence is transforming many industries (confidence: 0.9)
        • Cloud computing enables scalable applications (confidence: 0.85)
        
        === CONVERSATION SUMMARIES ===
        
        Conversation 1: Discussion about the future of technology and its impact
        Key themes: technology, future, impact, society
        """
        
        try:
            result = service._discover_connections(formatted_memory)
            
            # Validate all required fields are present and properly typed
            assert isinstance(result["connections"], list)
            assert isinstance(result["meta_patterns"], list)
            assert isinstance(result["serendipity_summary"], str)
            assert isinstance(result["recommendations"], list)
            
            # Validate connection structure if any exist
            for conn in result["connections"]:
                assert isinstance(conn["title"], str)
                assert isinstance(conn["description"], str)
                assert isinstance(conn["surprise_factor"], (int, float))
                assert isinstance(conn["relevance"], (int, float))
                assert 0.0 <= conn["surprise_factor"] <= 1.0
                assert 0.0 <= conn["relevance"] <= 1.0
                assert conn["connection_type"] in ["cross_domain", "temporal", "contradictory", "emergent", "thematic", "developmental", "balancing"]
            
            # Validate meta pattern structure if any exist
            for pattern in result["meta_patterns"]:
                assert isinstance(pattern["pattern_name"], str)
                assert isinstance(pattern["description"], str)
                assert isinstance(pattern["evidence_count"], int)
                assert isinstance(pattern["confidence"], (int, float))
                assert 0.0 <= pattern["confidence"] <= 1.0
                assert pattern["evidence_count"] >= 1
            
        except Exception as e:
            pytest.fail(f"Real AI JSON validation failed: {e}")


class TestPerformanceScenarios:
    """Test performance-related scenarios"""
    
    def test_large_memory_processing_performance(self):
        """Test performance with large memory datasets"""
        service, mock_ai = TestMockAIScenarios().serendipity_service_with_mock_ai()
        
        # Create large memory dataset
        large_insights = []
        for i in range(100):
            large_insights.append({
                "content": f"Insight {i}: This is a test insight with some content to make it realistic",
                "category": f"category_{i % 10}",
                "confidence": 0.8,
                "tags": [f"tag_{i}", f"tag_{i+1}"],
                "timestamp": f"2024-01-{(i % 30) + 1:02d}T10:00:00Z"
            })
        
        large_memory_data = {
            "insights": large_insights,
            "conversation_summaries": [
                {
                    "summary": f"Conversation {i} about various topics",
                    "key_themes": [f"theme_{i}", f"theme_{i+1}"],
                    "timestamp": f"2024-01-{(i % 30) + 1:02d}T09:00:00Z"
                }
                for i in range(20)
            ],
            "metadata": {"total_insights": 100}
        }
        
        # Mock successful response
        mock_ai.chat.return_value = json.dumps({
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Large dataset processed",
            "recommendations": []
        })
        
        start_time = time.time()
        
        # Format the large memory
        formatted_memory = service._format_memory_for_analysis(large_memory_data)
        
        # Should handle large dataset efficiently
        if isinstance(formatted_memory, list):
            # Chunked processing
            result = service._discover_connections_chunked(formatted_memory)
        else:
            # Single processing
            result = service._discover_connections(formatted_memory)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result is not None
        assert processing_time < 30  # Should complete within reasonable time
        print(f"Large memory processing took {processing_time:.2f} seconds")
    
    def test_concurrent_analysis_requests(self):
        """Test handling of concurrent analysis requests"""
        service, mock_ai = TestMockAIScenarios().serendipity_service_with_mock_ai()
        
        # Mock response with slight delay
        def delayed_response(*args, **kwargs):
            time.sleep(0.1)  # Small delay to simulate processing
            return json.dumps({
                "connections": [],
                "meta_patterns": [],
                "serendipity_summary": "Concurrent test",
                "recommendations": []
            })
        
        mock_ai.chat.side_effect = delayed_response
        
        # Simulate concurrent requests
        import threading
        results = []
        errors = []
        
        def analyze_memory(memory_id):
            try:
                result = service._discover_connections(f"memory data {memory_id}")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_memory, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent analysis had errors: {errors}"
        assert len(results) == 5
        
        # All should have completed successfully
        for result in results:
            assert result is not None
            assert "Concurrent test" in result["serendipity_summary"]
    
    def test_memory_usage_with_caching(self):
        """Test memory usage patterns with caching enabled"""
        service, mock_ai = TestMockAIScenarios().serendipity_service_with_mock_ai()
        
        mock_ai.chat.return_value = json.dumps({
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Cache test",
            "recommendations": []
        })
        
        # Perform multiple analyses to populate cache
        for i in range(10):
            service._discover_connections(f"memory data {i}")
        
        # Check cache statistics
        cache_stats = service.get_cache_stats()
        
        assert cache_stats["analysis_cache"]["entries"] > 0
        assert cache_stats["analysis_cache"]["total_accesses"] >= 10
        
        # Test cache cleanup
        removed = service.cleanup_expired_cache()
        assert isinstance(removed, dict)
        assert "analysis" in removed


if __name__ == "__main__":
    # Run with different markers for different test types
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--integration":
        # Run integration tests with real AI
        pytest.main([__file__, "-v", "-m", "integration"])
    else:
        # Run mock tests by default
        pytest.main([__file__, "-v", "-m", "not integration"])