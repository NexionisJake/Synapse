"""
Memory Service Module for Synapse AI Web Application

This module provides memory processing and insight generation functionality.
It extracts insights from conversations and maintains long-term memory storage.
"""

import json
import os
import logging
import threading
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
import ollama
from ai_service import AIServiceError
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, handle_service_error, safe_file_operation, RecoveryManager
from security import validate_file_access, sanitize_error_for_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryServiceError(Exception):
    """Custom exception for memory service errors"""
    pass

class MemoryService:
    """
    Memory processing service for extracting and storing conversation insights
    """
    
    def __init__(self, model: str = "llama3:8b", memory_file: str = "memory.json"):
        """
        Initialize the memory service
        
        Args:
            model: The Ollama model to use for insight generation
            memory_file: Path to the memory storage file
        """
        self.model = model
        self.memory_file = memory_file
        self.insight_prompt = self._get_insight_extraction_prompt()
        self._file_lock = threading.Lock()
    
    def _get_insight_extraction_prompt(self) -> str:
        """Get the specialized prompt for insight extraction"""
        return """You are an expert at analyzing conversations and extracting meaningful insights. 

Your task is to analyze the provided conversation and extract key insights about the user's thoughts, preferences, interests, and patterns.

CRITICAL: You must respond with ONLY a valid JSON object. Do not include any explanatory text, comments, or formatting outside the JSON. Your entire response must be parseable as JSON.

Respond with this exact JSON structure:
{
  "insights": [
    {
      "category": "string (e.g., 'interests', 'preferences', 'thinking_patterns', 'goals', 'concerns')",
      "content": "string (clear, concise description of the insight)",
      "confidence": number (0.0 to 1.0, how confident you are in this insight),
      "tags": ["array", "of", "relevant", "keywords"],
      "evidence": "string (brief quote or reference from conversation that supports this insight)"
    }
  ],
  "conversation_summary": "string (brief summary of the main topics discussed)",
  "key_themes": ["array", "of", "main", "themes"]
}

Focus on extracting insights that would be valuable for future conversations. Look for:
- User's interests and passions
- Thinking patterns and problem-solving approaches
- Goals and aspirations
- Concerns or challenges
- Communication preferences
- Learning style indicators
- Values and beliefs expressed

Only extract insights that are clearly supported by the conversation content. Be specific and actionable.

Remember: Respond with ONLY the JSON object, no other text."""

    def extract_insights(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract insights from a conversation using AI analysis
        
        Args:
            conversation_history: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            dict: Extracted insights in structured format
            
        Raises:
            MemoryServiceError: If there's an error during insight extraction
        """
        try:
            # Prepare the conversation text for analysis
            conversation_text = self._format_conversation_for_analysis(conversation_history)
            
            # Prepare messages for insight extraction
            messages = [
                {"role": "system", "content": self.insight_prompt},
                {"role": "user", "content": f"Please analyze this conversation and extract insights:\n\n{conversation_text}"}
            ]
            
            logger.info(f"Extracting insights from conversation with {len(conversation_history)} messages")
            
            # Make the API call to Ollama for insight extraction
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            # Extract the response content
            ai_response = response['message']['content']
            logger.info(f"Received insight extraction response: {len(ai_response)} characters")
            
            # Parse the JSON response
            try:
                # Try to extract JSON from the response if it contains extra text
                cleaned_response = self._extract_json_from_response(ai_response)
                insights_data = json.loads(cleaned_response)
                
                # Validate the response structure
                if not isinstance(insights_data, dict):
                    raise MemoryServiceError("AI response is not a valid JSON object")
                
                if 'insights' not in insights_data:
                    raise MemoryServiceError("AI response missing 'insights' field")
                
                if not isinstance(insights_data['insights'], list):
                    raise MemoryServiceError("'insights' field must be a list")
                
                # Add metadata to insights
                for insight in insights_data['insights']:
                    insight['timestamp'] = datetime.now().isoformat()
                    insight['source_conversation_length'] = len(conversation_history)
                
                # Add extraction metadata
                insights_data['extraction_metadata'] = {
                    'timestamp': datetime.now().isoformat(),
                    'model_used': self.model,
                    'conversation_length': len(conversation_history)
                }
                
                logger.info(f"Successfully extracted {len(insights_data['insights'])} insights")
                return insights_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"AI response was: {ai_response[:500]}...")
                raise MemoryServiceError(f"AI returned invalid JSON: {e}")
            
        except ollama.ResponseError as e:
            logger.error(f"Ollama API error during insight extraction: {e}")
            raise MemoryServiceError(f"AI communication failed during insight extraction: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during insight extraction: {e}")
            raise MemoryServiceError(f"Unexpected error during insight extraction: {e}")
    
    def _format_conversation_for_analysis(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Format conversation history for AI analysis
        
        Args:
            conversation_history: List of message dictionaries
            
        Returns:
            str: Formatted conversation text
        """
        formatted_lines = []
        
        for message in conversation_history:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            
            if role == 'user':
                formatted_lines.append(f"User: {content}")
            elif role == 'assistant':
                formatted_lines.append(f"Assistant: {content}")
        
        return "\n\n".join(formatted_lines)
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from AI response that might contain extra text
        
        Args:
            response: Raw AI response that should contain JSON
            
        Returns:
            str: Cleaned JSON string
        """
        # First try the response as-is
        response = response.strip()
        if response.startswith('{') and response.endswith('}'):
            return response
        
        # Look for JSON object in the response
        start_idx = response.find('{')
        if start_idx == -1:
            return response  # No JSON found, return as-is
        
        # Find the matching closing brace
        brace_count = 0
        end_idx = -1
        
        for i in range(start_idx, len(response)):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx != -1:
            return response[start_idx:end_idx + 1]
        
        return response  # Fallback to original response
    
    @handle_service_error(ErrorCategory.MEMORY_SERVICE, ErrorSeverity.MEDIUM)
    def save_insights(self, insights_data: Dict[str, Any]) -> None:
        """
        Save insights to the memory file with enhanced error handling and file locking
        
        Args:
            insights_data: Structured insights data to save
            
        Raises:
            MemoryServiceError: If there's an error saving insights
        """
        with self._file_lock:
            try:
                # Validate input data
                if not isinstance(insights_data, dict):
                    raise MemoryServiceError("Insights data must be a dictionary")
                
                new_insights = insights_data.get('insights', [])
                if not isinstance(new_insights, list):
                    raise MemoryServiceError("Insights must be a list")
                
                # Load existing memory data if file exists
                existing_data = self._load_memory_file()
                
                # Add new insights to existing data
                if 'insights' not in existing_data:
                    existing_data['insights'] = []
                
                # Validate and add the new insights
                for i, insight in enumerate(new_insights):
                    if not isinstance(insight, dict):
                        logger.warning(f"Skipping invalid insight at index {i}: not a dictionary")
                        continue
                    
                    # Add validation timestamp if not present
                    if 'timestamp' not in insight:
                        insight['timestamp'] = datetime.now().isoformat()
                    
                    existing_data['insights'].append(insight)
                
                # Update metadata
                existing_data['metadata'] = {
                    'total_insights': len(existing_data['insights']),
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0'
                }
                
                # Add conversation summaries if they don't exist
                if 'conversation_summaries' not in existing_data:
                    existing_data['conversation_summaries'] = []
                
                # Add this conversation's summary
                if 'conversation_summary' in insights_data:
                    summary_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'summary': insights_data['conversation_summary'],
                        'key_themes': insights_data.get('key_themes', []),
                        'insights_count': len([i for i in new_insights if isinstance(i, dict)])
                    }
                    existing_data['conversation_summaries'].append(summary_entry)
                
                # Save the updated data
                self._save_memory_file(existing_data)
                
                valid_insights_count = len([i for i in new_insights if isinstance(i, dict)])
                logger.info(f"Successfully saved {valid_insights_count} insights to {self.memory_file}")
                
            except Exception as e:
                error_handler = get_error_handler()
                error_handler.log_error(
                    e,
                    ErrorCategory.MEMORY_SERVICE,
                    ErrorSeverity.HIGH,
                    {
                        "insights_count": len(insights_data.get('insights', [])) if isinstance(insights_data, dict) else 0,
                        "memory_file": self.memory_file
                    }
                )
                # Sanitize error message for security
                sanitized_message = sanitize_error_for_user(e, "Memory save error")
                raise MemoryServiceError(sanitized_message)
    
    def _load_memory_file(self) -> Dict[str, Any]:
        """
        Load existing memory data from file with enhanced error handling and caching
        
        Returns:
            dict: Existing memory data or empty structure if file doesn't exist
        """
        default_structure = {
            'insights': [],
            'conversation_summaries': [],
            'metadata': {
                'total_insights': 0,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        if not os.path.exists(self.memory_file):
            logger.info(f"Memory file {self.memory_file} does not exist, creating new structure")
            return default_structure
        
        # Validate file access for security
        is_allowed, error_msg = validate_file_access(self.memory_file, "read")
        if not is_allowed:
            raise MemoryServiceError(f"File access denied: {error_msg}")
        
        try:
            # Try to use file optimizer for cached reading
            try:
                from performance_optimizer import file_optimizer
                data = file_optimizer.cached_file_read(self.memory_file, max_age_seconds=60)
                if data is not None:
                    # Ensure required fields exist
                    if 'insights' not in data:
                        data['insights'] = []
                    if 'conversation_summaries' not in data:
                        data['conversation_summaries'] = []
                    if 'metadata' not in data:
                        data['metadata'] = default_structure['metadata']
                    
                    logger.debug(f"Loaded memory file from cache with {len(data.get('insights', []))} insights")
                    return data
            except ImportError:
                logger.debug("Performance optimizer not available, using standard file operations")
            
            # Fallback to standard file operations
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate structure
                if not isinstance(data, dict):
                    raise MemoryServiceError("Memory file does not contain a valid JSON object")
                
                # Ensure required fields exist
                if 'insights' not in data:
                    data['insights'] = []
                if 'conversation_summaries' not in data:
                    data['conversation_summaries'] = []
                if 'metadata' not in data:
                    data['metadata'] = default_structure['metadata']
                
                logger.info(f"Loaded existing memory file with {len(data.get('insights', []))} insights")
                return data
        
        except json.JSONDecodeError as e:
            error_handler = get_error_handler()
            error_handler.log_error(
                e,
                ErrorCategory.FILE_SYSTEM,
                ErrorSeverity.HIGH,
                {"file": self.memory_file, "operation": "load_json"}
            )
            
            # Attempt recovery
            if RecoveryManager.recover_corrupted_json_file(self.memory_file, default_structure):
                logger.info("Successfully recovered corrupted memory file")
                return default_structure
            else:
                raise MemoryServiceError(f"Failed to recover corrupted memory file: {e}")
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.log_error(
                e,
                ErrorCategory.FILE_SYSTEM,
                ErrorSeverity.HIGH,
                {"file": self.memory_file, "operation": "load_file"}
            )
            raise MemoryServiceError(f"Failed to read memory file: {e}")
    
    def _save_memory_file(self, data: Dict[str, Any]) -> None:
        """
        Save memory data to file with enhanced error handling and optimization
        
        Args:
            data: Memory data to save
            
        Raises:
            MemoryServiceError: If there's an error saving the file
        """
        try:
            # Validate file access for security
            is_allowed, error_msg = validate_file_access(self.memory_file, "write")
            if not is_allowed:
                raise MemoryServiceError(f"File access denied: {error_msg}")
            
            # Validate data structure before saving
            if not isinstance(data, dict):
                raise MemoryServiceError("Memory data must be a dictionary")
            
            # Try to use file optimizer for optimized writing
            try:
                from performance_optimizer import file_optimizer
                success = file_optimizer.optimized_file_write(self.memory_file, data, create_backup=True)
                if success:
                    logger.info(f"Successfully saved memory data using optimizer to {self.memory_file}")
                    return
                else:
                    logger.warning("File optimizer failed, falling back to standard operations")
            except ImportError:
                logger.debug("Performance optimizer not available, using standard file operations")
            
            # Fallback to standard file operations
            # Check disk space before saving
            if not RecoveryManager.check_disk_space(".", 10):  # 10MB minimum
                raise MemoryServiceError("Insufficient disk space to save memory file")
            
            # Create backup of existing file if it exists
            backup_created = False
            if os.path.exists(self.memory_file):
                try:
                    backup_file = f"{self.memory_file}.backup"
                    shutil.copy2(self.memory_file, backup_file)
                    backup_created = True
                    logger.debug(f"Created backup: {backup_file}")
                except Exception as backup_error:
                    logger.warning(f"Failed to create backup: {backup_error}")
                    # Continue without backup - better to save than lose data
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = f"{self.memory_file}.tmp"
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Verify the written file is valid JSON
                with open(temp_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # This will raise an exception if JSON is invalid
                
                # Atomic rename
                if os.name == 'nt':  # Windows
                    if os.path.exists(self.memory_file):
                        os.remove(self.memory_file)
                os.rename(temp_file, self.memory_file)
                
                logger.info(f"Successfully saved memory data to {self.memory_file}")
                
            except Exception as e:
                # Clean up temp file if it exists
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                raise e
            
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.log_error(
                e,
                ErrorCategory.FILE_SYSTEM,
                ErrorSeverity.HIGH,
                {
                    "file": self.memory_file,
                    "operation": "save_file",
                    "data_size": len(str(data)) if data else 0
                }
            )
            raise MemoryServiceError(f"Failed to write memory file: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current memory storage (thread-safe)
        
        Returns:
            dict: Memory statistics
        """
        with self._file_lock:
            try:
                data = self._load_memory_file()
                
                insights = data.get('insights', [])
                summaries = data.get('conversation_summaries', [])
                
                # Calculate category distribution
                categories = {}
                for insight in insights:
                    category = insight.get('category', 'unknown')
                    categories[category] = categories.get(category, 0) + 1
                
                # Calculate confidence distribution
                confidence_levels = {'high': 0, 'medium': 0, 'low': 0}
                for insight in insights:
                    confidence = insight.get('confidence', 0)
                    if confidence >= 0.8:
                        confidence_levels['high'] += 1
                    elif confidence >= 0.5:
                        confidence_levels['medium'] += 1
                    else:
                        confidence_levels['low'] += 1
                
                return {
                    'total_insights': len(insights),
                    'total_conversations': len(summaries),
                    'categories': categories,
                    'confidence_distribution': confidence_levels,
                    'last_updated': data.get('metadata', {}).get('last_updated'),
                    'memory_file_exists': os.path.exists(self.memory_file),
                    'memory_file_size': os.path.getsize(self.memory_file) if os.path.exists(self.memory_file) else 0
                }
                
            except Exception as e:
                logger.error(f"Error getting memory stats: {e}")
            return {
                'error': str(e),
                'total_insights': 0,
                'total_conversations': 0,
                'memory_file_exists': False
            }
    
    def process_conversation(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Complete memory processing workflow: extract insights and save them
        
        Args:
            conversation_history: List of message dictionaries
            
        Returns:
            dict: Processing results including insights and statistics
            
        Raises:
            MemoryServiceError: If there's an error during processing
        """
        try:
            # Extract insights from conversation
            insights_data = self.extract_insights(conversation_history)
            
            # Save insights to memory file
            self.save_insights(insights_data)
            
            # Get updated memory statistics
            stats = self.get_memory_stats()
            
            return {
                'success': True,
                'insights_extracted': len(insights_data.get('insights', [])),
                'conversation_summary': insights_data.get('conversation_summary'),
                'key_themes': insights_data.get('key_themes', []),
                'memory_stats': stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation for memory: {e}")
            raise MemoryServiceError(f"Failed to process conversation: {e}")

# Global memory service instance
_memory_service_instance = None

def get_memory_service(model: str = "llama3:8b", memory_file: str = "memory.json") -> MemoryService:
    """
    Get or create the global memory service instance
    
    Args:
        model: The Ollama model to use for insight generation
        memory_file: Path to the memory storage file
        
    Returns:
        MemoryService: The memory service instance
    """
    global _memory_service_instance
    
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService(model=model, memory_file=memory_file)
        # On first initialization, check for and load sample data
        if not os.path.exists(memory_file) or os.path.getsize(memory_file) == 0:
            sample_data_path = "static/sample_conversation_history.json"
            if os.path.exists(sample_data_path):
                logger.info("Memory file is empty. Loading sample conversation history for demonstration.")
                try:
                    with open(sample_data_path, 'r', encoding='utf-8') as f:
                        sample_conversations = json.load(f)
                    
                    for conversation in sample_conversations:
                        # Reformat for memory processing
                        history = []
                        for user_msg, ai_msg in zip(conversation['user_messages'], conversation['ai_responses']):
                            history.append({"role": "user", "content": user_msg})
                            history.append({"role": "assistant", "content": ai_msg})
                        
                        # Process each conversation to generate and save insights
                        _memory_service_instance.process_conversation(history)
                    
                    logger.info(f"Successfully processed {len(sample_conversations)} sample conversations.")
                    
                except Exception as e:
                    logger.error(f"Failed to load and process sample conversation data: {e}")

    return _memory_service_instance

def reset_memory_service():
    """Reset the global memory service instance (useful for testing)"""
    global _memory_service_instance
    _memory_service_instance = None