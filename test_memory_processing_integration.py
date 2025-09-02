"""
Integration test for memory processing with real data
"""

import pytest
from unittest.mock import Mock, patch
from serendipity_service import SerendipityService, ValidationResult


def test_real_memory_processing():
    """Test memory processing with real memory.json file"""
    config = Mock()
    config.ENABLE_SERENDIPITY_ENGINE = True
    config.SERENDIPITY_MIN_INSIGHTS = 3
    config.SERENDIPITY_MAX_MEMORY_SIZE_MB = 10
    config.MEMORY_FILE = "memory.json"
    config.SERENDIPITY_MEMORY_CACHE_TTL = 3600
    config.SERENDIPITY_ANALYSIS_CACHE_TTL = 1800
    config.SERENDIPITY_FORMATTED_CACHE_TTL = 1800
    config.SERENDIPITY_MAX_CHUNK_SIZE = 3000  # Smaller to trigger chunking
    config.SERENDIPITY_CHUNK_OVERLAP = 200
    config.OLLAMA_MODEL = "llama3:8b"
    
    with patch('serendipity_service.get_ai_service'):
        service = SerendipityService(config=config)
        
        # Test loading real memory data
        memory_data = service._load_memory_data("memory.json")
        
        assert "insights" in memory_data
        assert "conversation_summaries" in memory_data
        assert len(memory_data["insights"]) > 0
        
        print(f"Loaded {len(memory_data['insights'])} insights and {len(memory_data['conversation_summaries'])} conversations")
        
        # Test validation
        validation_result = service._validate_memory_data_comprehensive(memory_data)
        
        print(f"Validation result: {validation_result.is_valid}")
        print(f"Insights: {validation_result.insights_count}")
        print(f"Conversations: {validation_result.conversations_count}")
        print(f"Categories: {validation_result.categories}")
        print(f"Errors: {validation_result.errors}")
        print(f"Warnings: {validation_result.warnings}")
        
        # Test formatting
        formatted_result = service._format_memory_for_analysis(memory_data)
        
        if isinstance(formatted_result, str):
            print(f"Formatted as single string: {len(formatted_result)} characters")
        else:
            print(f"Formatted as {len(formatted_result)} chunks")
            for i, chunk in enumerate(formatted_result):
                print(f"  Chunk {i+1}: {len(chunk.content)} chars, {chunk.insights_count} insights, {chunk.conversations_count} conversations")


if __name__ == "__main__":
    test_real_memory_processing()