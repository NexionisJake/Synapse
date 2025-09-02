"""
Comprehensive tests for AI analysis engine with advanced prompt engineering
Tests for Task 4: Implement AI analysis engine with advanced prompt engineering
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from serendipity_service import SerendipityService, SerendipityServiceError, InsufficientDataError
from ai_service import AIServiceError
from config import get_config


# Global fixtures for all test classes
@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
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
    return config

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    ai_service = Mock()
    ai_service.chat = Mock()
    return ai_service

@pytest.fixture
def serendipity_service(mock_config, mock_ai_service):
    """Create serendipity service with mocked dependencies"""
    with patch('serendipity_service.get_ai_service', return_value=mock_ai_service):
        service = SerendipityService(config=mock_config)
        service.ai_service = mock_ai_service
        return service

@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "insights": [
            {
                "content": "Learning programming requires consistent practice and patience",
                "category": "learning",
                "confidence": 0.9,
                "tags": ["programming", "practice"],
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "content": "Cooking is similar to programming - both require following recipes/algorithms",
                "category": "analogy",
                "confidence": 0.8,
                "tags": ["cooking", "programming"],
                "timestamp": "2024-01-02T10:00:00Z"
            },
            {
                "content": "Time management is crucial for productivity in any domain",
                "category": "productivity",
                "confidence": 0.85,
                "tags": ["time", "productivity"],
                "timestamp": "2024-01-03T10:00:00Z"
            }
        ],
        "conversation_summaries": [
            {
                "summary": "Discussion about learning methodologies and their effectiveness",
                "key_themes": ["learning", "methodology", "effectiveness"],
                "timestamp": "2024-01-01T09:00:00Z"
            },
            {
                "summary": "Conversation about work-life balance and time management strategies",
                "key_themes": ["balance", "time management", "strategies"],
                "timestamp": "2024-01-02T09:00:00Z"
            }
        ],
        "metadata": {
            "total_insights": 3,
            "last_updated": "2024-01-03T10:00:00Z"
        }
    }

@pytest.fixture
def valid_ai_response():
    """Valid AI response for testing"""
    return json.dumps({
        "connections": [
            {
                "title": "Learning-Cooking Systematic Approach",
                "description": "Both programming and cooking require systematic approaches with step-by-step processes",
                "surprise_factor": 0.8,
                "relevance": 0.9,
                "connected_insights": ["Learning programming requires consistent practice", "Cooking is similar to programming"],
                "connection_type": "cross_domain",
                "actionable_insight": "Apply cooking techniques to improve programming learning"
            }
        ],
        "meta_patterns": [
            {
                "pattern_name": "Systematic Learning",
                "description": "Consistent pattern of applying systematic approaches across domains",
                "evidence_count": 2,
                "confidence": 0.85
            }
        ],
        "serendipity_summary": "Analysis reveals strong patterns of systematic thinking across different domains",
        "recommendations": [
            "Explore more cross-domain connections",
            "Document systematic approaches you use"
        ]
    })


class TestAIAnalysisEngine:
    """Test suite for AI analysis engine functionality"""
    pass


class TestPromptEngineering:
    """Test advanced prompt engineering functionality"""
    
    def test_serendipity_system_prompt_contains_examples(self, serendipity_service):
        """Test that system prompt includes examples for better AI guidance"""
        prompt = serendipity_service._get_serendipity_system_prompt()
        
        # Check for example sections
        assert "EXAMPLES OF GOOD CONNECTIONS:" in prompt
        assert "systematic experimentation" in prompt.lower()
        assert "cross-domain:" in prompt.lower()
        assert "temporal:" in prompt.lower()
        assert "emergent:" in prompt.lower()
        
        # Check for specific guidance
        assert "surprise_factor" in prompt
        assert "relevance" in prompt
        assert "connected_insights" in prompt
        assert "actionable_insight" in prompt
        
        # Check for JSON format requirements
        assert "CRITICAL: Return ONLY valid JSON" in prompt
        assert "No additional text before or after" in prompt
    
    def test_prompt_includes_connection_types(self, serendipity_service):
        """Test that prompt includes all connection types"""
        prompt = serendipity_service._get_serendipity_system_prompt()
        
        connection_types = ["cross_domain", "temporal", "contradictory", "emergent", "thematic"]
        for conn_type in connection_types:
            assert conn_type in prompt
    
    def test_prompt_specifies_numeric_ranges(self, serendipity_service):
        """Test that prompt specifies valid numeric ranges"""
        prompt = serendipity_service._get_serendipity_system_prompt()
        
        assert "0.0 and 1.0" in prompt
        assert "3-7 connections" in prompt


class TestJSONExtractionAndValidation:
    """Test JSON extraction and validation functionality"""
    
    def test_extract_json_from_clean_response(self, serendipity_service, valid_ai_response):
        """Test JSON extraction from clean AI response"""
        result = serendipity_service._extract_json_from_response(valid_ai_response)
        
        assert result is not None
        assert "connections" in result
        assert "meta_patterns" in result
        assert len(result["connections"]) == 1
    
    def test_extract_json_with_extra_text(self, serendipity_service, valid_ai_response):
        """Test JSON extraction when response has extra text"""
        response_with_text = f"Here's my analysis:\n\n{valid_ai_response}\n\nThat's the complete analysis."
        
        result = serendipity_service._extract_json_from_response(response_with_text)
        
        assert result is not None
        assert "connections" in result
    
    def test_extract_json_from_code_blocks(self, serendipity_service, valid_ai_response):
        """Test JSON extraction from markdown code blocks"""
        response_with_code_blocks = f"```json\n{valid_ai_response}\n```"
        
        result = serendipity_service._extract_json_from_response(response_with_code_blocks)
        
        assert result is not None
        assert "connections" in result
    
    def test_json_recovery_with_trailing_commas(self, serendipity_service):
        """Test JSON recovery when response has trailing commas"""
        malformed_json = """{
            "connections": [
                {
                    "title": "Test Connection",
                    "description": "Test description",
                    "surprise_factor": 0.8,
                }
            ],
            "meta_patterns": [],
            "serendipity_summary": "Test summary",
            "recommendations": ["Test recommendation",]
        }"""
        
        result = serendipity_service._attempt_json_recovery_strategies(malformed_json)
        
        assert result is not None
        assert "connections" in result
    
    def test_validate_and_clean_connections(self, serendipity_service):
        """Test connection validation and cleaning"""
        raw_connection = {
            "title": "Test Connection with Very Long Title That Exceeds Normal Length Limits",
            "description": "Test description",
            "surprise_factor": 1.5,  # Out of range
            "relevance": -0.2,  # Out of range
            "connected_insights": ["insight1", "insight2"],
            "connection_type": "invalid_type",
            "actionable_insight": "Test insight"
        }
        
        cleaned = serendipity_service._validate_and_clean_connection(raw_connection, 0)
        
        assert cleaned is not None
        assert len(cleaned["title"]) <= 60
        assert 0.0 <= cleaned["surprise_factor"] <= 1.0
        assert 0.0 <= cleaned["relevance"] <= 1.0
        assert cleaned["connection_type"] == "emergent"  # Default for invalid type
    
    def test_validate_and_clean_meta_patterns(self, serendipity_service):
        """Test meta pattern validation and cleaning"""
        raw_pattern = {
            "pattern_name": "Test Pattern",
            "description": "Test description",
            "evidence_count": "invalid",  # Should be converted to int
            "confidence": 2.0  # Out of range
        }
        
        cleaned = serendipity_service._validate_and_clean_meta_pattern(raw_pattern, 0)
        
        assert cleaned is not None
        assert isinstance(cleaned["evidence_count"], int)
        assert cleaned["evidence_count"] >= 1
        assert 0.0 <= cleaned["confidence"] <= 1.0
    
    def test_fallback_response_creation(self, serendipity_service):
        """Test fallback response creation for failed parsing"""
        error_message = "Test error message"
        
        fallback = serendipity_service._create_fallback_response(error_message)
        
        assert "connections" in fallback
        assert "meta_patterns" in fallback
        assert "serendipity_summary" in fallback
        assert "recommendations" in fallback
        assert error_message in fallback["serendipity_summary"]
        assert len(fallback["recommendations"]) > 0


class TestTimeoutAndRetryMechanisms:
    """Test timeout handling and retry mechanisms"""
    
    def test_regular_analysis_timeout(self, serendipity_service, mock_ai_service):
        """Test timeout handling in regular analysis"""
        # Mock AI service to simulate long response
        def slow_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow response
            return "test response"
        
        mock_ai_service.chat.side_effect = slow_response
        serendipity_service.analysis_timeout = 0.05  # Very short timeout
        
        conversation = [{"role": "user", "content": "test"}]
        
        with pytest.raises(AIServiceError, match="timed out"):
            serendipity_service._handle_regular_analysis(conversation, time.time())
    
    def test_streaming_analysis_timeout(self, serendipity_service, mock_ai_service):
        """Test timeout handling in streaming analysis"""
        # Mock streaming response that times out
        def slow_stream(*args, **kwargs):
            yield {"content": "start", "done": False}
            time.sleep(0.1)  # Simulate slow stream
            yield {"content": "end", "done": True}
        
        mock_ai_service.chat.side_effect = slow_stream
        serendipity_service.analysis_timeout = 0.05  # Very short timeout
        
        conversation = [{"role": "user", "content": "test"}]
        
        with pytest.raises(AIServiceError, match="timed out"):
            serendipity_service._handle_streaming_analysis(conversation, time.time())
    
    def test_retry_mechanism_success_on_second_attempt(self, serendipity_service, mock_ai_service, valid_ai_response):
        """Test retry mechanism succeeds on second attempt"""
        # First call fails, second succeeds
        mock_ai_service.chat.side_effect = [
            AIServiceError("First attempt fails"),
            valid_ai_response
        ]
        
        formatted_memory = "test memory data"
        
        result = serendipity_service._discover_connections(formatted_memory)
        
        assert result is not None
        assert "connections" in result
        assert mock_ai_service.chat.call_count == 2
    
    def test_retry_mechanism_exhausted(self, serendipity_service, mock_ai_service):
        """Test retry mechanism when all attempts fail"""
        # All attempts fail
        mock_ai_service.chat.side_effect = AIServiceError("All attempts fail")
        
        formatted_memory = "test memory data"
        
        result = serendipity_service._discover_connections(formatted_memory)
        
        # Should return fallback response instead of raising exception
        assert result is not None
        assert "error" in result["serendipity_summary"] or "failed" in result["serendipity_summary"].lower()
        assert mock_ai_service.chat.call_count == 3  # Max retries
    
    def test_exponential_backoff_timing(self, serendipity_service, mock_ai_service):
        """Test that retry delays follow exponential backoff"""
        mock_ai_service.chat.side_effect = AIServiceError("Always fails")
        
        start_time = time.time()
        serendipity_service._discover_connections("test memory")
        end_time = time.time()
        
        # Should have delays: 2s, 3s (2*1.5) = ~5s total minimum
        # Allow some tolerance for test execution time
        assert end_time - start_time >= 4.5


class TestResponseCachingAndStreaming:
    """Test response caching and streaming capabilities"""
    
    def test_analysis_result_caching(self, serendipity_service, mock_ai_service, valid_ai_response):
        """Test that analysis results are cached"""
        mock_ai_service.chat.return_value = valid_ai_response
        
        formatted_memory = "test memory data"
        
        # First call
        result1 = serendipity_service._discover_connections(formatted_memory)
        
        # Second call should use cache
        result2 = serendipity_service._discover_connections(formatted_memory)
        
        assert result1 == result2
        assert mock_ai_service.chat.call_count == 1  # Only called once due to caching
    
    def test_cache_expiration(self, serendipity_service, mock_ai_service, valid_ai_response):
        """Test that expired cache entries are not used"""
        mock_ai_service.chat.return_value = valid_ai_response
        serendipity_service.analysis_cache_ttl = 0.1  # Very short TTL
        
        formatted_memory = "test memory data"
        
        # First call
        serendipity_service._discover_connections(formatted_memory)
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Second call should not use expired cache
        serendipity_service._discover_connections(formatted_memory)
        
        assert mock_ai_service.chat.call_count == 2
    
    def test_streaming_analysis_for_large_memory(self, serendipity_service, mock_ai_service):
        """Test that streaming is used for large memory datasets"""
        # Mock streaming response
        def mock_stream(*args, **kwargs):
            if kwargs.get('stream'):
                yield {"content": "partial", "done": False}
                yield {"content": " response", "done": False}
                yield {"content": "", "done": True, "full_content": "partial response"}
            else:
                return "non-streaming response"
        
        mock_ai_service.chat.side_effect = mock_stream
        
        # Large memory data should trigger streaming
        large_memory = "x" * 6000  # Larger than 5000 char threshold
        
        result = serendipity_service._discover_connections(large_memory, enable_streaming=True)
        
        # Should have attempted streaming
        assert mock_ai_service.chat.called
        call_args = mock_ai_service.chat.call_args
        assert call_args[1].get('stream') is True
    
    def test_streaming_error_handling(self, serendipity_service, mock_ai_service):
        """Test error handling in streaming analysis"""
        # Mock streaming response with error
        def mock_stream_with_error(*args, **kwargs):
            yield {"content": "start", "done": False}
            yield {"error": "Stream error occurred", "done": True}
        
        mock_ai_service.chat.side_effect = mock_stream_with_error
        
        conversation = [{"role": "user", "content": "test"}]
        
        with pytest.raises(AIServiceError, match="Stream error occurred"):
            serendipity_service._handle_streaming_analysis(conversation, time.time())
    
    def test_cache_key_generation(self, serendipity_service):
        """Test cache key generation for analysis results"""
        memory1 = "test memory data 1"
        memory2 = "test memory data 2"
        
        key1 = serendipity_service._generate_analysis_cache_key(memory1)
        key2 = serendipity_service._generate_analysis_cache_key(memory2)
        key3 = serendipity_service._generate_analysis_cache_key(memory1)  # Same as key1
        
        assert key1 != key2  # Different content should have different keys
        assert key1 == key3  # Same content should have same key
        assert len(key1) == 32  # MD5 hash length


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    def test_complete_analysis_workflow_success(self, serendipity_service, mock_ai_service, sample_memory_data, valid_ai_response):
        """Test complete successful analysis workflow"""
        mock_ai_service.chat.return_value = valid_ai_response
        
        with patch('serendipity_service.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = 1000
            mock_path.return_value.stat.return_value.st_mtime = time.time()
            
            with patch('builtins.open', mock_open_with_json(sample_memory_data)):
                result = serendipity_service.analyze_memory()
        
        assert result is not None
        assert "connections" in result
        assert "meta_patterns" in result
        assert "metadata" in result
        assert result["metadata"]["model_used"] == "llama3:8b"
    
    def test_analysis_with_insufficient_data(self, serendipity_service):
        """Test analysis with insufficient data"""
        insufficient_data = {
            "insights": [{"content": "Only one insight", "category": "test"}],
            "conversation_summaries": [],
            "metadata": {}
        }
        
        with patch('serendipity_service.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = 100
            mock_path.return_value.stat.return_value.st_mtime = time.time()
            
            with patch('builtins.open', mock_open_with_json(insufficient_data)):
                with pytest.raises(InsufficientDataError):
                    serendipity_service.analyze_memory()
    
    def test_analysis_with_ai_service_unavailable(self, serendipity_service):
        """Test analysis when AI service is unavailable"""
        serendipity_service.ai_service = None
        
        with pytest.raises(SerendipityServiceError, match="AI service is not available"):
            serendipity_service.analyze_memory()
    
    def test_analysis_with_malformed_ai_response(self, serendipity_service, mock_ai_service, sample_memory_data):
        """Test analysis with malformed AI response"""
        mock_ai_service.chat.return_value = "This is not JSON at all"
        
        with patch('serendipity_service.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = 1000
            mock_path.return_value.stat.return_value.st_mtime = time.time()
            
            with patch('builtins.open', mock_open_with_json(sample_memory_data)):
                result = serendipity_service.analyze_memory()
        
        # Should return fallback response instead of failing
        assert result is not None
        assert "connections" in result
        assert "Could not extract valid JSON" in result["serendipity_summary"]


def mock_open_with_json(json_data):
    """Helper function to mock file opening with JSON data"""
    import io
    return lambda *args, **kwargs: io.StringIO(json.dumps(json_data))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])