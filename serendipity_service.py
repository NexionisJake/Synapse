"""
Serendipity Service Module for Synapse AI Web Application

This module provides serendipity engine functionality for discovering
unexpected connections and patterns in conversation history and insights.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import ollama
from ai_service import AIServiceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerendipityServiceError(Exception):
    """Custom exception for serendipity service errors"""
    pass

class SerendipityService:
    """
    Serendipity engine service for discovering unexpected connections in memory data
    """
    
    def __init__(self, model: str = "llama3:8b", memory_file: str = "memory.json"):
        """
        Initialize the serendipity service
        
        Args:
            model: The Ollama model to use for connection analysis
            memory_file: Path to the memory storage file
        """
        self.model = model
        self.memory_file = memory_file
        self.connection_prompt = self._get_connection_discovery_prompt()
    
    def _get_connection_discovery_prompt(self) -> str:
        """Get the specialized prompt for connection discovery"""
        return """You are an expert at discovering unexpected connections, patterns, and insights across diverse topics and ideas.

Your task is to analyze the provided insights and conversation data to find surprising, meaningful connections that the user might not have noticed. Look for:

- Unexpected relationships between seemingly unrelated topics
- Recurring patterns across different conversations
- Hidden themes that connect various interests
- Contradictions or tensions in thinking patterns
- Evolution of ideas over time
- Cross-domain applications of concepts
- Serendipitous overlaps between different areas of interest

CRITICAL: You must respond with ONLY a valid JSON object. Do not include any explanatory text, comments, or formatting outside the JSON.

Respond with this exact JSON structure:
{
  "connections": [
    {
      "title": "string (catchy, intriguing title for the connection)",
      "description": "string (detailed explanation of the unexpected connection)",
      "surprise_factor": number (0.0 to 1.0, how surprising/unexpected this connection is),
      "relevance": number (0.0 to 1.0, how relevant/meaningful this connection is),
      "connected_insights": ["array", "of", "insight", "IDs", "or", "categories"],
      "connection_type": "string (e.g., 'pattern', 'contradiction', 'evolution', 'cross-domain', 'hidden_theme')",
      "actionable_insight": "string (what the user can do with this connection)"
    }
  ],
  "meta_patterns": [
    {
      "pattern_name": "string (name of the overarching pattern)",
      "description": "string (description of the meta-pattern across all data)",
      "evidence_count": number (how many insights support this pattern),
      "confidence": number (0.0 to 1.0, confidence in this meta-pattern)"
    }
  ],
  "serendipity_summary": "string (overall summary of the most interesting discoveries)",
  "recommendations": [
    "string (actionable recommendations based on discovered connections)"
  ]
}

Focus on connections that are:
- Genuinely surprising and non-obvious
- Intellectually stimulating and thought-provoking
- Actionable or practically useful
- Reveal deeper patterns in thinking or interests

If there isn't enough data for meaningful connections, be honest about it but still try to find at least some interesting patterns or suggest what kinds of conversations might reveal more connections.

Remember: Respond with ONLY the JSON object, no other text."""

    def discover_connections(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Discover unexpected connections in memory data using AI analysis
        
        Args:
            memory_data: Complete memory data including insights and summaries
            
        Returns:
            dict: Discovered connections and patterns
            
        Raises:
            SerendipityServiceError: If there's an error during connection discovery
        """
        try:
            # Prepare the memory data for analysis
            analysis_text = self._format_memory_for_analysis(memory_data)
            
            # Check if there's enough data for meaningful analysis
            insights_count = len(memory_data.get('insights', []))
            if insights_count < 3:
                return self._generate_insufficient_data_response(insights_count)
            
            # Prepare messages for connection discovery
            messages = [
                {"role": "system", "content": self.connection_prompt},
                {"role": "user", "content": f"Please analyze this memory data and discover unexpected connections:\n\n{analysis_text}"}
            ]
            
            logger.info(f"Discovering connections from memory data with {insights_count} insights")
            
            # Make the API call to Ollama for connection discovery
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            # Extract the response content
            ai_response = response['message']['content']
            logger.info(f"Received connection discovery response: {len(ai_response)} characters")
            
            # Parse the JSON response
            try:
                # Try to extract JSON from the response if it contains extra text
                cleaned_response = self._extract_json_from_response(ai_response)
                connections_data = json.loads(cleaned_response)
                
                # Validate the response structure
                if not isinstance(connections_data, dict):
                    raise SerendipityServiceError("AI response is not a valid JSON object")
                
                if 'connections' not in connections_data:
                    raise SerendipityServiceError("AI response missing 'connections' field")
                
                if not isinstance(connections_data['connections'], list):
                    raise SerendipityServiceError("'connections' field must be a list")
                
                # Add metadata to connections
                connections_data['analysis_metadata'] = {
                    'timestamp': datetime.now().isoformat(),
                    'model_used': self.model,
                    'insights_analyzed': insights_count,
                    'conversations_analyzed': len(memory_data.get('conversation_summaries', []))
                }
                
                logger.info(f"Successfully discovered {len(connections_data['connections'])} connections")
                return connections_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"AI response was: {ai_response[:500]}...")
                raise SerendipityServiceError(f"AI returned invalid JSON: {e}")
            
        except ollama.ResponseError as e:
            logger.error(f"Ollama API error during connection discovery: {e}")
            raise SerendipityServiceError(f"AI communication failed during connection discovery: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during connection discovery: {e}")
            raise SerendipityServiceError(f"Unexpected error during connection discovery: {e}")
    
    def _format_memory_for_analysis(self, memory_data: Dict[str, Any]) -> str:
        """
        Format memory data for AI analysis
        
        Args:
            memory_data: Complete memory data
            
        Returns:
            str: Formatted memory text for analysis
        """
        formatted_sections = []
        
        # Add insights section
        insights = memory_data.get('insights', [])
        if insights:
            formatted_sections.append("=== INSIGHTS ===")
            for i, insight in enumerate(insights):
                formatted_sections.append(f"Insight {i+1}:")
                formatted_sections.append(f"  Category: {insight.get('category', 'unknown')}")
                formatted_sections.append(f"  Content: {insight.get('content', '')}")
                formatted_sections.append(f"  Confidence: {insight.get('confidence', 0)}")
                formatted_sections.append(f"  Tags: {', '.join(insight.get('tags', []))}")
                formatted_sections.append(f"  Evidence: {insight.get('evidence', '')}")
                formatted_sections.append(f"  Timestamp: {insight.get('timestamp', '')}")
                formatted_sections.append("")
        
        # Add conversation summaries section
        summaries = memory_data.get('conversation_summaries', [])
        if summaries:
            formatted_sections.append("=== CONVERSATION SUMMARIES ===")
            for i, summary in enumerate(summaries):
                formatted_sections.append(f"Conversation {i+1}:")
                formatted_sections.append(f"  Summary: {summary.get('summary', '')}")
                formatted_sections.append(f"  Key Themes: {', '.join(summary.get('key_themes', []))}")
                formatted_sections.append(f"  Timestamp: {summary.get('timestamp', '')}")
                formatted_sections.append("")
        
        # Add metadata section
        metadata = memory_data.get('metadata', {})
        if metadata:
            formatted_sections.append("=== METADATA ===")
            formatted_sections.append(f"Total Insights: {metadata.get('total_insights', 0)}")
            formatted_sections.append(f"Last Updated: {metadata.get('last_updated', '')}")
            formatted_sections.append("")
        
        return "\n".join(formatted_sections)
    
    def _generate_insufficient_data_response(self, insights_count: int) -> Dict[str, Any]:
        """
        Generate a response when there's insufficient data for meaningful connections
        
        Args:
            insights_count: Number of insights available
            
        Returns:
            dict: Response indicating insufficient data with suggestions
        """
        return {
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": f"With only {insights_count} insights available, there isn't enough data yet to discover meaningful connections. Keep having conversations to build up your cognitive memory!",
            "recommendations": [
                "Continue having diverse conversations to build up your insight database",
                "Try discussing different topics to create more varied insights",
                "Return to the serendipity engine after you have at least 5-10 insights",
                "Consider exploring topics that connect to your existing interests"
            ],
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model,
                "insights_analyzed": insights_count,
                "insufficient_data": True
            }
        }
    
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
    
    def load_memory_data(self) -> Dict[str, Any]:
        """
        Load complete memory data from file
        
        Returns:
            dict: Complete memory data
            
        Raises:
            SerendipityServiceError: If there's an error loading memory data
        """
        if not os.path.exists(self.memory_file):
            logger.warning(f"Memory file {self.memory_file} does not exist")
            raise SerendipityServiceError(f"Memory file {self.memory_file} not found. Start some conversations to build memory first.")
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded memory file with {len(data.get('insights', []))} insights")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Memory file {self.memory_file} contains invalid JSON: {e}")
            raise SerendipityServiceError(f"Memory file is corrupted: {e}")
        except Exception as e:
            logger.error(f"Error reading memory file: {e}")
            raise SerendipityServiceError(f"Failed to read memory file: {e}")
    
    def analyze_memory(self) -> Dict[str, Any]:
        """
        Complete serendipity analysis workflow: load memory and discover connections
        
        Returns:
            dict: Discovered connections and analysis results
            
        Raises:
            SerendipityServiceError: If there's an error during analysis
        """
        try:
            # Load memory data
            memory_data = self.load_memory_data()
            
            # Discover connections
            connections_data = self.discover_connections(memory_data)
            
            return connections_data
            
        except Exception as e:
            logger.error(f"Error during serendipity analysis: {e}")
            raise SerendipityServiceError(f"Failed to analyze memory for connections: {e}")

# Global serendipity service instance
_serendipity_service_instance = None

def get_serendipity_service(model: str = "llama3:8b", memory_file: str = "memory.json") -> SerendipityService:
    """
    Get or create the global serendipity service instance
    
    Args:
        model: The Ollama model to use for connection analysis
        memory_file: Path to the memory storage file
        
    Returns:
        SerendipityService: The serendipity service instance
    """
    global _serendipity_service_instance
    
    if _serendipity_service_instance is None:
        _serendipity_service_instance = SerendipityService(model=model, memory_file=memory_file)
    
    return _serendipity_service_instance

def reset_serendipity_service():
    """Reset the global serendipity service instance (useful for testing)"""
    global _serendipity_service_instance
    _serendipity_service_instance = None