"""
Prompt Service Module for Synapse AI Web Application

This module provides system prompt management functionality including
loading, saving, validation, and testing of custom system prompts.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ai_service import get_ai_service, AIServiceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptServiceError(Exception):
    """Custom exception for prompt service errors"""
    pass

class PromptService:
    """
    Service for managing system prompt configuration and validation
    """
    
    def __init__(self, config_file: str = "prompt_config.json"):
        """
        Initialize the prompt service
        
        Args:
            config_file: Path to the prompt configuration file
        """
        self.config_file = config_file
        self.default_prompt = """You are Synapse, a private, local-first Cognitive Partner. Your sole purpose is to help the user clarify their own thinking, acting as a sounding board and a mirror for their mind, not as an assistant, search engine, or therapist. Your prime directive is to facilitate the user's journey to their own insights by asking better questions rather than providing answers. Adhere strictly to your guiding principles: maintain intellectual honesty over agreement by respectfully challenging assumptions; prioritize Socratic questioning over giving advice; and ground all your analysis in the user's reality, using only the information they have provided. 

**CRITICAL: Always format your responses using proper Markdown syntax. Never use HTML entities.**

Markdown formatting requirements:
- Use "# " for main headings and "## " for subheadings
- Create bulleted lists with "* " at the start of each line
- Use "**text**" for bold emphasis on key concepts  
- Use "> " for blockquotes and important reflections
- Use blank lines to separate paragraphs
- Put each list item on its own line
- Add line breaks between different sections
- Never use HTML entities like &gt; or &lt; - always use the actual characters

Before responding, follow your internal monologue: deconstruct the user's message, consult your principles, synthesize with long-term memory, formulate a non-judgmental, open-ended question, and review to ensure you are not giving a direct answer. You are strictly prohibited from giving advice, inventing external facts, or claiming to be a professional. Your voice is that of a patient, curious, and deeply analytical partner—warm and encouraging, yet always intellectually rigorous, giving the user the space to think without rushing to fill the void."""
        self._ensure_config_file_exists()
    
    def _ensure_config_file_exists(self) -> None:
        """Ensure the configuration file exists with default settings"""
        if not os.path.exists(self.config_file):
            default_config = {
                "current_prompt": self.default_prompt,
                "prompt_history": [
                    {
                        "prompt": self.default_prompt,
                        "name": "Default Synapse Prompt",
                        "created_at": datetime.now().isoformat(),
                        "is_default": True
                    }
                ],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self._save_config(default_config)
            logger.info(f"Created default prompt configuration file: {self.config_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the prompt configuration from file
        
        Returns:
            dict: The prompt configuration data
            
        Raises:
            PromptServiceError: If there's an error loading the configuration
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.error(f"Prompt configuration file not found: {self.config_file}")
            raise PromptServiceError(f"Configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompt configuration file: {e}")
            raise PromptServiceError(f"Invalid configuration file format: {e}")
        except Exception as e:
            logger.error(f"Error loading prompt configuration: {e}")
            raise PromptServiceError(f"Failed to load configuration: {e}")
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save the prompt configuration to file
        
        Args:
            config: The configuration data to save
            
        Raises:
            PromptServiceError: If there's an error saving the configuration
        """
        try:
            # Update metadata
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved prompt configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving prompt configuration: {e}")
            raise PromptServiceError(f"Failed to save configuration: {e}")
    
    def get_current_prompt(self) -> str:
        """
        Get the current system prompt
        
        Returns:
            str: The current system prompt
        """
        try:
            config = self._load_config()
            return config.get("current_prompt", self.default_prompt)
        except PromptServiceError:
            logger.warning("Using default prompt due to configuration error")
            return self.default_prompt
    
    def update_prompt(self, new_prompt: str, name: str = None) -> Dict[str, Any]:
        """
        Update the current system prompt
        
        Args:
            new_prompt: The new system prompt
            name: Optional name for the prompt
            
        Returns:
            dict: Result of the update operation
            
        Raises:
            PromptServiceError: If the prompt is invalid or update fails
        """
        # Validate the prompt
        validation_result = self.validate_prompt(new_prompt)
        if not validation_result["valid"]:
            raise PromptServiceError(f"Invalid prompt: {validation_result['error']}")
        
        try:
            config = self._load_config()
            
            # Create prompt entry
            prompt_entry = {
                "prompt": new_prompt.strip(),
                "name": name or f"Custom Prompt {len(config['prompt_history']) + 1}",
                "created_at": datetime.now().isoformat(),
                "is_default": False
            }
            
            # Update current prompt
            config["current_prompt"] = new_prompt.strip()
            
            # Add to history
            config["prompt_history"].append(prompt_entry)
            
            # Save configuration
            self._save_config(config)
            
            logger.info(f"Updated system prompt: {prompt_entry['name']}")
            
            return {
                "success": True,
                "message": "System prompt updated successfully",
                "prompt_name": prompt_entry["name"],
                "timestamp": prompt_entry["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error updating prompt: {e}")
            raise PromptServiceError(f"Failed to update prompt: {e}")
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate a system prompt
        
        Args:
            prompt: The prompt to validate
            
        Returns:
            dict: Validation result with 'valid' boolean and optional 'error' message
        """
        if not prompt or not prompt.strip():
            return {
                "valid": False,
                "error": "Prompt cannot be empty"
            }
        
        prompt = prompt.strip()
        
        # Check minimum length
        if len(prompt) < 10:
            return {
                "valid": False,
                "error": "Prompt must be at least 10 characters long"
            }
        
        # Check maximum length (reasonable limit for system prompts)
        if len(prompt) > 5000:
            return {
                "valid": False,
                "error": "Prompt must be less than 5000 characters"
            }
        
        # Check for potentially problematic content
        problematic_patterns = [
            "ignore previous instructions",
            "forget everything",
            "act as if you are",
            "pretend to be"
        ]
        
        prompt_lower = prompt.lower()
        for pattern in problematic_patterns:
            if pattern in prompt_lower:
                return {
                    "valid": False,
                    "error": f"Prompt contains potentially problematic instruction: '{pattern}'"
                }
        
        return {
            "valid": True,
            "message": "Prompt is valid"
        }
    
    def test_prompt(self, prompt: str, test_message: str = "Hello, how are you?") -> Dict[str, Any]:
        """
        Test a system prompt by sending a test message
        
        Args:
            prompt: The system prompt to test
            test_message: The test message to send (default: "Hello, how are you?")
            
        Returns:
            dict: Test result with response and metadata
            
        Raises:
            PromptServiceError: If the test fails
        """
        # Validate the prompt first
        validation_result = self.validate_prompt(prompt)
        if not validation_result["valid"]:
            raise PromptServiceError(f"Cannot test invalid prompt: {validation_result['error']}")
        
        try:
            # Create a temporary AI service instance with the test prompt
            ai_service = get_ai_service()
            original_prompt = ai_service.get_system_prompt()
            
            # Temporarily update the system prompt
            ai_service.update_system_prompt(prompt)
            
            # Send test message
            test_conversation = [{"role": "user", "content": test_message}]
            response = ai_service.chat(test_conversation)
            
            # Restore original prompt
            ai_service.update_system_prompt(original_prompt)
            
            return {
                "success": True,
                "test_message": test_message,
                "response": response,
                "response_length": len(response),
                "timestamp": datetime.now().isoformat()
            }
            
        except AIServiceError as e:
            logger.error(f"AI service error during prompt test: {e}")
            raise PromptServiceError(f"Failed to test prompt: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during prompt test: {e}")
            raise PromptServiceError(f"Unexpected error testing prompt: {e}")
    
    def get_prompt_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of all system prompts
        
        Returns:
            list: List of prompt history entries
        """
        try:
            config = self._load_config()
            return config.get("prompt_history", [])
        except PromptServiceError:
            logger.warning("Using empty history due to configuration error")
            return []
    
    def restore_prompt(self, prompt_index: int) -> Dict[str, Any]:
        """
        Restore a prompt from history as the current prompt
        
        Args:
            prompt_index: Index of the prompt in history to restore
            
        Returns:
            dict: Result of the restore operation
            
        Raises:
            PromptServiceError: If the index is invalid or restore fails
        """
        try:
            config = self._load_config()
            prompt_history = config.get("prompt_history", [])
            
            if prompt_index < 0 or prompt_index >= len(prompt_history):
                raise PromptServiceError(f"Invalid prompt index: {prompt_index}")
            
            selected_prompt = prompt_history[prompt_index]
            config["current_prompt"] = selected_prompt["prompt"]
            
            # Save configuration
            self._save_config(config)
            
            logger.info(f"Restored prompt: {selected_prompt['name']}")
            
            return {
                "success": True,
                "message": f"Restored prompt: {selected_prompt['name']}",
                "prompt_name": selected_prompt["name"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error restoring prompt: {e}")
            raise PromptServiceError(f"Failed to restore prompt: {e}")
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """
        Get statistics about prompt usage
        
        Returns:
            dict: Statistics about prompts
        """
        try:
            config = self._load_config()
            prompt_history = config.get("prompt_history", [])
            current_prompt = config.get("current_prompt", "")
            
            return {
                "total_prompts": len(prompt_history),
                "current_prompt_length": len(current_prompt),
                "default_prompts": len([p for p in prompt_history if p.get("is_default", False)]),
                "custom_prompts": len([p for p in prompt_history if not p.get("is_default", False)]),
                "last_updated": config.get("metadata", {}).get("last_updated"),
                "config_version": config.get("metadata", {}).get("version")
            }
            
        except PromptServiceError:
            return {
                "total_prompts": 0,
                "current_prompt_length": 0,
                "default_prompts": 0,
                "custom_prompts": 0,
                "last_updated": None,
                "config_version": None
            }

# Global prompt service instance
_prompt_service_instance = None

def get_prompt_service(config_file: str = "prompt_config.json") -> PromptService:
    """
    Get or create the global prompt service instance
    
    Args:
        config_file: Path to the prompt configuration file
        
    Returns:
        PromptService: The prompt service instance
    """
    global _prompt_service_instance
    
    if _prompt_service_instance is None:
        _prompt_service_instance = PromptService(config_file=config_file)
    
    return _prompt_service_instance

def reset_prompt_service():
    """Reset the global prompt service instance (useful for testing)"""
    global _prompt_service_instance
    _prompt_service_instance = None