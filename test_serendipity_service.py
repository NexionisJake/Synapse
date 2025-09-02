"""
Comprehensive Unit Tests for Serendipity Service

This module contains unit tests for all SerendipityService functionality including
data loading, validation, AI analysis, error handling, and integration scenarios.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Import the modules to test
from serendipity_service import (
    SerendipityService, 
    SerendipityServiceError,
    get_serendipity_service,
    reset_serendipity_service
)
from config import get_config
from error_handler import ErrorCategory, ErrorSeverity

class TestSerendipityService(unittest.TestCase):
    """Test cases for SerendipityService class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Reset global instance
        reset_serendipity_service()
        
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.ENABLE_SERENDIPITY_ENGINE = True
        self.mock_config.OLLAMA_MODEL = "llama3:8b"
        self.mock_config.MEMORY_FILE = "test_memory.json"
        
        # Create test memory data
        self.test_memory_data = {
            "insights": [
                {
                    "category": "interests",
                    "content": "User is interested in machine learning",
                    "confidence": 0.9,
                    "tags": ["AI", "ML"],
                    "evidence": "I love working with ML models",
                    "timestamp": "2025-01-01T10:00:00"
                },
                {
                    "category": "skills",
                    "content": "User has Python programming experience",
                    "confidence": 0.8,
                    "tags": ["programming", "Python"],
                    "evidence": "I've been coding in Python for 2 years",
                    "timestamp": "2025-01-01T11:00:00"
                },
                {
                    "category": "goals",
                    "content": "User wants to build AI applications",
                    "confidence": 0.85,
                    "tags": ["career", "AI"],
                    "evidence": "My goal is to create useful AI apps",
                    "timestamp": "2025-01-01T12:00:00"
                }
            ],
            "conversation_summaries": [
                {
                    "summary": "Discussion about machine learning career paths",
                    "key_themes": ["career", "ML", "education"],
                    "timestamp": "2025-01-01T10:00:00"
                },
                {
                    "summary": "Conversation about Python frameworks for AI",
                    "key_themes": ["Python", "frameworks", "AI"],
                    "timestamp": "2025-01-01T11:00:00"
                }
            ],
            "metadata": {
                "total_insights": 3,
                "last_updated": "2025-01-01T12:00:00"
            }
        }
        
        # Create test AI response
        self.test_ai_response = """{
            "connections": [
                {
                    "title": "ML Career-Skills Alignment",
                    "description": "Strong connection between ML interest and Python skills",
                    "surprise_factor": 0.3,
                    "relevance": 0.9,
                    "connected_insights": ["ML interest", "Python skills"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Focus on ML libraries in Python"
                }
            ],
            "meta_patterns": [
                {
                    "pattern_name": "Technical Career Focus",
                    "description": "Consistent focus on technical skills and AI career",
                    "evidence_count": 3,
                    "confidence": 0.85
                }
            ],
            "serendipity_summary": "Strong alignment between interests and skills",
            "recommendations": ["Build ML portfolio", "Learn advanced Python libraries"]
        }"""
    
    def tearDown(self):
        """Clean up after each test method"""
        reset_serendipity_service()
    
    @patch('serendipity_service.get_ai_service')
    def test_initialization_success(self, mock_get_ai_service):
        """Test successful service initialization"""
        mock_ai_service = Mock()
        mock_get_ai_service.return_value = mock_ai_service
        
        service = SerendipityService(config=self.mock_config)
        
        self.assertIsNotNone(service)
        self.assertEqual(service.config, self.mock_config)
        self.assertEqual(service.ai_service, mock_ai_service)
        self.assertEqual(service.min_insights_required, 3)
    
    def test_initialization_disabled_service(self):
        """Test initialization when service is disabled"""
        self.mock_config.ENABLE_SERENDIPITY_ENGINE = False
        
        service = SerendipityService(config=self.mock_config)
        
        self.assertIsNone(service.ai_service)
    
    @patch('serendipity_service.get_ai_service')
    def test_initialization_ai_service_failure(self, mock_get_ai_service):
        """Test initialization when AI service fails"""
        mock_get_ai_service.side_effect = Exception("AI service unavailable")
        
        service = SerendipityService(config=self.mock_config)
        
        self.assertIsNone(service.ai_service)
    
    def test_get_serendipity_system_prompt(self):
        """Test serendipity system prompt generation"""
        service = SerendipityService(config=self.mock_config)
        prompt = service._get_serendipity_system_prompt()
        
        self.assertIsInstance(prompt, str)
        self.assertIn("serendipitous insights", prompt)
        self.assertIn("JSON format", prompt)
        self.assertIn("connections", prompt)
    
    def test_load_memory_data_success(self):
        """Test successful memory data loading"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_memory_data, f)
            temp_file = f.name
        
        try:
            service = SerendipityService(config=self.mock_config)
            memory_data = service._load_memory_data(temp_file)
            
            self.assertEqual(memory_data, self.test_memory_data)
            self.assertIn("insights", memory_data)
            self.assertIn("conversation_summaries", memory_data)
        finally:
            os.unlink(temp_file)
    
    def test_load_memory_data_file_not_found(self):
        """Test memory data loading when file doesn't exist"""
        service = SerendipityService(config=self.mock_config)
        
        with self.assertRaises(SerendipityServiceError) as context:
            service._load_memory_data("nonexistent_file_that_should_not_exist.json")
        
        self.assertIn("not found", str(context.exception).lower())
    
    def test_load_memory_data_invalid_json(self):
        """Test memory data loading with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            service = SerendipityService(config=self.mock_config)
            
            # Should not raise exception due to recovery mechanism
            # Instead it should recover with empty data
            memory_data = service._load_memory_data(temp_file)
            self.assertEqual(memory_data["insights"], [])
            self.assertEqual(memory_data["conversation_summaries"], [])
        finally:
            # Clean up both original and backup files
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            # Clean up any backup files created during recovery
            import glob
            for backup_file in glob.glob(f"{temp_file}.corrupted.*"):
                os.unlink(backup_file)
    
    def test_load_memory_data_missing_keys(self):
        """Test memory data loading with missing required keys"""
        incomplete_data = {"some_other_key": "value"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(incomplete_data, f)
            temp_file = f.name
        
        try:
            service = SerendipityService(config=self.mock_config)
            memory_data = service._load_memory_data(temp_file)
            
            # Should add missing keys with empty lists
            self.assertIn("insights", memory_data)
            self.assertIn("conversation_summaries", memory_data)
            self.assertEqual(memory_data["insights"], [])
            self.assertEqual(memory_data["conversation_summaries"], [])
        finally:
            os.unlink(temp_file)
    
    def test_validate_memory_data_success(self):
        """Test successful memory data validation"""
        service = SerendipityService(config=self.mock_config)
        
        # Should not raise exception
        service._validate_memory_data(self.test_memory_data)
    
    def test_validate_memory_data_insufficient_data(self):
        """Test memory data validation with insufficient data"""
        insufficient_data = {
            "insights": [{"content": "single insight", "category": "test"}],
            "conversation_summaries": []
        }
        
        service = SerendipityService(config=self.mock_config)
        
        with self.assertRaises(SerendipityServiceError) as context:
            service._validate_memory_data(insufficient_data)
        
        self.assertIn("Insufficient data", str(context.exception))
    
    def test_validate_memory_data_malformed_insights(self):
        """Test memory data validation with malformed insights"""
        malformed_data = {
            "insights": [
                "not a dict",
                {"content": "valid insight", "category": "test"},
                {"category": "missing content"}  # Missing content field
            ],
            "conversation_summaries": [
                {"summary": "test conversation"}
            ]
        }
        
        service = SerendipityService(config=self.mock_config)
        
        # Should not raise exception but log warnings
        service._validate_memory_data(malformed_data)
    
    def test_format_memory_for_analysis(self):
        """Test memory data formatting for AI analysis"""
        service = SerendipityService(config=self.mock_config)
        formatted = service._format_memory_for_analysis(self.test_memory_data)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("INSIGHTS AND KNOWLEDGE", formatted)
        self.assertIn("CONVERSATION SUMMARIES", formatted)
        self.assertIn("machine learning", formatted)
        self.assertIn("Python programming", formatted)
    
    def test_format_memory_empty_data(self):
        """Test memory formatting with empty data"""
        empty_data = {"insights": [], "conversation_summaries": []}
        
        service = SerendipityService(config=self.mock_config)
        formatted = service._format_memory_for_analysis(empty_data)
        
        self.assertIsInstance(formatted, str)
        # Should handle empty data gracefully
    
    @patch('serendipity_service.get_ai_service')
    def test_discover_connections_success(self, mock_get_ai_service):
        """Test successful connection discovery"""
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = self.test_ai_response
        mock_get_ai_service.return_value = mock_ai_service
        
        service = SerendipityService(config=self.mock_config)
        formatted_memory = "test memory content"
        
        results = service._discover_connections(formatted_memory)
        
        self.assertIn("connections", results)
        self.assertIn("meta_patterns", results)
        self.assertIn("serendipity_summary", results)
        self.assertIn("recommendations", results)
        self.assertEqual(len(results["connections"]), 1)
    
    @patch('serendipity_service.get_ai_service')
    def test_discover_connections_ai_failure(self, mock_get_ai_service):
        """Test connection discovery when AI fails"""
        mock_ai_service = Mock()
        mock_ai_service.chat.side_effect = Exception("AI service error")
        mock_get_ai_service.return_value = mock_ai_service
        
        service = SerendipityService(config=self.mock_config)
        formatted_memory = "test memory content"
        
        with self.assertRaises(SerendipityServiceError):
            service._discover_connections(formatted_memory)
    
    def test_parse_ai_response_success(self):
        """Test successful AI response parsing"""
        service = SerendipityService(config=self.mock_config)
        
        results = service._parse_ai_response(self.test_ai_response)
        
        self.assertIn("connections", results)
        self.assertIn("meta_patterns", results)
        self.assertEqual(len(results["connections"]), 1)
        self.assertEqual(results["connections"][0]["title"], "ML Career-Skills Alignment")
    
    def test_parse_ai_response_invalid_json(self):
        """Test AI response parsing with invalid JSON"""
        service = SerendipityService(config=self.mock_config)
        invalid_response = "This is not JSON at all"
        
        results = service._parse_ai_response(invalid_response)
        
        # Should return fallback response
        self.assertIn("connections", results)
        self.assertIn("error", results)
        self.assertEqual(results["connections"], [])
    
    def test_parse_ai_response_missing_keys(self):
        """Test AI response parsing with missing required keys"""
        incomplete_response = '{"connections": []}'
        
        service = SerendipityService(config=self.mock_config)
        results = service._parse_ai_response(incomplete_response)
        
        # Should add missing keys with defaults
        self.assertIn("meta_patterns", results)
        self.assertIn("serendipity_summary", results)
        self.assertIn("recommendations", results)
    
    def test_validate_connection_success(self):
        """Test successful connection validation"""
        valid_connection = {
            "title": "Test Connection",
            "description": "Test description",
            "surprise_factor": 0.8,
            "relevance": 0.9
        }
        
        service = SerendipityService(config=self.mock_config)
        result = service._validate_connection(valid_connection)
        
        self.assertTrue(result)
    
    def test_validate_connection_missing_fields(self):
        """Test connection validation with missing required fields"""
        invalid_connection = {"description": "Missing title"}
        
        service = SerendipityService(config=self.mock_config)
        result = service._validate_connection(invalid_connection)
        
        self.assertFalse(result)
    
    def test_validate_connection_invalid_numeric_values(self):
        """Test connection validation with invalid numeric values"""
        connection = {
            "title": "Test",
            "description": "Test",
            "surprise_factor": 1.5,  # Out of range
            "relevance": "invalid"   # Not numeric
        }
        
        service = SerendipityService(config=self.mock_config)
        result = service._validate_connection(connection)
        
        self.assertTrue(result)  # Should fix values and return True
        self.assertEqual(connection["surprise_factor"], 1.0)  # Clamped to valid range
        self.assertEqual(connection["relevance"], 0.5)  # Default value
    
    def test_validate_meta_pattern_success(self):
        """Test successful meta pattern validation"""
        valid_pattern = {
            "pattern_name": "Test Pattern",
            "description": "Test description",
            "confidence": 0.8,
            "evidence_count": 5
        }
        
        service = SerendipityService(config=self.mock_config)
        result = service._validate_meta_pattern(valid_pattern)
        
        self.assertTrue(result)
    
    def test_validate_meta_pattern_invalid_values(self):
        """Test meta pattern validation with invalid values"""
        pattern = {
            "pattern_name": "Test",
            "description": "Test",
            "confidence": 1.5,  # Out of range
            "evidence_count": -1  # Negative
        }
        
        service = SerendipityService(config=self.mock_config)
        result = service._validate_meta_pattern(pattern)
        
        self.assertTrue(result)  # Should fix values and return True
        self.assertEqual(pattern["confidence"], 1.0)  # Clamped
        self.assertEqual(pattern["evidence_count"], 0)  # Fixed to minimum
    
    def test_create_fallback_response(self):
        """Test fallback response creation"""
        service = SerendipityService(config=self.mock_config)
        error_msg = "Test error"
        
        response = service._create_fallback_response(error_msg)
        
        self.assertIn("connections", response)
        self.assertIn("meta_patterns", response)
        self.assertIn("error", response)
        self.assertEqual(response["error"], error_msg)
        self.assertEqual(response["connections"], [])
    
    @patch('serendipity_service.get_ai_service')
    def test_get_service_status(self, mock_get_ai_service):
        """Test service status retrieval"""
        mock_ai_service = Mock()
        mock_ai_service.test_connection.return_value = {"connected": True}
        mock_get_ai_service.return_value = mock_ai_service
        
        service = SerendipityService(config=self.mock_config)
        status = service.get_service_status()
        
        self.assertIn("enabled", status)
        self.assertIn("ai_service_available", status)
        self.assertIn("model", status)
        self.assertIn("timestamp", status)
        self.assertTrue(status["enabled"])
        self.assertTrue(status["ai_service_available"])
    
    def test_get_service_status_disabled(self):
        """Test service status when disabled"""
        self.mock_config.ENABLE_SERENDIPITY_ENGINE = False
        
        service = SerendipityService(config=self.mock_config)
        status = service.get_service_status()
        
        self.assertFalse(status["enabled"])
        self.assertFalse(status["ai_service_available"])
    
    @patch('serendipity_service.get_ai_service')
    def test_analyze_memory_full_workflow(self, mock_get_ai_service):
        """Test complete memory analysis workflow"""
        # Setup mocks
        mock_ai_service = Mock()
        mock_ai_service.chat.return_value = self.test_ai_response
        mock_get_ai_service.return_value = mock_ai_service
        
        # Create temporary memory file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_memory_data, f)
            temp_file = f.name
        
        try:
            service = SerendipityService(config=self.mock_config)
            results = service.analyze_memory(temp_file)
            
            # Verify results structure
            self.assertIn("connections", results)
            self.assertIn("meta_patterns", results)
            self.assertIn("serendipity_summary", results)
            self.assertIn("recommendations", results)
            self.assertIn("metadata", results)
            
            # Verify metadata
            metadata = results["metadata"]
            self.assertIn("analysis_timestamp", metadata)
            self.assertIn("model_used", metadata)
            self.assertIn("insights_analyzed", metadata)
            self.assertIn("analysis_duration", metadata)
            
            # Verify content
            self.assertEqual(len(results["connections"]), 1)
            self.assertEqual(metadata["insights_analyzed"], 3)
            
        finally:
            os.unlink(temp_file)
    
    def test_analyze_memory_service_disabled(self):
        """Test memory analysis when service is disabled"""
        self.mock_config.ENABLE_SERENDIPITY_ENGINE = False
        
        service = SerendipityService(config=self.mock_config)
        
        with self.assertRaises(SerendipityServiceError) as context:
            service.analyze_memory()
        
        self.assertIn("disabled", str(context.exception).lower())
    
    def test_analyze_memory_ai_service_unavailable(self):
        """Test memory analysis when AI service is unavailable"""
        service = SerendipityService(config=self.mock_config)
        service.ai_service = None  # Simulate unavailable AI service
        
        with self.assertRaises(SerendipityServiceError) as context:
            service.analyze_memory()
        
        self.assertIn("ai service", str(context.exception).lower())
    
    def test_global_service_instance(self):
        """Test global service instance management"""
        # First call should create instance
        service1 = get_serendipity_service(config=self.mock_config)
        self.assertIsNotNone(service1)
        
        # Second call should return same instance
        service2 = get_serendipity_service()
        self.assertIs(service1, service2)
        
        # Reset should clear instance
        reset_serendipity_service()
        service3 = get_serendipity_service(config=self.mock_config)
        self.assertIsNot(service1, service3)

class TestSerendipityServiceIntegration(unittest.TestCase):
    """Integration tests for SerendipityService with real components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        reset_serendipity_service()
        
        # Create realistic test data
        self.realistic_memory_data = {
            "insights": [
                {
                    "category": "interests",
                    "content": "User is passionate about sustainable technology and green energy solutions",
                    "confidence": 0.9,
                    "tags": ["sustainability", "technology", "environment"],
                    "evidence": "I'm really excited about solar panel innovations and electric vehicles",
                    "timestamp": "2025-01-15T10:30:00"
                },
                {
                    "category": "skills",
                    "content": "User has experience with data analysis and Python programming",
                    "confidence": 0.85,
                    "tags": ["programming", "data_science", "Python"],
                    "evidence": "I've been working with pandas and matplotlib for data visualization",
                    "timestamp": "2025-01-15T11:15:00"
                },
                {
                    "category": "goals",
                    "content": "User wants to combine technical skills with environmental impact",
                    "confidence": 0.8,
                    "tags": ["career", "environment", "impact"],
                    "evidence": "I'd love to work on projects that help fight climate change using data",
                    "timestamp": "2025-01-15T12:00:00"
                },
                {
                    "category": "experience",
                    "content": "User has worked on renewable energy research project",
                    "confidence": 0.75,
                    "tags": ["research", "renewable_energy", "academic"],
                    "evidence": "Last semester I did a project analyzing wind farm efficiency data",
                    "timestamp": "2025-01-15T14:30:00"
                },
                {
                    "category": "learning",
                    "content": "User is studying machine learning applications in environmental science",
                    "confidence": 0.9,
                    "tags": ["machine_learning", "environmental_science", "education"],
                    "evidence": "I'm taking a course on ML for climate modeling and prediction",
                    "timestamp": "2025-01-15T16:00:00"
                }
            ],
            "conversation_summaries": [
                {
                    "summary": "Discussion about career paths in environmental technology",
                    "key_themes": ["career", "environment", "technology", "impact"],
                    "timestamp": "2025-01-15T10:00:00"
                },
                {
                    "summary": "Conversation about data science tools and techniques",
                    "key_themes": ["data_science", "Python", "tools", "learning"],
                    "timestamp": "2025-01-15T11:00:00"
                },
                {
                    "summary": "Talk about renewable energy research and opportunities",
                    "key_themes": ["research", "renewable_energy", "opportunities", "academic"],
                    "timestamp": "2025-01-15T14:00:00"
                }
            ],
            "metadata": {
                "total_insights": 5,
                "last_updated": "2025-01-15T16:00:00"
            }
        }
    
    def test_realistic_memory_formatting(self):
        """Test memory formatting with realistic data"""
        config = Mock()
        config.ENABLE_SERENDIPITY_ENGINE = True
        config.OLLAMA_MODEL = "llama3:8b"
        
        service = SerendipityService(config=config)
        formatted = service._format_memory_for_analysis(self.realistic_memory_data)
        
        # Verify comprehensive formatting
        self.assertIn("INTERESTS:", formatted)
        self.assertIn("SKILLS:", formatted)
        self.assertIn("GOALS:", formatted)
        self.assertIn("sustainable technology", formatted)
        self.assertIn("Python programming", formatted)
        self.assertIn("CONVERSATION SUMMARIES", formatted)
        self.assertIn("environmental technology", formatted)
        
        # Verify structure and length
        self.assertGreater(len(formatted), 1000)  # Should be substantial
        self.assertIn("confidence:", formatted)
        self.assertIn("tags:", formatted)
    
    def test_error_handling_with_realistic_scenarios(self):
        """Test error handling with realistic error scenarios"""
        config = Mock()
        config.ENABLE_SERENDIPITY_ENGINE = True
        config.OLLAMA_MODEL = "llama3:8b"
        config.MEMORY_FILE = "nonexistent_file_for_testing.json"
        
        service = SerendipityService(config=config)
        
        # Test file not found scenario
        with self.assertRaises(SerendipityServiceError) as context:
            service._load_memory_data()
        
        self.assertIn("not found", str(context.exception).lower())
    
    def test_large_memory_data_handling(self):
        """Test handling of large memory datasets"""
        # Create large dataset
        large_insights = []
        for i in range(100):
            large_insights.append({
                "category": f"category_{i % 10}",
                "content": f"This is insight number {i} with substantial content that represents real user insights",
                "confidence": 0.7 + (i % 3) * 0.1,
                "tags": [f"tag_{i % 5}", f"tag_{(i+1) % 5}"],
                "evidence": f"Evidence for insight {i} with detailed explanation",
                "timestamp": f"2025-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00"
            })
        
        large_memory_data = {
            "insights": large_insights,
            "conversation_summaries": [
                {
                    "summary": f"Conversation {i} about various topics",
                    "key_themes": [f"theme_{i % 3}", f"theme_{(i+1) % 3}"],
                    "timestamp": f"2025-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00"
                }
                for i in range(20)
            ],
            "metadata": {
                "total_insights": 100,
                "last_updated": "2025-01-31T23:59:59"
            }
        }
        
        config = Mock()
        config.ENABLE_SERENDIPITY_ENGINE = True
        config.OLLAMA_MODEL = "llama3:8b"
        
        service = SerendipityService(config=config)
        
        # Should handle large data without errors
        formatted = service._format_memory_for_analysis(large_memory_data)
        self.assertIsInstance(formatted, str)
        self.assertGreater(len(formatted), 10000)  # Should be very large
        
        # Validation should pass
        service._validate_memory_data(large_memory_data)

if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    # Run tests
    unittest.main(verbosity=2)