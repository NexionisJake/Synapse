"""
AI Service Module for Synapse AI Web Application

This module provides the core AI communication functionality using Ollama
with the Llama 3 8B model. It handles system prompt configuration, error
handling, and conversation processing.
"""

import ollama
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, handle_service_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class AIService:
    """
    AI communication service for handling conversations with Ollama
    """
    
    def __init__(self, model: str = "llama3:8b", system_prompt: str = None):
        """
        Initialize the AI service
        
        Args:
            model: The Ollama model to use (default: llama3:8b)
            system_prompt: Custom system prompt for AI personality
        """
        self.model = model
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self._validate_ollama_connection()
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the AI"""
        return """You are Synapse, a private, local-first Cognitive Partner. Your sole purpose is to help the user clarify their own thinking, acting as a sounding board and a mirror for their mind, not as an assistant, search engine, or therapist. Your prime directive is to facilitate the user's journey to their own insights by asking better questions rather than providing answers. Adhere strictly to your guiding principles: maintain intellectual honesty over agreement by respectfully challenging assumptions; prioritize Socratic questioning over giving advice; and ground all your analysis in the user's reality, using only the information they have provided. Before responding, follow your internal monologue: deconstruct the user's message, consult your principles, synthesize with long-term memory, formulate a non-judgmental, open-ended question, and review to ensure you are not giving a direct answer. You are strictly prohibited from giving advice, inventing external facts, or claiming to be a professional. Your voice is that of a patient, curious, and deeply analytical partner—warm and encouraging, yet always intellectually rigorous, giving the user the space to think without rushing to fill the void."""
    
    def _validate_ollama_connection(self) -> None:
        """
        Validate that Ollama is running and the model is available
        
        Raises:
            AIServiceError: If Ollama is not accessible or model is not available
        """
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Test connection by listing available models
                models_response = ollama.list()
                
                # Extract model names from the response
                model_names = []
                if hasattr(models_response, 'models'):
                    # Pydantic model response
                    for model in models_response.models:
                        if hasattr(model, 'model'):
                            model_names.append(model.model)
                        elif hasattr(model, 'name'):
                            model_names.append(model.name)
                elif isinstance(models_response, dict) and 'models' in models_response:
                    # Dictionary response
                    for model in models_response['models']:
                        if isinstance(model, dict):
                            if 'model' in model:
                                model_names.append(model['model'])
                            elif 'name' in model:
                                model_names.append(model['name'])
                
                if self.model not in model_names:
                    error_msg = f"Model {self.model} is not available. Available models: {model_names}. Please install with 'ollama pull {self.model}'"
                    logger.warning(error_msg)
                    error_handler = get_error_handler()
                    error_handler.log_error(
                        AIServiceError(error_msg),
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.HIGH,
                        {"available_models": model_names, "requested_model": self.model}
                    )
                    raise AIServiceError(error_msg)
                
                logger.info(f"Successfully connected to Ollama with model {self.model}")
                return
                
            except ollama.ResponseError as e:
                error_handler = get_error_handler()
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_handler.log_error(
                        e,
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.CRITICAL,
                        {"attempts": max_retries, "model": self.model}
                    )
                    raise AIServiceError(f"Failed to connect to Ollama after {max_retries} attempts: {e}")
            except Exception as e:
                error_handler = get_error_handler()
                if attempt < max_retries - 1:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}, retrying: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    error_handler.log_error(
                        e,
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.CRITICAL,
                        {"attempts": max_retries, "model": self.model}
                    )
                    raise AIServiceError(f"Ollama service is not available after {max_retries} attempts. Please ensure Ollama is running: {e}")
    
    @handle_service_error(ErrorCategory.AI_SERVICE, ErrorSeverity.MEDIUM)
    def chat(self, conversation_history: List[Dict[str, str]], stream: bool = False):
        """
        Send a conversation to the AI and get a response
        
        Args:
            conversation_history: List of message dictionaries with 'role' and 'content' keys
            stream: Whether to return a streaming response generator
            
        Returns:
            str or generator: The AI's response message or streaming generator
            
        Raises:
            AIServiceError: If there's an error communicating with the AI
        """
        max_retries = 2
        retry_delay = 1
        
        # Validate input
        if not conversation_history:
            raise AIServiceError("Conversation history cannot be empty")
        
        for attempt in range(max_retries):
            try:
                # Prepare messages with system prompt
                messages = [{"role": "system", "content": self.system_prompt}]
                
                # Add conversation history with validation
                for i, message in enumerate(conversation_history):
                    if not isinstance(message, dict):
                        raise AIServiceError(f"Message at index {i} is not a dictionary")
                    if 'role' not in message or 'content' not in message:
                        raise AIServiceError(f"Message at index {i} missing 'role' or 'content'")
                    if not isinstance(message['content'], str):
                        raise AIServiceError(f"Message content at index {i} must be a string")
                    
                    messages.append({
                        "role": message['role'],
                        "content": message['content']
                    })
                
                logger.info(f"Sending {len(messages)} messages to AI model {self.model} (attempt {attempt + 1})")
                
                # Make the API call to Ollama with timeout
                start_time = time.time()
                
                if stream:
                    # Return streaming generator
                    return self._handle_streaming_response(messages, start_time)
                else:
                    # Regular non-streaming response
                    response = ollama.chat(
                        model=self.model,
                        messages=messages,
                        options={
                            "timeout": 180  # Increased timeout for long-running analysis (3 minutes)
                        }
                    )
                    response_time = time.time() - start_time
                    
                    # Handle both old dict format and new typed response format
                    if hasattr(response, 'message'):
                        # New typed response format
                        message = response.message
                        if hasattr(message, 'content'):
                            ai_response = message.content
                        else:
                            raise AIServiceError("Invalid response format: message missing 'content' attribute")
                    elif isinstance(response, dict):
                        # Old dict format (for backward compatibility)
                        if 'message' not in response:
                            raise AIServiceError("Invalid response format: missing 'message' field")
                        if 'content' not in response['message']:
                            raise AIServiceError("Invalid response format: missing 'content' field")
                        ai_response = response['message']['content']
                    else:
                        raise AIServiceError(f"Invalid response format: unexpected type {type(response)}")
                    
                    # Validate response content
                    if not isinstance(ai_response, str):
                        raise AIServiceError("Invalid response format: content is not a string")
                    if not ai_response.strip():
                        raise AIServiceError("AI returned empty response")
                    
                    logger.info(f"Received response from AI: {len(ai_response)} characters in {response_time:.2f}s")
                    return ai_response
                
            except ollama.ResponseError as e:
                error_handler = get_error_handler()
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama API error on attempt {attempt + 1}, retrying: {e}")
                    error_handler.log_error(
                        e,
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.LOW,
                        {"attempt": attempt + 1, "max_retries": max_retries}
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    error_handler.log_error(
                        e,
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.HIGH,
                        {"attempts": max_retries, "conversation_length": len(conversation_history)}
                    )
                    raise AIServiceError(f"AI communication failed after {max_retries} attempts: {e}")
            except (KeyError, TypeError) as e:
                error_handler = get_error_handler()
                error_handler.log_error(
                    e,
                    ErrorCategory.AI_SERVICE,
                    ErrorSeverity.HIGH,
                    {"response_structure": str(response) if 'response' in locals() else "unknown"}
                )
                raise AIServiceError(f"Invalid response format from AI service: {e}")
            except Exception as e:
                error_handler = get_error_handler()
                if attempt < max_retries - 1:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}, retrying: {e}")
                    error_handler.log_error(
                        e,
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.MEDIUM,
                        {"attempt": attempt + 1, "max_retries": max_retries}
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    error_handler.log_error(
                        e,
                        ErrorCategory.AI_SERVICE,
                        ErrorSeverity.HIGH,
                        {"attempts": max_retries, "conversation_length": len(conversation_history)}
                    )
                    raise AIServiceError(f"Unexpected error during AI communication: {e}")
    
    def _handle_streaming_response(self, messages, start_time):
        """
        Handle streaming response from Ollama
        
        Args:
            messages: The messages to send to Ollama
            start_time: Start time for performance tracking
            
        Yields:
            dict: Streaming response chunks with content and metadata
        """
        try:
            # Make streaming API call to Ollama
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "timeout": 180  # Increased timeout for streaming analysis
                }
            )
            
            full_response = ""
            chunk_count = 0
            
            for chunk in stream:
                chunk_count += 1
                
                # Handle both old dict format and new typed response format
                if hasattr(chunk, 'message'):
                    # New typed response format
                    message = chunk.message
                    if hasattr(message, 'content'):
                        content = message.content
                    else:
                        content = ""
                elif isinstance(chunk, dict):
                    # Old dict format (for backward compatibility)
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                    else:
                        content = ""
                else:
                    content = ""
                
                if content:
                    full_response += content
                    
                    # Yield chunk data
                    yield {
                        "content": content,
                        "full_content": full_response,
                        "chunk_id": chunk_count,
                        "timestamp": time.time(),
                        "done": False
                    }
            
            # Send final chunk with completion info
            response_time = time.time() - start_time
            logger.info(f"Completed streaming response: {len(full_response)} characters in {response_time:.2f}s ({chunk_count} chunks)")
            
            yield {
                "content": "",
                "full_content": full_response,
                "chunk_id": chunk_count + 1,
                "timestamp": time.time(),
                "done": True,
                "response_time": response_time,
                "total_chunks": chunk_count
            }
            
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.log_error(
                e,
                ErrorCategory.AI_SERVICE,
                ErrorSeverity.HIGH,
                {"streaming": True, "chunk_count": chunk_count if 'chunk_count' in locals() else 0}
            )
            # Send error chunk
            yield {
                "content": "",
                "full_content": "",
                "chunk_id": 0,
                "timestamp": time.time(),
                "done": True,
                "error": str(e)
            }

    def update_system_prompt(self, new_prompt: str) -> None:
        """
        Update the system prompt for the AI
        
        Args:
            new_prompt: The new system prompt to use
        """
        try:
            if not new_prompt or not new_prompt.strip():
                raise AIServiceError("System prompt cannot be empty")
            
            # Validate prompt length
            if len(new_prompt.strip()) > 10000:
                raise AIServiceError("System prompt is too long (maximum 10,000 characters)")
            
            self.system_prompt = new_prompt.strip()
            logger.info("System prompt updated successfully")
            
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.log_error(
                e,
                ErrorCategory.AI_SERVICE,
                ErrorSeverity.MEDIUM,
                {"prompt_length": len(new_prompt) if new_prompt else 0}
            )
            raise
    
    def get_system_prompt(self) -> str:
        """
        Get the current system prompt
        
        Returns:
            str: The current system prompt
        """
        return self.system_prompt
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Ollama and return status information
        
        Returns:
            dict: Status information including connection status and available models
        """
        try:
            start_time = time.time()
            models_response = ollama.list()
            response_time = time.time() - start_time
            
            # Extract model names from the response
            model_names = []
            if hasattr(models_response, 'models'):
                # Pydantic model response
                for model in models_response.models:
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
                    elif hasattr(model, 'name'):
                        model_names.append(model.name)
            elif isinstance(models_response, dict) and 'models' in models_response:
                # Dictionary response
                for model in models_response['models']:
                    if isinstance(model, dict):
                        if 'model' in model:
                            model_names.append(model['model'])
                        elif 'name' in model:
                            model_names.append(model['name'])
            
            # Test a simple chat to verify model works
            test_successful = False
            try:
                test_response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a test assistant."},
                        {"role": "user", "content": "Say 'test successful'"}
                    ],
                    options={"timeout": 10}
                )
                if test_response and 'message' in test_response:
                    test_successful = True
            except Exception:
                pass  # Test failed, but connection to Ollama works
            
            return {
                "connected": True,
                "model": self.model,
                "model_available": self.model in model_names,
                "model_functional": test_successful,
                "available_models": model_names,
                "response_time": round(response_time, 3),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.log_error(
                e,
                ErrorCategory.AI_SERVICE,
                ErrorSeverity.MEDIUM,
                {"model": self.model}
            )
            return {
                "connected": False,
                "error": str(e),
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }

# Global AI service instance
_ai_service_instance = None

def get_ai_service(model: str = "llama3:8b", system_prompt: str = None) -> AIService:
    """
    Get or create the global AI service instance
    
    Args:
        model: The Ollama model to use
        system_prompt: Custom system prompt for AI personality
        
    Returns:
        AIService: The AI service instance
    """
    global _ai_service_instance
    
    if _ai_service_instance is None:
        _ai_service_instance = AIService(model=model, system_prompt=system_prompt)
    
    return _ai_service_instance

def reset_ai_service():
    """Reset the global AI service instance (useful for testing)"""
    global _ai_service_instance
    _ai_service_instance = None