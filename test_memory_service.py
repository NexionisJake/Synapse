"""
Unit tests for Memory Service Module

This module contains comprehensive tests for the memory processing and
insight generation functionality.
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

from memory_service import MemoryService, MemoryServiceError, get_memory_service, reset_memory_service


class TestMemoryService(unittest.TestCase):
    """Test cases for MemoryService class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary directory for test files within project
        self.test_dir = os.path.join(os.getcwd(), 'test_temp')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_memory_file = os.path.join(self.test_dir, 'test_memory.json')
        
        # Sample conversation data for testing
        self.sample_conversation = [
            {"role": "user", "content": "I'm really interested in machine learning and AI"},
            {"role": "assistant", "content": "That's fascinating! What aspects of ML interest you most?"},
            {"role": "user", "content": "I love working with neural networks and deep learning"},
            {"role": "assistant", "content": "Deep learning is such an exciting field. Are you working on any projects?"}
        ]
        
        # Sample AI response for insight extraction
        self.sample_ai_response = {
            "insights": [
                {
                    "category": "interests",
                    "content": "User has strong interest in machine learning and AI",
                    "confidence": 0.9,
                    "tags": ["machine_learning", "AI", "technology"],
                    "evidence": "I'm really interested in machine learning and AI"
                },
                {
                    "category": "technical_skills",
                    "content": "User has experience with neural networks and deep learning",
                    "confidence": 0.8,
                    "tags": ["neural_networks", "deep_learning", "technical"],
                    "evidence": "I love working with neural networks and deep learning"
                }
            ],
            "conversation_summary": "Discussion about user's interest in machine learning and AI",
            "key_themes": ["machine_learning", "AI", "deep_learning"]
        }
        
        # Reset global memory service instance
        reset_memory_service()
    
    def tearDown(self):
        """Clean up after each test method"""
        # Remove temporary directory and all its contents
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        reset_memory_service()
    
    def test_memory_service_initialization(self):
        """Test MemoryService initialization"""
        service = MemoryService(model="test-model", memory_file=self.test_memory_file)
        
        self.assertEqual(service.model, "test-model")
        self.assertEqual(service.memory_file, self.test_memory_file)
        self.assertIsNotNone(service.insight_prompt)
        self.assertIn("JSON", service.insight_prompt)
    
    def test_format_conversation_for_analysis(self):
        """Test conversation formatting for AI analysis"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        formatted = service._format_conversation_for_analysis(self.sample_conversation)
        
        self.assertIn("User: I'm really interested in machine learning and AI", formatted)
        self.assertIn("Assistant: That's fascinating!", formatted)
        self.assertIn("User: I love working with neural networks", formatted)
        self.assertIn("Assistant: Deep learning is such an exciting field", formatted)
    
    @patch('memory_service.ollama.chat')
    def test_extract_insights_success(self, mock_chat):
        """Test successful insight extraction"""
        # Mock the AI response
        mock_chat.return_value = {
            'message': {
                'content': json.dumps(self.sample_ai_response)
            }
        }
        
        service = MemoryService(memory_file=self.test_memory_file)
        result = service.extract_insights(self.sample_conversation)
        
        # Verify the result structure
        self.assertIn('insights', result)
        self.assertIn('conversation_summary', result)
        self.assertIn('key_themes', result)
        self.assertIn('extraction_metadata', result)
        
        # Verify insights have timestamps
        for insight in result['insights']:
            self.assertIn('timestamp', insight)
            self.assertIn('source_conversation_length', insight)
        
        # Verify AI was called correctly
        mock_chat.assert_called_once()
        call_args = mock_chat.call_args
        self.assertEqual(call_args[1]['model'], 'llama3:8b')
        self.assertEqual(len(call_args[1]['messages']), 2)
    
    @patch('memory_service.ollama.chat')
    def test_extract_insights_invalid_json(self, mock_chat):
        """Test insight extraction with invalid JSON response"""
        # Mock invalid JSON response
        mock_chat.return_value = {
            'message': {
                'content': 'This is not valid JSON'
            }
        }
        
        service = MemoryService(memory_file=self.test_memory_file)
        
        with self.assertRaises(MemoryServiceError) as context:
            service.extract_insights(self.sample_conversation)
        
        self.assertIn("invalid JSON", str(context.exception))
    
    @patch('memory_service.ollama.chat')
    def test_extract_insights_missing_insights_field(self, mock_chat):
        """Test insight extraction with missing insights field"""
        # Mock response without insights field
        mock_chat.return_value = {
            'message': {
                'content': json.dumps({"summary": "test"})
            }
        }
        
        service = MemoryService(memory_file=self.test_memory_file)
        
        with self.assertRaises(MemoryServiceError) as context:
            service.extract_insights(self.sample_conversation)
        
        self.assertIn("missing 'insights' field", str(context.exception))
    
    def test_load_memory_file_new_file(self):
        """Test loading memory file when file doesn't exist"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        data = service._load_memory_file()
        
        self.assertIn('insights', data)
        self.assertIn('conversation_summaries', data)
        self.assertIn('metadata', data)
        self.assertEqual(len(data['insights']), 0)
        self.assertEqual(len(data['conversation_summaries']), 0)
    
    def test_load_memory_file_existing_file(self):
        """Test loading existing memory file"""
        # Create test memory file
        test_data = {
            'insights': [{'test': 'insight'}],
            'conversation_summaries': [{'test': 'summary'}],
            'metadata': {'total_insights': 1}
        }
        
        with open(self.test_memory_file, 'w') as f:
            json.dump(test_data, f)
        
        service = MemoryService(memory_file=self.test_memory_file)
        data = service._load_memory_file()
        
        self.assertEqual(len(data['insights']), 1)
        self.assertEqual(len(data['conversation_summaries']), 1)
        self.assertEqual(data['metadata']['total_insights'], 1)
    
    def test_load_memory_file_corrupted_json(self):
        """Test loading corrupted memory file"""
        # Create corrupted JSON file
        with open(self.test_memory_file, 'w') as f:
            f.write('{"invalid": json}')
        
        service = MemoryService(memory_file=self.test_memory_file)
        data = service._load_memory_file()
        
        # Should return empty structure and backup corrupted file
        self.assertEqual(len(data['insights']), 0)
        # Check that a backup file was created (with timestamp)
        backup_files = [f for f in os.listdir(self.test_dir) if 'corrupted' in f or 'backup' in f]
        self.assertTrue(len(backup_files) > 0, "Backup file should have been created")
    
    def test_save_memory_file(self):
        """Test saving memory file"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        test_data = {
            'insights': [{'test': 'insight'}],
            'metadata': {'total_insights': 1}
        }
        
        service._save_memory_file(test_data)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.test_memory_file))
        
        with open(self.test_memory_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['insights'][0]['test'], 'insight')
        self.assertEqual(saved_data['metadata']['total_insights'], 1)
    
    def test_save_insights(self):
        """Test saving insights to memory file"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        service.save_insights(self.sample_ai_response)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.test_memory_file))
        
        # Load and verify data
        with open(self.test_memory_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data['insights']), 2)
        self.assertEqual(len(saved_data['conversation_summaries']), 1)
        self.assertIn('metadata', saved_data)
        self.assertEqual(saved_data['metadata']['total_insights'], 2)
    
    def test_save_insights_append_to_existing(self):
        """Test appending insights to existing memory file"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        # Save initial insights
        service.save_insights(self.sample_ai_response)
        
        # Save additional insights
        additional_insights = {
            "insights": [
                {
                    "category": "goals",
                    "content": "User wants to learn more about AI",
                    "confidence": 0.7,
                    "tags": ["learning", "goals"],
                    "evidence": "What aspects of ML interest you most?"
                }
            ],
            "conversation_summary": "Follow-up discussion about AI learning goals",
            "key_themes": ["learning", "goals"]
        }
        
        service.save_insights(additional_insights)
        
        # Verify data was appended
        with open(self.test_memory_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data['insights']), 3)  # 2 + 1
        self.assertEqual(len(saved_data['conversation_summaries']), 2)
        self.assertEqual(saved_data['metadata']['total_insights'], 3)
    
    def test_get_memory_stats(self):
        """Test getting memory statistics"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        # Save some test data
        service.save_insights(self.sample_ai_response)
        
        stats = service.get_memory_stats()
        
        self.assertEqual(stats['total_insights'], 2)
        self.assertEqual(stats['total_conversations'], 1)
        self.assertIn('categories', stats)
        self.assertIn('confidence_distribution', stats)
        self.assertTrue(stats['memory_file_exists'])
        self.assertGreater(stats['memory_file_size'], 0)
    
    def test_get_memory_stats_empty_file(self):
        """Test getting memory statistics with no data"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        stats = service.get_memory_stats()
        
        self.assertEqual(stats['total_insights'], 0)
        self.assertEqual(stats['total_conversations'], 0)
        self.assertFalse(stats['memory_file_exists'])
        self.assertEqual(stats['memory_file_size'], 0)
    
    @patch('memory_service.ollama.chat')
    def test_process_conversation_complete_workflow(self, mock_chat):
        """Test complete conversation processing workflow"""
        # Mock the AI response
        mock_chat.return_value = {
            'message': {
                'content': json.dumps(self.sample_ai_response)
            }
        }
        
        service = MemoryService(memory_file=self.test_memory_file)
        result = service.process_conversation(self.sample_conversation)
        
        # Verify result structure
        self.assertTrue(result['success'])
        self.assertEqual(result['insights_extracted'], 2)
        self.assertIn('conversation_summary', result)
        self.assertIn('key_themes', result)
        self.assertIn('memory_stats', result)
        self.assertIn('timestamp', result)
        
        # Verify file was created and contains data
        self.assertTrue(os.path.exists(self.test_memory_file))
        
        with open(self.test_memory_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data['insights']), 2)


class TestMemoryServiceGlobalFunctions(unittest.TestCase):
    """Test cases for global memory service functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        reset_memory_service()
    
    def tearDown(self):
        """Clean up after tests"""
        reset_memory_service()
    
    def test_get_memory_service_singleton(self):
        """Test that get_memory_service returns singleton instance"""
        service1 = get_memory_service()
        service2 = get_memory_service()
        
        self.assertIs(service1, service2)
    
    def test_get_memory_service_with_parameters(self):
        """Test get_memory_service with custom parameters"""
        service = get_memory_service(model="custom-model", memory_file="custom.json")
        
        self.assertEqual(service.model, "custom-model")
        self.assertEqual(service.memory_file, "custom.json")
    
    def test_reset_memory_service(self):
        """Test resetting global memory service instance"""
        service1 = get_memory_service()
        reset_memory_service()
        service2 = get_memory_service()
        
        self.assertIsNot(service1, service2)


class TestMemoryServiceIntegration(unittest.TestCase):
    """Integration tests for memory service with file system operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.join(os.getcwd(), 'test_temp_integration')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_memory_file = os.path.join(self.test_dir, 'integration_memory.json')
        reset_memory_service()
    
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        reset_memory_service()
    
    @patch('memory_service.ollama.chat')
    def test_multiple_conversation_processing(self, mock_chat):
        """Test processing multiple conversations and accumulating insights"""
        # Mock AI responses for multiple conversations
        responses = [
            {
                "insights": [{"category": "interests", "content": "User likes AI", "confidence": 0.9, "tags": ["AI"], "evidence": "test"}],
                "conversation_summary": "AI discussion",
                "key_themes": ["AI"]
            },
            {
                "insights": [{"category": "skills", "content": "User codes Python", "confidence": 0.8, "tags": ["Python"], "evidence": "test"}],
                "conversation_summary": "Python discussion",
                "key_themes": ["Python"]
            }
        ]
        
        mock_chat.side_effect = [
            {'message': {'content': json.dumps(responses[0])}},
            {'message': {'content': json.dumps(responses[1])}}
        ]
        
        service = MemoryService(memory_file=self.test_memory_file)
        
        # Process first conversation
        conversation1 = [
            {"role": "user", "content": "I love AI"},
            {"role": "assistant", "content": "That's great!"}
        ]
        result1 = service.process_conversation(conversation1)
        
        # Process second conversation
        conversation2 = [
            {"role": "user", "content": "I code in Python"},
            {"role": "assistant", "content": "Python is awesome!"}
        ]
        result2 = service.process_conversation(conversation2)
        
        # Verify accumulation
        self.assertEqual(result1['insights_extracted'], 1)
        self.assertEqual(result2['insights_extracted'], 1)
        self.assertEqual(result2['memory_stats']['total_insights'], 2)
        self.assertEqual(result2['memory_stats']['total_conversations'], 2)
    
    def test_file_backup_on_save(self):
        """Test that backup files are created when saving"""
        service = MemoryService(memory_file=self.test_memory_file)
        
        # Create initial file
        initial_data = {"insights": [{"test": "initial"}]}
        service._save_memory_file(initial_data)
        
        # Save new data (should create backup)
        new_data = {"insights": [{"test": "updated"}]}
        service._save_memory_file(new_data)
        
        # Verify backup exists
        backup_file = f"{self.test_memory_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
        
        # Verify backup contains original data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        self.assertEqual(backup_data['insights'][0]['test'], 'initial')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)