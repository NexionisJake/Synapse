#!/usr/bin/env python3
"""
Comprehensive Error Handling and User Experience Tests

This module tests all error handling paths and user experience flows
for the serendipity analysis feature, ensuring robust error recovery
and user-friendly guidance.
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock, Mock
from flask import Flask
from app import app
from serendipity_service import (
    SerendipityService, SerendipityServiceError, InsufficientDataError,
    DataValidationError, MemoryProcessingError
)
import os
import tempfile


class TestErrorHandlingAndUX(unittest.TestCase):
    """Test comprehensive error handling and user experience optimization"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Set up test environment variables
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        os.environ['OLLAMA_MODEL'] = 'llama3:8b'
        os.environ['SERENDIPITY_MIN_INSIGHTS'] = '3'
        
        # Create temporary memory file for testing
        self.temp_memory_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_memory_file.close()
        os.environ['MEMORY_FILE'] = self.temp_memory_file.name
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary file
        if os.path.exists(self.temp_memory_file.name):
            os.unlink(self.temp_memory_file.name)
    
    def create_test_memory_data(self, insights_count=5, conversations_count=3):
        """Create test memory data with specified counts"""
        insights = []
        for i in range(insights_count):
            insights.append({
                "content": f"Test insight {i+1} about various topics and ideas",
                "category": f"category_{i % 3}",
                "confidence": 0.8,
                "tags": [f"tag{i}", f"topic{i}"],
                "evidence": f"Evidence for insight {i+1}",
                "timestamp": "2024-01-01T10:00:00Z"
            })
        
        conversations = []
        for i in range(conversations_count):
            conversations.append({
                "summary": f"Conversation {i+1} summary with meaningful content",
                "key_themes": [f"theme{i}", f"topic{i}"],
                "timestamp": "2024-01-01T10:00:00Z",
                "insights_count": 2
            })
        
        return {
            "insights": insights,
            "conversation_summaries": conversations,
            "metadata": {
                "total_insights": insights_count,
                "last_updated": "2024-01-01T10:00:00Z"
            }
        }
    
    def write_memory_file(self, data):
        """Write data to temporary memory file"""
        with open(self.temp_memory_file.name, 'w') as f:
            json.dump(data, f)
    
    # Test 1: Insufficient Data Error Handling
    def test_insufficient_data_error_handling(self):
        """Test handling of insufficient data scenarios with user guidance"""
        # Create memory with insufficient data
        insufficient_data = self.create_test_memory_data(insights_count=1, conversations_count=1)
        self.write_memory_file(insufficient_data)
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        # Verify error structure
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('timestamp', data)
        
        # Verify user-friendly message
        message = data['message'].lower()
        self.assertTrue(
            any(keyword in message for keyword in ['insufficient', 'not enough', 'more conversations']),
            f"Message should contain guidance about insufficient data: {data['message']}"
        )
    
    # Test 2: Network and Connection Error Simulation
    @patch('serendipity_service.get_ai_service')
    def test_network_error_handling(self, mock_get_ai_service):
        """Test handling of network and connection errors"""
        # Create sufficient test data
        test_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(test_data)
        
        # Mock AI service to raise connection error
        mock_ai_service = MagicMock()
        mock_ai_service.chat.side_effect = ConnectionError("Network connection failed")
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        
        # Verify error handling
        self.assertIn('error', data)
        self.assertIn('message', data)
        
        # Message should be sanitized and user-friendly
        self.assertNotIn('ConnectionError', data['message'])  # Technical details should be sanitized
    
    # Test 3: Service Unavailable Handling
    def test_service_unavailable_handling(self):
        """Test handling when serendipity service is disabled"""
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'False'
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        
        # Verify service unavailable response
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('disabled', data['message'].lower())
        
        # Reset for other tests
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
    
    # Test 4: Corrupted Memory File Handling
    def test_corrupted_memory_file_handling(self):
        """Test handling of corrupted or invalid memory files"""
        # Write invalid JSON to memory file
        with open(self.temp_memory_file.name, 'w') as f:
            f.write('{"invalid": json, "missing": comma}')
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        # Verify error handling
        self.assertIn('error', data)
        self.assertIn('message', data)
        
        # Should provide actionable guidance
        message = data['message'].lower()
        self.assertTrue(
            any(keyword in message for keyword in ['file', 'data', 'corrupted', 'invalid']),
            f"Message should indicate file/data issue: {data['message']}"
        )
    
    # Test 5: Empty Memory File Handling
    def test_empty_memory_file_handling(self):
        """Test handling of empty memory files"""
        # Create empty file
        with open(self.temp_memory_file.name, 'w') as f:
            f.write('')
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        # Verify error handling
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('empty', data['message'].lower())
    
    # Test 6: Missing Memory File Handling
    def test_missing_memory_file_handling(self):
        """Test handling when memory file doesn't exist"""
        # Remove the memory file
        os.unlink(self.temp_memory_file.name)
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        # Verify error handling
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('not found', data['message'].lower())
    
    # Test 7: Partial Results Handling
    @patch('serendipity_service.get_ai_service')
    def test_partial_results_handling(self, mock_get_ai_service):
        """Test graceful handling of partial analysis results"""
        # Create sufficient test data
        test_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(test_data)
        
        # Mock AI service to return partial results
        mock_ai_service = MagicMock()
        partial_response = {
            "connections": [
                {
                    "title": "Test Connection",
                    "description": "A test connection",
                    "surprise_factor": 0.8,
                    "relevance": 0.9,
                    "connected_insights": ["insight1", "insight2"],
                    "connection_type": "cross_domain",
                    "actionable_insight": "Test action"
                }
            ],
            "meta_patterns": [],  # Empty patterns (partial result)
            "serendipity_summary": "",  # Empty summary (partial result)
            "recommendations": []
        }
        mock_ai_service.chat.return_value = json.dumps(partial_response)
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.post('/api/serendipity')
        
        # Should succeed but indicate partial results
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify partial results structure
        self.assertIn('connections', data)
        self.assertIn('meta_patterns', data)
        self.assertEqual(len(data['connections']), 1)
        self.assertEqual(len(data['meta_patterns']), 0)
    
    # Test 8: Timeout Handling Simulation
    @patch('serendipity_service.get_ai_service')
    def test_timeout_handling(self, mock_get_ai_service):
        """Test handling of analysis timeouts"""
        # Create test data
        test_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(test_data)
        
        # Mock AI service to simulate timeout
        mock_ai_service = MagicMock()
        mock_ai_service.chat.side_effect = TimeoutError("Analysis timeout")
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        
        # Verify timeout handling
        self.assertIn('error', data)
        self.assertIn('message', data)
        
        # Should provide timeout-specific guidance
        message = data['message'].lower()
        self.assertTrue(
            any(keyword in message for keyword in ['timeout', 'time', 'slow', 'longer']),
            f"Message should indicate timeout issue: {data['message']}"
        )
    
    # Test 9: Large Dataset Handling
    def test_large_dataset_handling(self):
        """Test handling of large datasets that might cause performance issues"""
        # Create large dataset
        large_data = self.create_test_memory_data(insights_count=100, conversations_count=50)
        self.write_memory_file(large_data)
        
        # This should not fail, but may take longer
        response = self.client.post('/api/serendipity')
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500, 503])
        
        data = response.get_json()
        self.assertIn('error', data) or self.assertIn('connections', data)
    
    # Test 10: Malformed AI Response Handling
    @patch('serendipity_service.get_ai_service')
    def test_malformed_ai_response_handling(self, mock_get_ai_service):
        """Test handling of malformed AI responses"""
        # Create test data
        test_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(test_data)
        
        # Mock AI service to return malformed JSON
        mock_ai_service = MagicMock()
        mock_ai_service.chat.return_value = "This is not valid JSON response"
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        
        # Verify error handling
        self.assertIn('error', data)
        self.assertIn('message', data)
    
    # Test 11: Error Message Sanitization
    @patch('serendipity_service.get_ai_service')
    def test_error_message_sanitization(self, mock_get_ai_service):
        """Test that error messages are properly sanitized for security"""
        # Create test data
        test_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(test_data)
        
        # Mock AI service to raise error with sensitive information
        mock_ai_service = MagicMock()
        sensitive_error = Exception("Database connection failed: user=admin, password=secret123, host=internal.server.com")
        mock_ai_service.chat.side_effect = sensitive_error
        mock_get_ai_service.return_value = mock_ai_service
        
        response = self.client.post('/api/serendipity')
        
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        
        # Verify sensitive information is not exposed
        message = data['message']
        self.assertNotIn('password=secret123', message)
        self.assertNotIn('user=admin', message)
        self.assertNotIn('internal.server.com', message)
        
        # Should contain generic, helpful message
        self.assertTrue(len(message) > 0)
        self.assertNotIn('Exception', message)  # Technical details should be sanitized
    
    # Test 12: Progressive Enhancement Testing
    def test_progressive_enhancement(self):
        """Test that the system works with minimal data and improves with more"""
        # Test with minimal data (should provide guidance)
        minimal_data = self.create_test_memory_data(insights_count=1, conversations_count=1)
        self.write_memory_file(minimal_data)
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 400)  # Insufficient data
        
        # Test with sufficient data (should work)
        sufficient_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(sufficient_data)
        
        with patch('serendipity_service.get_ai_service') as mock_get_ai_service:
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = json.dumps({
                "connections": [{"title": "Test", "description": "Test", "surprise_factor": 0.8, "relevance": 0.9, "connected_insights": [], "connection_type": "test", "actionable_insight": "Test"}],
                "meta_patterns": [],
                "serendipity_summary": "Test summary",
                "recommendations": []
            })
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/api/serendipity')
            self.assertEqual(response.status_code, 200)  # Should work now
    
    # Test 13: Accessibility and User Guidance
    def test_accessibility_and_user_guidance(self):
        """Test that error responses include proper accessibility and user guidance"""
        # Test insufficient data scenario
        insufficient_data = self.create_test_memory_data(insights_count=1, conversations_count=1)
        self.write_memory_file(insufficient_data)
        
        response = self.client.post('/api/serendipity')
        data = response.get_json()
        
        # Verify user guidance is provided
        message = data['message']
        self.assertTrue(
            any(guidance in message.lower() for guidance in [
                'conversation', 'chat', 'more', 'build', 'accumulate', 'time'
            ]),
            f"Message should provide actionable guidance: {message}"
        )
        
        # Verify response includes timestamp for debugging
        self.assertIn('timestamp', data)
    
    # Test 14: Recovery Strategies Testing
    @patch('serendipity_service.get_ai_service')
    def test_recovery_strategies(self, mock_get_ai_service):
        """Test various recovery strategies for different error types"""
        # Create test data
        test_data = self.create_test_memory_data(insights_count=5, conversations_count=3)
        self.write_memory_file(test_data)
        
        # Test recovery from temporary AI service failure
        mock_ai_service = MagicMock()
        
        # First call fails, second succeeds (simulating retry)
        mock_ai_service.chat.side_effect = [
            ConnectionError("Temporary failure"),
            json.dumps({
                "connections": [{"title": "Test", "description": "Test", "surprise_factor": 0.8, "relevance": 0.9, "connected_insights": [], "connection_type": "test", "actionable_insight": "Test"}],
                "meta_patterns": [],
                "serendipity_summary": "Test summary",
                "recommendations": []
            })
        ]
        mock_get_ai_service.return_value = mock_ai_service
        
        # First request should fail
        response1 = self.client.post('/api/serendipity')
        self.assertEqual(response1.status_code, 500)
        
        # Reset mock for second attempt
        mock_ai_service.chat.side_effect = None
        mock_ai_service.chat.return_value = json.dumps({
            "connections": [{"title": "Test", "description": "Test", "surprise_factor": 0.8, "relevance": 0.9, "connected_insights": [], "connection_type": "test", "actionable_insight": "Test"}],
            "meta_patterns": [],
            "serendipity_summary": "Test summary",
            "recommendations": []
        })
        
        # Second request should succeed (simulating recovery)
        response2 = self.client.post('/api/serendipity')
        self.assertEqual(response2.status_code, 200)
    
    # Test 15: Edge Cases and Boundary Conditions
    def test_edge_cases_and_boundary_conditions(self):
        """Test various edge cases and boundary conditions"""
        # Test with exactly minimum required data
        min_data = self.create_test_memory_data(insights_count=3, conversations_count=0)
        self.write_memory_file(min_data)
        
        with patch('serendipity_service.get_ai_service') as mock_get_ai_service:
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = json.dumps({
                "connections": [],
                "meta_patterns": [],
                "serendipity_summary": "",
                "recommendations": []
            })
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/api/serendipity')
            # Should succeed but may have empty results
            self.assertIn(response.status_code, [200, 400])
        
        # Test with malformed insights
        malformed_data = {
            "insights": [
                {"content": "Valid insight", "category": "test"},
                {"invalid": "structure"},  # Missing required fields
                {"content": "", "category": "test"}  # Empty content
            ],
            "conversation_summaries": [],
            "metadata": {}
        }
        self.write_memory_file(malformed_data)
        
        response = self.client.post('/api/serendipity')
        # Should handle malformed data gracefully
        self.assertIn(response.status_code, [200, 400, 500])


class TestUserExperienceFlows(unittest.TestCase):
    """Test complete user experience flows and scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        os.environ['ENABLE_SERENDIPITY_ENGINE'] = 'True'
        
        # Create temporary memory file
        self.temp_memory_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_memory_file.close()
        os.environ['MEMORY_FILE'] = self.temp_memory_file.name
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_memory_file.name):
            os.unlink(self.temp_memory_file.name)
    
    def test_new_user_onboarding_flow(self):
        """Test the complete new user onboarding experience"""
        # Simulate new user with no data
        with open(self.temp_memory_file.name, 'w') as f:
            json.dump({"insights": [], "conversation_summaries": [], "metadata": {}}, f)
        
        # First API call should provide onboarding guidance
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        message = data['message'].lower()
        
        # Should contain onboarding guidance
        self.assertTrue(
            any(keyword in message for keyword in ['conversation', 'chat', 'start', 'build']),
            f"Should provide onboarding guidance: {data['message']}"
        )
    
    def test_progressive_user_journey(self):
        """Test user journey from no data to full analysis"""
        # Stage 1: No data
        empty_data = {"insights": [], "conversation_summaries": [], "metadata": {}}
        with open(self.temp_memory_file.name, 'w') as f:
            json.dump(empty_data, f)
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 400)
        
        # Stage 2: Some data but insufficient
        partial_data = {
            "insights": [{"content": "Test insight", "category": "test"}],
            "conversation_summaries": [],
            "metadata": {}
        }
        with open(self.temp_memory_file.name, 'w') as f:
            json.dump(partial_data, f)
        
        response = self.client.post('/api/serendipity')
        self.assertEqual(response.status_code, 400)
        
        # Stage 3: Sufficient data for analysis
        sufficient_data = {
            "insights": [
                {"content": f"Test insight {i}", "category": "test"} 
                for i in range(5)
            ],
            "conversation_summaries": [
                {"summary": f"Conversation {i}", "key_themes": ["test"]} 
                for i in range(3)
            ],
            "metadata": {"total_insights": 5}
        }
        with open(self.temp_memory_file.name, 'w') as f:
            json.dump(sufficient_data, f)
        
        with patch('serendipity_service.get_ai_service') as mock_get_ai_service:
            mock_ai_service = MagicMock()
            mock_ai_service.chat.return_value = json.dumps({
                "connections": [{"title": "Test", "description": "Test", "surprise_factor": 0.8, "relevance": 0.9, "connected_insights": [], "connection_type": "test", "actionable_insight": "Test"}],
                "meta_patterns": [],
                "serendipity_summary": "Test summary",
                "recommendations": []
            })
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/api/serendipity')
            self.assertEqual(response.status_code, 200)
    
    def test_error_recovery_user_flow(self):
        """Test user experience during error recovery scenarios"""
        # Create sufficient data
        test_data = {
            "insights": [{"content": f"Test insight {i}", "category": "test"} for i in range(5)],
            "conversation_summaries": [{"summary": f"Conversation {i}", "key_themes": ["test"]} for i in range(3)],
            "metadata": {"total_insights": 5}
        }
        with open(self.temp_memory_file.name, 'w') as f:
            json.dump(test_data, f)
        
        # Simulate temporary service failure
        with patch('serendipity_service.get_ai_service') as mock_get_ai_service:
            mock_ai_service = MagicMock()
            mock_ai_service.chat.side_effect = ConnectionError("Temporary failure")
            mock_get_ai_service.return_value = mock_ai_service
            
            response = self.client.post('/api/serendipity')
            self.assertEqual(response.status_code, 500)
            
            # Error should provide recovery guidance
            data = response.get_json()
            self.assertIn('error', data)
            self.assertIn('message', data)
            
            # Should suggest retry
            message = data['message'].lower()
            self.assertTrue(
                any(keyword in message for keyword in ['try', 'again', 'retry', 'later']),
                f"Should suggest retry: {data['message']}"
            )


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)