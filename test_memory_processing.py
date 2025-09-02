"""
Comprehensive unit tests for enhanced memory data processing in SerendipityService

Tests cover:
- Memory data validation with edge cases
- Data formatting with chunking support
- Multi-level caching with TTL management
- Insufficient data detection
- Large dataset handling
"""

import json
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serendipity_service import (
    SerendipityService, 
    SerendipityServiceError,
    InsufficientDataError,
    DataValidationError,
    MemoryProcessingError,
    ValidationResult,
    MemoryChunk,
    CacheEntry
)
from config import get_config


class TestMemoryDataValidation:
    """Test comprehensive memory data validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = Mock()
        self.config.ENABLE_SERENDIPITY_ENGINE = True
        self.config.SERENDIPITY_MIN_INSIGHTS = 3
        self.config.SERENDIPITY_MAX_MEMORY_SIZE_MB = 10
        self.config.SERENDIPITY_ANALYSIS_TIMEOUT = 30
        self.config.OLLAMA_MODEL = "llama3:8b"
        self.config.MEMORY_FILE = "test_memory.json"
        self.config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
        self.config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
        self.config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
        
        with patch('serendipity_service.get_ai_service'):
            self.service = SerendipityService(config=self.config)
    
    def test_validate_valid_memory_data(self):
        """Test validation of valid memory data"""
        memory_data = {
            "insights": [
                {
                    "category": "test",
                    "content": "Test insight content",
                    "confidence": 0.8,
                    "tags": ["tag1", "tag2"],
                    "timestamp": "2025-01-01T10:00:00"
                },
                {
                    "category": "another",
                    "content": "Another test insight",
                    "confidence": 0.9
                },
                {
                    "category": "third",
                    "content": "Third insight for minimum requirement"
                }
            ],
            "conversation_summaries": [
                {
                    "summary": "Test conversation summary",
                    "key_themes": ["theme1", "theme2"],
                    "timestamp": "2025-01-01T11:00:00",
                    "insights_count": 2
                }
            ],
            "metadata": {
                "total_insights": 3,
                "last_updated": "2025-01-01T12:00:00"
            }
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.insights_count == 3
        assert result.conversations_count == 1
        assert len(result.categories) == 3
        assert result.total_content_length > 0
    
    def test_validate_insufficient_data(self):
        """Test validation with insufficient data"""
        memory_data = {
            "insights": [
                {"category": "test", "content": "Only one insight"}
            ],
            "conversation_summaries": [],
            "metadata": {}
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        assert not result.is_valid
        assert any("insufficient data" in error.lower() for error in result.errors)
        assert result.insights_count == 1
        assert result.conversations_count == 0
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields"""
        memory_data = {
            "insights": [
                {"category": "test"},  # Missing content
                {"content": "Test content"},  # Missing category
                {"category": "", "content": ""},  # Empty fields
                {"category": "valid", "content": "Valid insight"}
            ],
            "conversation_summaries": [
                {"key_themes": ["theme"]},  # Missing summary
                {"summary": ""},  # Empty summary
                {"summary": "Valid summary"}
            ],
            "metadata": {}
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        # Should have errors for missing content, category, and summary fields
        error_text = " ".join(result.errors)
        assert "missing required field" in error_text.lower()
    
    def test_validate_invalid_data_types(self):
        """Test validation with invalid data types"""
        memory_data = {
            "insights": "not a list",  # Should be list
            "conversation_summaries": [
                {"summary": 123}  # Summary should be string
            ],
            "metadata": "not a dict"  # Should be dict
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        assert not result.is_valid
        assert "'insights' must be a list" in result.errors
        assert "'conversation_summaries' must be a list" in result.errors
    
    def test_validate_confidence_values(self):
        """Test validation of confidence values"""
        memory_data = {
            "insights": [
                {"category": "test", "content": "Test 1", "confidence": 1.5},  # Out of range
                {"category": "test", "content": "Test 2", "confidence": -0.1},  # Out of range
                {"category": "test", "content": "Test 3", "confidence": "invalid"},  # Invalid type
                {"category": "test", "content": "Test 4", "confidence": 0.8}  # Valid
            ],
            "conversation_summaries": [],
            "metadata": {}
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        # Should have warnings about confidence values
        warning_text = " ".join(result.warnings)
        assert "confidence out of range" in warning_text or "confidence must be a number" in warning_text
    
    def test_validate_timestamps(self):
        """Test validation of timestamp formats"""
        memory_data = {
            "insights": [
                {"category": "test", "content": "Test 1", "timestamp": "invalid-timestamp"},
                {"category": "test", "content": "Test 2", "timestamp": "2025-01-01T10:00:00"},
                {"category": "test", "content": "Test 3", "timestamp": 12345}  # Invalid type
            ],
            "conversation_summaries": [
                {"summary": "Test summary", "timestamp": "2025-01-01T11:00:00"}
            ],
            "metadata": {}
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        # Should have warnings about invalid timestamps
        warning_text = " ".join(result.warnings)
        assert "invalid timestamp" in warning_text.lower() or "timestamp should be" in warning_text.lower()
    
    def test_validate_content_length_warnings(self):
        """Test warnings for content length issues"""
        memory_data = {
            "insights": [
                {"category": "test", "content": "x" * 1500},  # Very long content
                {"category": "test", "content": "short"},  # Very short content
                {"category": "test", "content": "Normal length content for testing"}
            ],
            "conversation_summaries": [
                {"summary": "x" * 2500},  # Very long summary
                {"summary": "short"}  # Very short summary
            ],
            "metadata": {}
        }
        
        result = self.service._validate_memory_data_comprehensive(memory_data)
        
        # Should have warnings about content length
        warning_text = " ".join(result.warnings)
        assert "very long" in warning_text.lower() or "very short" in warning_text.lower()


class TestMemoryDataLoading:
    """Test memory data loading with error handling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = Mock()
        self.config.ENABLE_SERENDIPITY_ENGINE = True
        self.config.SERENDIPITY_MIN_INSIGHTS = 3
        self.config.SERENDIPITY_MAX_MEMORY_SIZE_MB = 10
        self.config.MEMORY_FILE = "test_memory.json"
        self.config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
        self.config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
        self.config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
        self.config.OLLAMA_MODEL = "llama3:8b"
        
        with patch('serendipity_service.get_ai_service'):
            self.service = SerendipityService(config=self.config)
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent memory file"""
        with pytest.raises(SerendipityServiceError) as exc_info:
            self.service._load_memory_data("nonexistent_file.json")
        
        assert "not found" in str(exc_info.value)
    
    def test_load_empty_file(self):
        """Test loading empty memory file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create empty file
            pass
        
        try:
            with pytest.raises(SerendipityServiceError) as exc_info:
                self.service._load_memory_data(f.name)
            
            assert "empty" in str(exc_info.value)
        finally:
            Path(f.name).unlink()
    
    def test_load_invalid_json(self):
        """Test loading file with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json, content}')
        
        try:
            # Should attempt recovery and return minimal structure
            result = self.service._load_memory_data(f.name)
            
            # Should have basic structure after recovery
            assert "insights" in result
            assert "conversation_summaries" in result
            assert isinstance(result["insights"], list)
            assert isinstance(result["conversation_summaries"], list)
        finally:
            Path(f.name).unlink()
    
    def test_load_valid_json_file(self):
        """Test loading valid JSON file"""
        test_data = {
            "insights": [
                {"category": "test", "content": "Test insight 1"},
                {"category": "test", "content": "Test insight 2"},
                {"category": "test", "content": "Test insight 3"}
            ],
            "conversation_summaries": [
                {"summary": "Test conversation"}
            ],
            "metadata": {"total_insights": 3}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
        
        try:
            result = self.service._load_memory_data(f.name)
            
            assert result == test_data
        finally:
            Path(f.name).unlink()
    
    def test_json_recovery_trailing_commas(self):
        """Test JSON recovery for trailing commas"""
        invalid_json = '{"insights": [{"category": "test", "content": "test",}], "metadata": {},}'
        
        recovered = self.service._attempt_json_recovery(invalid_json, "test.json")
        
        assert recovered is not None
        assert "insights" in recovered
        assert len(recovered["insights"]) == 1
    
    def test_json_recovery_partial_content(self):
        """Test JSON recovery for partial content"""
        invalid_json = 'some prefix {"insights": [], "conversation_summaries": []} some suffix'
        
        recovered = self.service._attempt_json_recovery(invalid_json, "test.json")
        
        assert recovered is not None
        assert "insights" in recovered
        assert "conversation_summaries" in recovered
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
        
        try:
            key1 = self.service._generate_memory_cache_key(f.name)
            key2 = self.service._generate_memory_cache_key(f.name)
            
            # Same file should generate same key
            assert key1 == key2
            assert len(key1) == 32  # MD5 hash length
        finally:
            Path(f.name).unlink()


class TestMemoryFormatting:
    """Test memory data formatting with chunking"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = Mock()
        self.config.ENABLE_SERENDIPITY_ENGINE = True
        self.config.SERENDIPITY_MIN_INSIGHTS = 3
        self.config.SERENDIPITY_MAX_CHUNK_SIZE = 1000  # Small chunk size for testing
        self.config.SERENDIPITY_CHUNK_OVERLAP = 50
        self.config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
        self.config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
        self.config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
        self.config.OLLAMA_MODEL = "llama3:8b"
        
        with patch('serendipity_service.get_ai_service'):
            self.service = SerendipityService(config=self.config)
            self.service.max_chunk_size_chars = 1000
    
    def test_format_small_memory_data(self):
        """Test formatting small memory data (no chunking needed)"""
        memory_data = {
            "insights": [
                {"category": "test", "content": "Test insight 1", "confidence": 0.8},
                {"category": "test", "content": "Test insight 2", "tags": ["tag1", "tag2"]}
            ],
            "conversation_summaries": [
                {"summary": "Test conversation", "key_themes": ["theme1"]}
            ],
            "metadata": {"total_insights": 2}
        }
        
        result = self.service._format_memory_for_analysis(memory_data)
        
        assert isinstance(result, str)
        assert "=== INSIGHTS AND KNOWLEDGE ===" in result
        assert "=== CONVERSATION SUMMARIES ===" in result
        assert "=== MEMORY METADATA ===" in result
        assert "Test insight 1" in result
        assert "Test conversation" in result
    
    def test_format_large_memory_data_chunking(self):
        """Test formatting large memory data that requires chunking"""
        # Create large memory data
        insights = []
        for i in range(20):
            insights.append({
                "category": f"category_{i % 5}",
                "content": f"This is a long test insight number {i} with substantial content " * 10,
                "confidence": 0.8,
                "tags": [f"tag_{i}", f"tag_{i+1}"]
            })
        
        memory_data = {
            "insights": insights,
            "conversation_summaries": [
                {"summary": "Long conversation summary " * 20, "key_themes": ["theme1", "theme2"]}
            ],
            "metadata": {"total_insights": len(insights)}
        }
        
        result = self.service._format_memory_for_analysis(memory_data)
        
        # Should return chunks for large data
        assert isinstance(result, list)
        assert all(isinstance(chunk, MemoryChunk) for chunk in result)
        assert len(result) > 1  # Should be split into multiple chunks
        
        # Check chunk properties
        for chunk in result:
            assert chunk.chunk_id.startswith("chunk_")
            assert len(chunk.content) <= self.service.max_chunk_size_chars + 500  # Allow some overflow
            assert chunk.size_bytes > 0
            assert isinstance(chunk.metadata, dict)
    
    def test_format_insights_section(self):
        """Test insights section formatting"""
        insights = [
            {
                "category": "technical",
                "content": "Technical insight 1",
                "confidence": 0.9,
                "tags": ["tech", "programming"],
                "timestamp": "2025-01-01T10:00:00"
            },
            {
                "category": "personal",
                "content": "Personal insight 1",
                "confidence": 0.7,
                "tags": ["personal"]
            },
            {
                "category": "technical",
                "content": "Technical insight 2",
                "confidence": 0.8
            }
        ]
        
        result = self.service._format_insights_section(insights)
        
        assert "=== INSIGHTS AND KNOWLEDGE ===" in result
        assert "TECHNICAL (2 insights" in result
        assert "PERSONAL (1 insights" in result
        assert "Technical insight 1" in result
        assert "confidence: 0.9" in result
        assert "tags: tech, programming" in result
    
    def test_format_conversations_section(self):
        """Test conversations section formatting"""
        conversations = [
            {
                "summary": "Recent conversation",
                "key_themes": ["theme1", "theme2"],
                "timestamp": "2025-01-02T10:00:00",
                "insights_count": 3
            },
            {
                "summary": "Older conversation",
                "timestamp": "2025-01-01T10:00:00",
                "insights_count": 1
            }
        ]
        
        result = self.service._format_conversations_section(conversations)
        
        assert "=== CONVERSATION SUMMARIES ===" in result
        assert "Recent conversation" in result
        assert "Key themes: theme1, theme2" in result
        assert "Date: 2025-01-02" in result
        assert "Insights generated: 3" in result
    
    def test_chunk_metadata_extraction(self):
        """Test chunk metadata extraction"""
        chunk_content = """=== INSIGHTS AND KNOWLEDGE ===

TECHNICAL (3 insights):
• Technical insight 1
• Technical insight 2

PERSONAL (1 insights):
• Personal insight 1

=== CONVERSATION SUMMARIES ===

Conversation 1: Test conversation
"""
        
        memory_data = {"insights": [], "conversation_summaries": []}
        metadata = self.service._extract_chunk_metadata(chunk_content, memory_data)
        
        assert metadata["has_insights"]
        assert metadata["has_conversations"]
        assert not metadata["has_metadata"]
        assert metadata["content_length"] == len(chunk_content)
        assert len(metadata["categories"]) > 0
    
    def test_count_insights_in_chunk(self):
        """Test counting insights in chunk"""
        chunk_content = """=== INSIGHTS AND KNOWLEDGE ===

TECHNICAL:
• First insight
• Second insight
• Third insight

PERSONAL:
• Fourth insight
"""
        
        count = self.service._count_insights_in_chunk(chunk_content)
        assert count == 4
    
    def test_count_conversations_in_chunk(self):
        """Test counting conversations in chunk"""
        chunk_content = """=== CONVERSATION SUMMARIES ===

Conversation 1: First conversation
Conversation 2: Second conversation
Conversation 3: Third conversation
"""
        
        count = self.service._count_conversations_in_chunk(chunk_content)
        assert count == 3


class TestCaching:
    """Test multi-level caching functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = Mock()
        self.config.ENABLE_SERENDIPITY_ENGINE = True
        self.config.SERENDIPITY_MEMORY_CACHE_TTL = 1  # 1 second for testing
        self.config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1
        self.config.SERENDIPITY_FORMATTED_CACHE_TTL = 1
        self.config.OLLAMA_MODEL = "llama3:8b"
        
        with patch('serendipity_service.get_ai_service'):
            self.service = SerendipityService(config=self.config)
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration"""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(seconds=2),
            ttl_seconds=1
        )
        
        assert entry.is_expired()
        
        fresh_entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now(),
            ttl_seconds=10
        )
        
        assert not fresh_entry.is_expired()
    
    def test_cache_entry_access(self):
        """Test cache entry access counting"""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now(),
            ttl_seconds=10
        )
        
        assert entry.access_count == 0
        
        data = entry.access()
        assert data == {"test": "data"}
        assert entry.access_count == 1
        
        entry.access()
        assert entry.access_count == 2
    
    def test_memory_cache_hit_miss(self):
        """Test memory cache hit and miss"""
        test_data = {
            "insights": [{"category": "test", "content": "Test insight"}],
            "conversation_summaries": [],
            "metadata": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
        
        try:
            # First load - cache miss
            result1 = self.service._load_memory_data(f.name)
            assert result1 == test_data
            
            # Second load - cache hit
            result2 = self.service._load_memory_data(f.name)
            assert result2 == test_data
            
            # Cache should have one entry
            stats = self.service.get_cache_stats()
            assert stats["memory_cache"]["entries"] == 1
            assert stats["memory_cache"]["total_accesses"] >= 1
        finally:
            Path(f.name).unlink()
    
    def test_cache_expiration_cleanup(self):
        """Test cache expiration and cleanup"""
        # Add entry to cache manually
        cache_key = "test_key"
        expired_entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(seconds=2),
            ttl_seconds=1
        )
        
        with self.service._cache_lock:
            self.service._memory_cache[cache_key] = expired_entry
        
        # Clean up expired entries
        removed = self.service.cleanup_expired_cache()
        
        assert removed["memory"] == 1
        assert cache_key not in self.service._memory_cache
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Add entries to all caches
        with self.service._cache_lock:
            self.service._memory_cache["key1"] = CacheEntry({"data": 1}, datetime.now(), 10)
            self.service._analysis_cache["key2"] = CacheEntry({"data": 2}, datetime.now(), 10)
            self.service._formatted_cache["key3"] = CacheEntry({"data": 3}, datetime.now(), 10)
        
        # Clear all caches
        cleared = self.service.clear_cache()
        
        assert cleared["memory"] == 1
        assert cleared["analysis"] == 1
        assert cleared["formatted"] == 1
        
        # All caches should be empty
        assert len(self.service._memory_cache) == 0
        assert len(self.service._analysis_cache) == 0
        assert len(self.service._formatted_cache) == 0
    
    def test_clear_specific_cache(self):
        """Test clearing specific cache type"""
        # Add entries to all caches
        with self.service._cache_lock:
            self.service._memory_cache["key1"] = CacheEntry({"data": 1}, datetime.now(), 10)
            self.service._analysis_cache["key2"] = CacheEntry({"data": 2}, datetime.now(), 10)
            self.service._formatted_cache["key3"] = CacheEntry({"data": 3}, datetime.now(), 10)
        
        # Clear only memory cache
        cleared = self.service.clear_cache("memory")
        
        assert cleared["memory"] == 1
        assert "analysis" not in cleared
        assert "formatted" not in cleared
        
        # Only memory cache should be empty
        assert len(self.service._memory_cache) == 0
        assert len(self.service._analysis_cache) == 1
        assert len(self.service._formatted_cache) == 1
    
    def test_cache_stats(self):
        """Test cache statistics"""
        # Add entries with different access patterns
        entry1 = CacheEntry({"data": 1}, datetime.now(), 10)
        entry1.access()  # Access once
        
        entry2 = CacheEntry({"data": 2}, datetime.now() - timedelta(seconds=2), 1)  # Expired
        
        with self.service._cache_lock:
            self.service._memory_cache["key1"] = entry1
            self.service._memory_cache["key2"] = entry2
        
        stats = self.service.get_cache_stats()
        
        assert stats["memory_cache"]["entries"] == 2
        assert stats["memory_cache"]["expired"] == 1
        assert stats["memory_cache"]["total_accesses"] == 1


class TestChunkedAnalysis:
    """Test chunked analysis functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = Mock()
        self.config.ENABLE_SERENDIPITY_ENGINE = True
        self.config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
        self.config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
        self.config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
        self.config.OLLAMA_MODEL = "llama3:8b"
        
        with patch('serendipity_service.get_ai_service'):
            self.service = SerendipityService(config=self.config)
            
            # Mock AI service
            self.service.ai_service = Mock()
    
    def test_deduplicate_connections(self):
        """Test connection deduplication"""
        connections = [
            {
                "title": "Machine Learning Patterns",
                "description": "Description 1",
                "relevance": 0.9,
                "surprise_factor": 0.8
            },
            {
                "title": "ML Patterns in Code",  # Similar to first
                "description": "Description 2",
                "relevance": 0.7,
                "surprise_factor": 0.6
            },
            {
                "title": "Completely Different Topic",
                "description": "Description 3",
                "relevance": 0.8,
                "surprise_factor": 0.9
            }
        ]
        
        unique = self.service._deduplicate_connections(connections)
        
        # Should keep the highest scoring similar connection and the different one
        assert len(unique) == 2
        titles = [conn["title"] for conn in unique]
        assert "Machine Learning Patterns" in titles
        assert "Completely Different Topic" in titles
    
    def test_deduplicate_meta_patterns(self):
        """Test meta pattern deduplication"""
        patterns = [
            {
                "pattern_name": "Learning Progression",
                "description": "Description 1",
                "confidence": 0.9,
                "evidence_count": 5
            },
            {
                "pattern_name": "Learning Progress Pattern",  # Similar to first
                "description": "Description 2",
                "confidence": 0.7,
                "evidence_count": 3
            },
            {
                "pattern_name": "Social Interaction",
                "description": "Description 3",
                "confidence": 0.8,
                "evidence_count": 4
            }
        ]
        
        unique = self.service._deduplicate_meta_patterns(patterns)
        
        # Should keep the highest scoring similar pattern and the different one
        assert len(unique) == 2
        names = [pattern["pattern_name"] for pattern in unique]
        assert "Learning Progression" in names
        assert "Social Interaction" in names
    
    def test_title_similarity_calculation(self):
        """Test title similarity calculation"""
        # Identical titles
        assert self.service._calculate_title_similarity("test title", "test title") == 1.0
        
        # Completely different titles
        assert self.service._calculate_title_similarity("machine learning", "cooking recipes") == 0.0
        
        # Similar titles
        similarity = self.service._calculate_title_similarity("machine learning patterns", "ML patterns analysis")
        assert 0.0 < similarity < 1.0
        
        # Empty titles
        assert self.service._calculate_title_similarity("", "test") == 0.0
        assert self.service._calculate_title_similarity("", "") == 0.0
    
    def test_merge_chunked_results(self):
        """Test merging results from multiple chunks"""
        connections = [
            {"title": "Connection 1", "relevance": 0.9, "surprise_factor": 0.8},
            {"title": "Connection 2", "relevance": 0.7, "surprise_factor": 0.6}
        ]
        
        patterns = [
            {"pattern_name": "Pattern 1", "confidence": 0.9, "evidence_count": 5}
        ]
        
        chunk_summaries = [
            {"chunk_id": "chunk_1", "connections_found": 1, "patterns_found": 1},
            {"chunk_id": "chunk_2", "connections_found": 1, "patterns_found": 0}
        ]
        
        result = self.service._merge_chunked_results(connections, patterns, chunk_summaries)
        
        assert "connections" in result
        assert "meta_patterns" in result
        assert "serendipity_summary" in result
        assert "recommendations" in result
        assert "chunk_analysis" in result
        
        chunk_analysis = result["chunk_analysis"]
        assert chunk_analysis["chunks_processed"] == 2
        assert chunk_analysis["total_connections_found"] == 2
        assert chunk_analysis["total_patterns_found"] == 1
    
    def test_generate_cross_chunk_recommendations(self):
        """Test cross-chunk recommendation generation"""
        # Test with many connections
        many_connections = [{"title": f"Connection {i}"} for i in range(15)]
        recommendations = self.service._generate_cross_chunk_recommendations(
            many_connections, [], []
        )
        
        assert any("rich interconnections" in rec for rec in recommendations)
        
        # Test with few connections
        few_connections = [{"title": "Connection 1"}]
        recommendations = self.service._generate_cross_chunk_recommendations(
            few_connections, [], []
        )
        
        assert any("limited connections" in rec.lower() for rec in recommendations)
        
        # Test with high confidence patterns
        high_conf_patterns = [{"pattern_name": "Pattern 1", "confidence": 0.9}]
        recommendations = self.service._generate_cross_chunk_recommendations(
            [], high_conf_patterns, []
        )
        
        assert any("strong recurring patterns" in rec for rec in recommendations)


class TestLargeDatasetHandling:
    """Test handling of large datasets"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = Mock()
        self.config.ENABLE_SERENDIPITY_ENGINE = True
        self.config.SERENDIPITY_MIN_INSIGHTS = 3
        self.config.SERENDIPITY_MAX_MEMORY_SIZE_MB = 1  # Small limit for testing
        self.config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
        self.config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
        self.config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
        self.config.OLLAMA_MODEL = "llama3:8b"
        
        with patch('serendipity_service.get_ai_service'):
            self.service = SerendipityService(config=self.config)
    
    def test_large_file_warning(self):
        """Test warning for large memory files"""
        # Create large test data
        large_data = {
            "insights": [
                {"category": f"cat_{i}", "content": "x" * 1000}
                for i in range(1000)
            ],
            "conversation_summaries": [],
            "metadata": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_data, f)
        
        try:
            # Should log warning but still load
            with patch('serendipity_service.logger') as mock_logger:
                result = self.service._load_memory_from_file(f.name)
                
                # Check that warning was logged
                mock_logger.warning.assert_called()
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if "large" in str(call).lower()]
                assert len(warning_calls) > 0
                
                # Data should still be loaded
                assert len(result["insights"]) == 1000
        finally:
            Path(f.name).unlink()
    
    def test_memory_chunking_for_large_data(self):
        """Test that large memory data gets chunked"""
        # Create data that will exceed chunk size
        large_insights = []
        for i in range(50):
            large_insights.append({
                "category": f"category_{i % 10}",
                "content": f"This is insight number {i} with substantial content. " * 20,
                "confidence": 0.8
            })
        
        memory_data = {
            "insights": large_insights,
            "conversation_summaries": [
                {"summary": "Long conversation summary. " * 50}
            ],
            "metadata": {"total_insights": len(large_insights)}
        }
        
        # Set small chunk size to force chunking
        self.service.max_chunk_size_chars = 2000
        
        result = self.service._format_memory_data(memory_data)
        
        # Should return chunks for large data
        assert isinstance(result, list)
        assert len(result) > 1
        assert all(isinstance(chunk, MemoryChunk) for chunk in result)
        
        # Verify chunk sizes are reasonable
        for chunk in result:
            assert len(chunk.content) <= self.service.max_chunk_size_chars + 1000  # Allow some overflow
            assert chunk.insights_count >= 0
            assert chunk.conversations_count >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])