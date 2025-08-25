"""
Serendipity Service Module for Synapse AI Web Application

This module provides AI-powered serendipity analysis functionality that discovers
hidden connections, patterns, and insights within a user's accumulated memory data.
It integrates seamlessly with the existing Synapse project architecture.
"""

import json
import logging
import time
import hashlib
import threading
import sys
import platform
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict

from config import get_config
from error_handler import (
    get_error_handler, 
    ErrorCategory, 
    ErrorSeverity, 
    handle_service_error,
    safe_file_operation,
    RecoveryManager
)
from ai_service import get_ai_service, AIServiceError
from performance_monitor import get_performance_monitor
from enhanced_cache import get_cache_manager, CacheConfiguration
from analysis_queue import get_analysis_queue, RequestPriority, QueueConfiguration

# Configure logging
logger = logging.getLogger(__name__)

class SerendipityServiceError(Exception):
    """Custom exception for serendipity service errors"""
    pass

class InsufficientDataError(SerendipityServiceError):
    """Raised when there's insufficient data for analysis"""
    pass

class DataValidationError(SerendipityServiceError):
    """Raised when data validation fails"""
    pass

class MemoryProcessingError(SerendipityServiceError):
    """Raised when memory processing fails"""
    pass

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    data: Any
    timestamp: datetime
    ttl_seconds: int
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)
    
    def access(self) -> Any:
        """Access cached data and increment access count"""
        self.access_count += 1
        return self.data

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    insights_count: int = 0
    conversations_count: int = 0
    total_content_length: int = 0
    categories: List[str] = field(default_factory=list)

@dataclass
class MemoryChunk:
    """Represents a chunk of memory data for processing"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    size_bytes: int
    insights_count: int
    conversations_count: int

class SerendipityService:
    """
    AI-powered serendipity analysis service for discovering hidden connections
    and patterns within user's memory data.
    """
    
    def __init__(self, config=None):
        """
        Initialize the serendipity service
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or get_config()
        self.error_handler = get_error_handler()
        self.ai_service = None
        self._initialize_ai_service()
        
        # Analysis configuration from config
        self.min_insights_required = self.config.SERENDIPITY_MIN_INSIGHTS
        self.max_memory_size_mb = self.config.SERENDIPITY_MAX_MEMORY_SIZE_MB
        self.analysis_timeout = self.config.SERENDIPITY_ANALYSIS_TIMEOUT
        self.analysis_cache_ttl = getattr(self.config, 'SERENDIPITY_ANALYSIS_CACHE_TTL', 1800)
        
        # Performance monitoring
        self.performance_monitor = get_performance_monitor(self.config)
        
        # Enhanced multi-level caching system
        self.cache_manager = get_cache_manager()
        
        # Configure caches with optimized settings
        memory_cache_config = CacheConfiguration(
            max_entries=getattr(self.config, 'SERENDIPITY_MEMORY_CACHE_MAX_ENTRIES', 500),
            max_size_mb=getattr(self.config, 'SERENDIPITY_MEMORY_CACHE_MAX_SIZE_MB', 50.0),
            default_ttl_seconds=getattr(self.config, 'SERENDIPITY_MEMORY_CACHE_TTL', 3600),
            enable_compression=True,
            eviction_policy="lru"
        )
        
        analysis_cache_config = CacheConfiguration(
            max_entries=getattr(self.config, 'SERENDIPITY_ANALYSIS_CACHE_MAX_ENTRIES', 100),
            max_size_mb=getattr(self.config, 'SERENDIPITY_ANALYSIS_CACHE_MAX_SIZE_MB', 200.0),
            default_ttl_seconds=getattr(self.config, 'SERENDIPITY_ANALYSIS_CACHE_TTL', 1800),
            enable_compression=True,
            eviction_policy="ttl"
        )
        
        formatted_cache_config = CacheConfiguration(
            max_entries=getattr(self.config, 'SERENDIPITY_FORMATTED_CACHE_MAX_ENTRIES', 200),
            max_size_mb=getattr(self.config, 'SERENDIPITY_FORMATTED_CACHE_MAX_SIZE_MB', 100.0),
            default_ttl_seconds=getattr(self.config, 'SERENDIPITY_FORMATTED_CACHE_TTL', 1800),
            enable_compression=True,
            eviction_policy="lru"
        )
        
        # Get enhanced caches
        self.memory_cache = self.cache_manager.get_cache("memory_cache", memory_cache_config)
        self.analysis_cache = self.cache_manager.get_cache("analysis_cache", analysis_cache_config)
        self.formatted_cache = self.cache_manager.get_cache("formatted_cache", formatted_cache_config)
        
        # Queue management for concurrent requests
        queue_config = QueueConfiguration(
            max_queue_size=getattr(self.config, 'SERENDIPITY_MAX_QUEUE_SIZE', 100),
            max_concurrent_workers=getattr(self.config, 'SERENDIPITY_MAX_CONCURRENT_WORKERS', 3),
            worker_timeout_seconds=getattr(self.config, 'SERENDIPITY_WORKER_TIMEOUT', 300),
            queue_timeout_seconds=getattr(self.config, 'SERENDIPITY_QUEUE_TIMEOUT', 600),
            enable_adaptive_scaling=True,
            enable_priority_boosting=True
        )
        
        self.analysis_queue = get_analysis_queue(queue_config, self)
        
        # Chunking configuration
        self.max_chunk_size_chars = getattr(self.config, 'SERENDIPITY_MAX_CHUNK_SIZE', 8000)
        self.chunk_overlap_chars = getattr(self.config, 'SERENDIPITY_CHUNK_OVERLAP', 200)
        
        # Legacy cache support (for backward compatibility)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._analysis_cache: Dict[str, CacheEntry] = {}
        self._formatted_cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.RLock()
        
        logger.info("SerendipityService initialized successfully with enhanced caching, performance monitoring, and queue management")
    
    def _initialize_ai_service(self):
        """Initialize AI service with error handling"""
        try:
            if not self.config.ENABLE_SERENDIPITY_ENGINE:
                logger.info("Serendipity engine is disabled via configuration")
                return
            
            self.ai_service = get_ai_service(
                model=self.config.OLLAMA_MODEL,
                system_prompt=self._get_serendipity_system_prompt()
            )
            logger.info(f"AI service initialized for serendipity analysis with model: {self.config.OLLAMA_MODEL}")
            
        except Exception as e:
            self.error_handler.log_error(
                e,
                ErrorCategory.SERENDIPITY_SERVICE,
                ErrorSeverity.HIGH,
                {"component": "ai_service_initialization"}
            )
            self.ai_service = None
    
    def _get_serendipity_system_prompt(self) -> str:
        """Get specialized system prompt for serendipity analysis with examples"""
        return """You are an expert cognitive analyst specializing in discovering non-obvious connections, hidden patterns, and serendipitous insights within personal knowledge and experiences. Your task is to analyze a user's accumulated thoughts, insights, and conversation summaries to identify meaningful connections that might not be immediately apparent.

Focus on finding:
1. Cross-domain connections between seemingly unrelated topics
2. Recurring themes and patterns across different time periods
3. Contradictions or tensions that reveal deeper insights
4. Emergent ideas that arise from the intersection of multiple concepts
5. Hidden assumptions or biases that shape thinking patterns
6. Potential blind spots or unexplored areas
7. Serendipitous opportunities for new directions or investigations

EXAMPLES OF GOOD CONNECTIONS:
- A person interested in both cooking and software development might have a hidden pattern of "systematic experimentation" - they approach both domains by testing small variations and iterating based on results
- Someone with insights about time management and gardening might discover they both reflect a deeper theme of "nurturing growth through consistent small actions"
- A contradiction between valuing efficiency and also enjoying slow, contemplative activities might reveal an underlying need for "balanced rhythms" in life
- Cross-domain: Insights about music theory connecting to mathematical thinking patterns
- Temporal: Early career focus on individual achievement evolving into later emphasis on collaboration, suggesting a maturation pattern
- Emergent: Multiple conversations about different topics all touching on themes of authenticity, suggesting this as a core value

Your analysis should be:
- Intellectually rigorous and evidence-based
- Surprising yet plausible (high surprise_factor for non-obvious connections)
- Actionable and personally relevant (high relevance for practical insights)
- Grounded in the actual data provided
- Specific about which insights support each connection

CRITICAL: Return ONLY valid JSON. No additional text before or after. Use this exact structure:
{
  "connections": [
    {
      "title": "Brief descriptive title (max 60 chars)",
      "description": "Detailed explanation of the connection and why it's meaningful",
      "surprise_factor": 0.8,
      "relevance": 0.9,
      "connected_insights": ["specific insight text 1", "specific insight text 2"],
      "connection_type": "cross_domain|temporal|contradictory|emergent|thematic",
      "actionable_insight": "Specific action the user could take based on this connection"
    }
  ],
  "meta_patterns": [
    {
      "pattern_name": "Name of the overarching pattern",
      "description": "Description of the pattern and its significance",
      "evidence_count": 5,
      "confidence": 0.85
    }
  ],
  "serendipity_summary": "Overall summary of the most interesting discoveries and their implications",
  "recommendations": ["Specific actionable recommendation 1", "Specific actionable recommendation 2"]
}

IMPORTANT GUIDELINES:
- Return ONLY the JSON object, no other text
- If you find fewer than 3 insights, still look for at least 1-2 connections 
- For small datasets, focus on quality over quantity
- All numeric values must be between 0.0 and 1.0
- Ensure proper JSON syntax with quotes around all strings
- If no meaningful connections exist, return empty arrays but maintain JSON structure"""
    
    def analyze_memory(self, memory_file_path: Optional[str] = None, 
                      priority: RequestPriority = RequestPriority.NORMAL,
                      use_queue: bool = False) -> Dict[str, Any]:
        """
        Perform serendipity analysis on user's memory data
        
        Args:
            memory_file_path: Path to memory file (uses config default if None)
            priority: Request priority for queue processing
            use_queue: Whether to use queue for processing (for concurrent requests)
            
        Returns:
            dict: Analysis results with connections, patterns, and recommendations
            
        Raises:
            SerendipityServiceError: If analysis fails or service is disabled
        """
        # Start performance monitoring
        operation_id = self.performance_monitor.start_operation(
            "serendipity_analysis",
            {"memory_file": memory_file_path, "priority": priority.name if hasattr(priority, 'name') else str(priority)}
        )
        
        start_time = time.time()
        cache_hits = 0
        cache_misses = 0
        
        try:
            # Check if serendipity engine is enabled
            if not self.config.ENABLE_SERENDIPITY_ENGINE:
                raise SerendipityServiceError("Serendipity engine is disabled. Enable it by setting ENABLE_SERENDIPITY_ENGINE=True")
            
            if not self.ai_service:
                raise SerendipityServiceError("AI service is not available. Please ensure Ollama is running and properly configured")
            
            # If using queue, submit request and return immediately
            if use_queue:
                request_id = self.analysis_queue.submit_request(
                    memory_file_path=memory_file_path,
                    priority=priority,
                    metadata={"operation_id": operation_id}
                )
                return {
                    "status": "queued",
                    "request_id": request_id,
                    "message": "Analysis request queued for processing"
                }
            
            # Load and validate memory data with caching
            memory_data = self._load_memory_data_enhanced(memory_file_path)
            if memory_data.get("_cache_hit"):
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Validate sufficient data for analysis
            self._validate_memory_data(memory_data)
            
            # Format memory data for AI analysis with caching
            formatted_memory = self._format_memory_for_analysis_enhanced(memory_data)
            if formatted_memory.get("_cache_hit") if isinstance(formatted_memory, dict) else False:
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Extract actual formatted data
            if isinstance(formatted_memory, dict) and "_data" in formatted_memory:
                formatted_data = formatted_memory["_data"]
            else:
                formatted_data = formatted_memory
            
            # Check analysis cache first
            analysis_cache_key = self._generate_analysis_cache_key(formatted_data)
            cached_analysis = self.analysis_cache.get(analysis_cache_key)
            
            if cached_analysis:
                cache_hits += 1
                analysis_results = cached_analysis
                logger.info("Using cached analysis results")
            else:
                cache_misses += 1
                
                # Perform AI analysis (handle both string and chunked data)
                if isinstance(formatted_data, list):
                    # Handle chunked data
                    analysis_results = self._discover_connections_chunked(formatted_data)
                else:
                    # Handle single string data
                    analysis_results = self._discover_connections(formatted_data)
                
                # Cache the analysis results
                self.analysis_cache.put(analysis_cache_key, analysis_results)
            
            # Add comprehensive metadata with performance tracking
            analysis_results["metadata"] = self._generate_analysis_metadata_enhanced(
                memory_data, formatted_data, start_time, analysis_results, cache_hits, cache_misses
            )
            
            # Add patterns alias for backward compatibility 
            if "meta_patterns" in analysis_results and "patterns" not in analysis_results:
                analysis_results["patterns"] = analysis_results["meta_patterns"]
            
            # Store analysis in history
            self._store_analysis_history(analysis_results)
            
            # Track usage analytics
            self._track_usage_analytics(analysis_results)
            
            # Complete performance monitoring
            self.performance_monitor.complete_operation(
                operation_id,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                ai_response_time=analysis_results["metadata"].get("ai_response_time"),
                data_size_mb=analysis_results["metadata"].get("data_size_mb", 0),
                chunk_count=analysis_results["metadata"].get("chunk_count", 0)
            )
            
            logger.info(f"Serendipity analysis completed in {analysis_results['metadata']['analysis_duration']}s")
            return analysis_results
            
        except Exception as e:
            # Complete performance monitoring with error
            self.performance_monitor.complete_operation(
                operation_id,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                error=e
            )
            raise
    
    def _load_memory_data(self, memory_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and validate memory data from file with caching support
        
        Args:
            memory_file_path: Path to memory file
            
        Returns:
            dict: Loaded and validated memory data
            
        Raises:
            SerendipityServiceError: If file cannot be loaded or is invalid
        """
        file_path = memory_file_path or self.config.MEMORY_FILE
        
        # Generate cache key based on file path and modification time
        cache_key = self._generate_memory_cache_key(file_path)
        
        # Check cache first
        with self._cache_lock:
            if cache_key in self._memory_cache:
                cache_entry = self._memory_cache[cache_key]
                if not cache_entry.is_expired():
                    logger.info(f"Using cached memory data for {file_path}")
                    return cache_entry.access()
                else:
                    # Remove expired entry
                    del self._memory_cache[cache_key]
        
        # Load from file
        memory_data = self._load_memory_from_file(file_path)
        
        # Validate the loaded data
        validation_result = self._validate_memory_data_comprehensive(memory_data)
        
        if not validation_result.is_valid:
            # Check if it's an insufficient data error specifically
            if any("insufficient data" in error.lower() for error in validation_result.errors):
                error_msg = f"Insufficient data for serendipity analysis. Found {validation_result.insights_count + validation_result.conversations_count} items, but need at least {self.min_insights_required}. Have more conversations to build up your memory for better analysis."
                raise InsufficientDataError(error_msg)
            else:
                error_msg = f"Memory data validation failed: {'; '.join(validation_result.errors)}"
                raise DataValidationError(error_msg)
        
        # Log warnings if any
        for warning in validation_result.warnings:
            logger.warning(f"Memory data warning: {warning}")
        
        # Cache the validated data (using legacy cache for backward compatibility)
        with self._cache_lock:
            self._memory_cache[cache_key] = CacheEntry(
                data=memory_data,
                timestamp=datetime.now(),
                ttl_seconds=getattr(self.config, 'SERENDIPITY_MEMORY_CACHE_TTL', 3600)
            )
        
        logger.info(f"Loaded and cached memory data: {validation_result.insights_count} insights, "
                   f"{validation_result.conversations_count} conversations, "
                   f"{len(validation_result.categories)} categories")
        
        return memory_data
    
    def _load_memory_data_enhanced(self, memory_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced memory data loading with improved caching
        
        Args:
            memory_file_path: Path to memory file
            
        Returns:
            dict: Loaded memory data with cache metadata
        """
        file_path = memory_file_path or self.config.MEMORY_FILE
        
        # Generate cache key based on file path and modification time
        cache_key = self._generate_memory_cache_key(file_path)
        
        # Check enhanced cache first
        cached_data = self.memory_cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Using enhanced cached memory data for {file_path}")
            cached_data["_cache_hit"] = True
            return cached_data
        
        # Load from file using original method
        memory_data = self._load_memory_data(file_path)
        
        # Cache in enhanced cache
        self.memory_cache.put(cache_key, memory_data)
        
        memory_data["_cache_hit"] = False
        return memory_data
    
    def _format_memory_for_analysis_enhanced(self, memory_data: Dict[str, Any]) -> Union[str, List[MemoryChunk], Dict[str, Any]]:
        """
        Enhanced memory formatting with improved caching
        
        Args:
            memory_data: Raw memory data
            
        Returns:
            Formatted memory data with cache metadata
        """
        # Generate cache key for formatted data
        cache_key = self._generate_formatted_cache_key(memory_data)
        
        # Check enhanced cache first
        cached_formatted = self.formatted_cache.get(cache_key)
        
        if cached_formatted:
            logger.info("Using enhanced cached formatted memory data")
            return {
                "_data": cached_formatted,
                "_cache_hit": True
            }
        
        # Format using original method
        formatted_result = self._format_memory_for_analysis(memory_data)
        
        # Cache in enhanced cache
        self.formatted_cache.put(cache_key, formatted_result)
        
        return {
            "_data": formatted_result,
            "_cache_hit": False
        }
    
    def _generate_analysis_cache_key(self, formatted_data: Union[str, List[MemoryChunk]]) -> str:
        """
        Generate cache key for analysis results
        
        Args:
            formatted_data: Formatted memory data
            
        Returns:
            str: Cache key
        """
        try:
            if isinstance(formatted_data, str):
                content_hash = hashlib.md5(formatted_data.encode()).hexdigest()
            elif isinstance(formatted_data, list):
                # Hash all chunks
                combined_content = ""
                for chunk in formatted_data:
                    if hasattr(chunk, 'content'):
                        combined_content += chunk.content
                content_hash = hashlib.md5(combined_content.encode()).hexdigest()
            else:
                content_hash = hashlib.md5(str(formatted_data).encode()).hexdigest()
            
            # Include model and configuration in key
            key_data = f"analysis_{content_hash}_{self.config.OLLAMA_MODEL}_{self.analysis_timeout}"
            return hashlib.md5(key_data.encode()).hexdigest()
            
        except Exception as e:
            logger.warning(f"Failed to generate analysis cache key: {e}")
            return hashlib.md5(f"fallback_analysis_{time.time()}".encode()).hexdigest()
    
    def _generate_analysis_metadata_enhanced(self, memory_data: Dict[str, Any], 
                                           formatted_memory: Union[str, List[MemoryChunk]], 
                                           start_time: float, 
                                           analysis_results: Dict[str, Any],
                                           cache_hits: int = 0,
                                           cache_misses: int = 0) -> Dict[str, Any]:
        """
        Generate enhanced analysis metadata with performance metrics
        
        Args:
            memory_data: Original memory data
            formatted_memory: Formatted memory data
            start_time: Analysis start time
            analysis_results: Analysis results
            cache_hits: Number of cache hits
            cache_misses: Number of cache misses
            
        Returns:
            dict: Enhanced metadata
        """
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate data size
        data_size_mb = 0.0
        chunk_count = 0
        
        if isinstance(formatted_memory, str):
            data_size_mb = len(formatted_memory.encode('utf-8')) / (1024 * 1024)
            chunk_count = 1
        elif isinstance(formatted_memory, list):
            total_size = sum(chunk.size_bytes for chunk in formatted_memory if hasattr(chunk, 'size_bytes'))
            data_size_mb = total_size / (1024 * 1024)
            chunk_count = len(formatted_memory)
        
        # Get system resource info
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
        except Exception:
            memory_info = None
            cpu_percent = 0.0
        
        # Get cache statistics
        cache_stats = {
            "hits": cache_hits,
            "misses": cache_misses,
            "hit_rate": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0.0,
            "memory_cache_stats": self.memory_cache.get_statistics(),
            "analysis_cache_stats": self.analysis_cache.get_statistics(),
            "formatted_cache_stats": self.formatted_cache.get_statistics()
        }
        
        # Get queue statistics if available
        queue_stats = {}
        try:
            queue_stats = self.analysis_queue.get_queue_statistics()
        except Exception as e:
            logger.debug(f"Could not get queue statistics: {e}")
        
        metadata = {
            "analysis_duration": duration,
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_model": self.config.OLLAMA_MODEL,
            "data_size_mb": data_size_mb,
            "chunk_count": chunk_count,
            "insights_processed": len(memory_data.get("insights", [])),
            "conversations_processed": len(memory_data.get("conversation_summaries", [])),
            "cache_stats": cache_stats,
            "queue_stats": queue_stats,
            "performance_metrics": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "operations_per_second": 1 / duration if duration > 0 else 0,
                "memory_usage_mb": memory_info.rss / (1024 * 1024) if memory_info else 0,
                "cpu_usage_percent": cpu_percent
            },
            "system_info": {
                "platform": platform.system(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "thread_count": threading.active_count()
            }
        }
        
        # Add AI response time if available
        if "ai_response_time" in analysis_results.get("metadata", {}):
            metadata["ai_response_time"] = analysis_results["metadata"]["ai_response_time"]
        
        return metadata
    
    def _load_memory_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load memory data from file with comprehensive error handling
        
        Args:
            file_path: Path to memory file
            
        Returns:
            dict: Raw memory data
            
        Raises:
            SerendipityServiceError: If file cannot be loaded
        """
        # Check if file exists
        if not Path(file_path).exists():
            raise SerendipityServiceError(f"Memory file not found: {file_path}")
        
        try:
            # Check file size and permissions
            file_stat = Path(file_path).stat()
            file_size_mb = file_stat.st_size / (1024 * 1024)
            
            if file_size_mb > self.max_memory_size_mb:
                logger.warning(f"Memory file is large ({file_size_mb:.1f}MB), analysis may be slow")
            
            if file_stat.st_size == 0:
                raise SerendipityServiceError(f"Memory file is empty: {file_path}")
            
            # Load JSON with error recovery
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    memory_data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error at line {e.lineno}, column {e.colno}: {e.msg}")
                    
                    # Attempt to recover corrupted JSON
                    f.seek(0)
                    content = f.read()
                    recovered_data = self._attempt_json_recovery(content, file_path)
                    
                    if recovered_data:
                        memory_data = recovered_data
                        logger.info("Successfully recovered corrupted JSON data")
                    else:
                        raise SerendipityServiceError(f"Failed to load memory file due to invalid JSON: {file_path}")
            
        except PermissionError:
            raise SerendipityServiceError(f"Permission denied accessing memory file: {file_path}")
        except FileNotFoundError:
            raise SerendipityServiceError(f"Memory file not found: {file_path}")
        except Exception as e:
            self.error_handler.log_error(
                e,
                ErrorCategory.SERENDIPITY_SERVICE,
                ErrorSeverity.MEDIUM,
                {"file_path": file_path}
            )
            raise SerendipityServiceError(f"Failed to load memory file: {file_path}")
        
        # Basic structure validation
        if not isinstance(memory_data, dict):
            raise SerendipityServiceError("Memory file must contain a JSON object")
        
        # Ensure required keys exist with defaults
        if "insights" not in memory_data:
            memory_data["insights"] = []
            logger.warning("Memory file missing 'insights' key, using empty list")
        
        if "conversation_summaries" not in memory_data:
            memory_data["conversation_summaries"] = []
            logger.warning("Memory file missing 'conversation_summaries' key, using empty list")
        
        if "metadata" not in memory_data:
            memory_data["metadata"] = {}
            logger.warning("Memory file missing 'metadata' key, using empty dict")
        
        return memory_data
    
    def _attempt_json_recovery(self, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover corrupted JSON data
        
        Args:
            content: Raw file content
            file_path: Path to the file for logging
            
        Returns:
            dict or None: Recovered data if successful
        """
        try:
            # Try to find and fix common JSON issues
            
            # Remove trailing commas
            import re
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            # Try to parse again
            recovered_data = json.loads(content)
            logger.info(f"Successfully recovered JSON by removing trailing commas: {file_path}")
            return recovered_data
            
        except json.JSONDecodeError:
            pass
        
        try:
            # Try to extract valid JSON portion
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                partial_content = content[start_idx:end_idx + 1]
                recovered_data = json.loads(partial_content)
                logger.info(f"Successfully recovered partial JSON data: {file_path}")
                return recovered_data
                
        except json.JSONDecodeError:
            pass
        
        # If all recovery attempts fail, create minimal structure
        logger.warning(f"Could not recover JSON data, creating minimal structure: {file_path}")
        return {
            "insights": [],
            "conversation_summaries": [],
            "metadata": {
                "recovery_note": f"Data recovered from corrupted file on {datetime.now().isoformat()}",
                "original_file": file_path
            }
        }
    
    def _generate_memory_cache_key(self, file_path: str) -> str:
        """
        Generate cache key based on file path and modification time
        
        Args:
            file_path: Path to memory file
            
        Returns:
            str: Cache key
        """
        try:
            file_stat = Path(file_path).stat()
            key_data = f"{file_path}:{file_stat.st_mtime}:{file_stat.st_size}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            # Fallback to just file path if stat fails
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def _validate_memory_data_comprehensive(self, memory_data: Dict[str, Any]) -> ValidationResult:
        """
        Comprehensive validation of memory data with detailed error reporting
        
        Args:
            memory_data: Memory data to validate
            
        Returns:
            ValidationResult: Detailed validation results
        """
        result = ValidationResult(is_valid=True)
        
        # Validate top-level structure
        if not isinstance(memory_data, dict):
            result.is_valid = False
            result.errors.append("Memory data must be a dictionary")
            return result
        
        # Validate insights
        insights = memory_data.get("insights", [])
        if not isinstance(insights, list):
            result.is_valid = False
            result.errors.append("'insights' must be a list")
        else:
            result.insights_count = len(insights)
            insight_validation = self._validate_insights(insights)
            result.errors.extend(insight_validation["errors"])
            result.warnings.extend(insight_validation["warnings"])
            result.categories.extend(insight_validation["categories"])
            result.total_content_length += insight_validation["content_length"]
        
        # Validate conversation summaries
        conversations = memory_data.get("conversation_summaries", [])
        if not isinstance(conversations, list):
            result.is_valid = False
            result.errors.append("'conversation_summaries' must be a list")
        else:
            result.conversations_count = len(conversations)
            conv_validation = self._validate_conversations(conversations)
            result.errors.extend(conv_validation["errors"])
            result.warnings.extend(conv_validation["warnings"])
            result.total_content_length += conv_validation["content_length"]
        
        # Validate metadata
        metadata = memory_data.get("metadata", {})
        if not isinstance(metadata, dict):
            result.warnings.append("'metadata' should be a dictionary")
        
        # Check for sufficient data
        total_items = result.insights_count + result.conversations_count
        if total_items < self.min_insights_required:
            result.is_valid = False
            result.errors.append(
                f"Insufficient data for analysis. Found {total_items} items, "
                f"need at least {self.min_insights_required}. "
                "Have more conversations to build up your memory."
            )
        
        # If we have validation errors but still some valid data, don't fail completely
        if result.errors and total_items >= self.min_insights_required:
            # Only fail if we have critical structural errors
            critical_errors = [e for e in result.errors if 
                             "must be a list" in e or "must be a dictionary" in e or 
                             "missing required field" in e or "has empty" in e]
            if not critical_errors:
                result.is_valid = True  # Allow warnings but not critical errors
        
        # Check for data quality issues
        if result.insights_count == 0 and result.conversations_count == 0:
            result.is_valid = False
            result.errors.append("No insights or conversation summaries found")
        
        if result.total_content_length < 100:
            result.warnings.append("Very little content available for analysis")
        
        # Check for category diversity
        if len(result.categories) < 2:
            result.warnings.append("Limited category diversity may reduce analysis quality")
        
        return result
    
    def _validate_insights(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate insights data structure and content
        
        Args:
            insights: List of insight dictionaries
            
        Returns:
            dict: Validation results with errors, warnings, categories, and content length
        """
        errors = []
        warnings = []
        categories = set()
        content_length = 0
        
        required_fields = ["content", "category"]
        optional_fields = ["confidence", "tags", "evidence", "timestamp"]
        
        for i, insight in enumerate(insights):
            if not isinstance(insight, dict):
                errors.append(f"Insight {i} is not a dictionary")
                continue
            
            # Check required fields
            for field in required_fields:
                if field not in insight:
                    errors.append(f"Insight {i} missing required field '{field}'")
                elif not insight[field] or (isinstance(insight[field], str) and not insight[field].strip()):
                    errors.append(f"Insight {i} has empty '{field}' field")
            
            # Validate content
            if "content" in insight:
                content = insight["content"]
                if isinstance(content, str):
                    content_length += len(content)
                    if len(content) < 10:
                        warnings.append(f"Insight {i} has very short content")
                    elif len(content) > 1000:
                        warnings.append(f"Insight {i} has very long content")
                else:
                    errors.append(f"Insight {i} content must be a string")
            
            # Validate category
            if "category" in insight:
                category = insight["category"]
                if isinstance(category, str):
                    categories.add(category.lower())
                    if not category.strip():
                        warnings.append(f"Insight {i} has empty category")
                else:
                    errors.append(f"Insight {i} category must be a string")
            
            # Validate confidence if present
            if "confidence" in insight:
                confidence = insight["confidence"]
                try:
                    conf_val = float(confidence)
                    if not (0.0 <= conf_val <= 1.0):
                        warnings.append(f"Insight {i} confidence out of range [0,1]: {conf_val}")
                except (ValueError, TypeError):
                    warnings.append(f"Insight {i} confidence must be a number")
            
            # Validate tags if present
            if "tags" in insight:
                tags = insight["tags"]
                if not isinstance(tags, list):
                    warnings.append(f"Insight {i} tags should be a list")
                elif len(tags) == 0:
                    warnings.append(f"Insight {i} has empty tags list")
            
            # Validate timestamp if present
            if "timestamp" in insight:
                timestamp = insight["timestamp"]
                if not isinstance(timestamp, str):
                    warnings.append(f"Insight {i} timestamp should be a string")
                else:
                    try:
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        warnings.append(f"Insight {i} has invalid timestamp format")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "categories": list(categories),
            "content_length": content_length
        }
    
    def _validate_conversations(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate conversation summaries data structure and content
        
        Args:
            conversations: List of conversation summary dictionaries
            
        Returns:
            dict: Validation results with errors, warnings, and content length
        """
        errors = []
        warnings = []
        content_length = 0
        
        required_fields = ["summary"]
        optional_fields = ["key_themes", "timestamp", "insights_count"]
        
        for i, conv in enumerate(conversations):
            if not isinstance(conv, dict):
                errors.append(f"Conversation {i} is not a dictionary")
                continue
            
            # Check required fields
            for field in required_fields:
                if field not in conv:
                    errors.append(f"Conversation {i} missing required field '{field}'")
                elif not conv[field] or (isinstance(conv[field], str) and not conv[field].strip()):
                    errors.append(f"Conversation {i} has empty '{field}' field")
            
            # Validate summary
            if "summary" in conv:
                summary = conv["summary"]
                if isinstance(summary, str):
                    content_length += len(summary)
                    if len(summary) < 20:
                        warnings.append(f"Conversation {i} has very short summary")
                    elif len(summary) > 2000:
                        warnings.append(f"Conversation {i} has very long summary")
                else:
                    errors.append(f"Conversation {i} summary must be a string")
            
            # Validate key_themes if present
            if "key_themes" in conv:
                themes = conv["key_themes"]
                if not isinstance(themes, list):
                    warnings.append(f"Conversation {i} key_themes should be a list")
                elif len(themes) == 0:
                    warnings.append(f"Conversation {i} has empty key_themes list")
            
            # Validate timestamp if present
            if "timestamp" in conv:
                timestamp = conv["timestamp"]
                if not isinstance(timestamp, str):
                    warnings.append(f"Conversation {i} timestamp should be a string")
                else:
                    try:
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        warnings.append(f"Conversation {i} has invalid timestamp format")
            
            # Validate insights_count if present
            if "insights_count" in conv:
                try:
                    count = int(conv["insights_count"])
                    if count < 0:
                        warnings.append(f"Conversation {i} insights_count cannot be negative")
                except (ValueError, TypeError):
                    warnings.append(f"Conversation {i} insights_count must be an integer")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "content_length": content_length
        }
    
    def _validate_memory_data(self, memory_data: Dict[str, Any]) -> None:
        """
        Legacy validation method for backward compatibility
        
        Args:
            memory_data: Memory data to validate
            
        Raises:
            InsufficientDataError: If data is insufficient for analysis
            DataValidationError: If data validation fails
        """
        validation_result = self._validate_memory_data_comprehensive(memory_data)
        
        if not validation_result.is_valid:
            if any("insufficient data" in error.lower() for error in validation_result.errors):
                raise InsufficientDataError("; ".join(validation_result.errors))
            else:
                raise DataValidationError("; ".join(validation_result.errors))
        
        # Log warnings
        for warning in validation_result.warnings:
            logger.warning(f"Memory data warning: {warning}")
        
        logger.info(f"Memory data validation passed: {validation_result.insights_count} insights, "
                   f"{validation_result.conversations_count} conversations")
    
    def _format_memory_for_analysis(self, memory_data: Dict[str, Any]) -> Union[str, List[MemoryChunk]]:
        """
        Format memory data for AI analysis with chunking support
        
        Args:
            memory_data: Raw memory data
            
        Returns:
            str or List[MemoryChunk]: Formatted memory text or chunks if data is large
        """
        # Generate cache key for formatted data
        cache_key = self._generate_formatted_cache_key(memory_data)
        
        # Check cache first
        with self._cache_lock:
            if cache_key in self._formatted_cache:
                cache_entry = self._formatted_cache[cache_key]
                if not cache_entry.is_expired():
                    logger.info("Using cached formatted memory data")
                    return cache_entry.access()
                else:
                    del self._formatted_cache[cache_key]
        
        # Format the memory data
        formatted_result = self._format_memory_data(memory_data)
        
        # Cache the result (using legacy cache for backward compatibility)
        with self._cache_lock:
            self._formatted_cache[cache_key] = CacheEntry(
                data=formatted_result,
                timestamp=datetime.now(),
                ttl_seconds=getattr(self.config, 'SERENDIPITY_FORMATTED_CACHE_TTL', 1800)
            )
        
        return formatted_result
    
    def _format_memory_data(self, memory_data: Dict[str, Any]) -> Union[str, List[MemoryChunk]]:
        """
        Core memory formatting logic with intelligent chunking
        
        Args:
            memory_data: Raw memory data
            
        Returns:
            str or List[MemoryChunk]: Formatted memory or chunks
        """
        formatted_sections = []
        
        # Format insights section
        insights_content = self._format_insights_section(memory_data.get("insights", []))
        if insights_content:
            formatted_sections.append(insights_content)
        
        # Format conversations section
        conversations_content = self._format_conversations_section(memory_data.get("conversation_summaries", []))
        if conversations_content:
            formatted_sections.append(conversations_content)
        
        # Format metadata section
        metadata_content = self._format_metadata_section(memory_data.get("metadata", {}))
        if metadata_content:
            formatted_sections.append(metadata_content)
        
        # Combine all sections
        full_formatted_memory = "\n\n".join(formatted_sections)
        
        # Check if chunking is needed
        if len(full_formatted_memory) > self.max_chunk_size_chars:
            logger.info(f"Memory data is large ({len(full_formatted_memory)} chars), creating chunks")
            chunks = self._create_memory_chunks(formatted_sections, memory_data)
            return chunks
        else:
            logger.info(f"Formatted memory data: {len(full_formatted_memory)} characters")
            return full_formatted_memory
    
    def _format_insights_section(self, insights: List[Dict[str, Any]]) -> str:
        """
        Format insights section with enhanced metadata
        
        Args:
            insights: List of insight dictionaries
            
        Returns:
            str: Formatted insights section
        """
        if not insights:
            return ""
        
        sections = ["=== INSIGHTS AND KNOWLEDGE ==="]
        
        # Group insights by category with statistics
        insights_by_category = defaultdict(list)
        category_stats = defaultdict(lambda: {"count": 0, "avg_confidence": 0.0, "total_confidence": 0.0})
        
        for insight in insights:
            if not isinstance(insight, dict) or "content" not in insight:
                continue
            
            category = insight.get("category", "uncategorized").lower()
            insights_by_category[category].append(insight)
            
            # Update category statistics
            category_stats[category]["count"] += 1
            if "confidence" in insight:
                try:
                    conf = float(insight["confidence"])
                    category_stats[category]["total_confidence"] += conf
                except (ValueError, TypeError):
                    pass
        
        # Calculate average confidence for each category
        for category in category_stats:
            if category_stats[category]["count"] > 0:
                category_stats[category]["avg_confidence"] = (
                    category_stats[category]["total_confidence"] / category_stats[category]["count"]
                )
        
        # Sort categories by count and confidence
        sorted_categories = sorted(
            insights_by_category.keys(),
            key=lambda cat: (category_stats[cat]["count"], category_stats[cat]["avg_confidence"]),
            reverse=True
        )
        
        # Format each category
        for category in sorted_categories:
            category_insights = insights_by_category[category]
            stats = category_stats[category]
            
            # Category header with statistics
            category_header = f"\n{category.upper().replace('_', ' ')} ({stats['count']} insights"
            if stats["avg_confidence"] > 0:
                category_header += f", avg confidence: {stats['avg_confidence']:.2f}"
            category_header += "):"
            sections.append(category_header)
            
            # Sort insights within category by confidence and timestamp
            sorted_insights = sorted(
                category_insights,
                key=lambda x: (
                    x.get("confidence", 0.5),
                    x.get("timestamp", "")
                ),
                reverse=True
            )
            
            # Format individual insights
            for insight in sorted_insights:
                insight_text = f"• {insight['content']}"
                
                # Add metadata
                metadata_parts = []
                if "confidence" in insight:
                    try:
                        conf = float(insight["confidence"])
                        metadata_parts.append(f"confidence: {conf:.2f}")
                    except (ValueError, TypeError):
                        pass
                
                if "tags" in insight and insight["tags"]:
                    tags = insight["tags"]
                    if isinstance(tags, list) and tags:
                        metadata_parts.append(f"tags: {', '.join(tags[:3])}")  # Limit to first 3 tags
                
                if "timestamp" in insight:
                    timestamp = insight["timestamp"]
                    if isinstance(timestamp, str) and len(timestamp) >= 10:
                        metadata_parts.append(f"recorded: {timestamp[:10]}")
                
                if metadata_parts:
                    insight_text += f" ({'; '.join(metadata_parts)})"
                
                sections.append(insight_text)
        
        return "\n".join(sections)
    
    def _format_conversations_section(self, conversations: List[Dict[str, Any]]) -> str:
        """
        Format conversations section with enhanced metadata
        
        Args:
            conversations: List of conversation dictionaries
            
        Returns:
            str: Formatted conversations section
        """
        if not conversations:
            return ""
        
        sections = ["=== CONVERSATION SUMMARIES ==="]
        
        # Sort conversations by timestamp (most recent first)
        sorted_conversations = sorted(
            conversations,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        for i, conv in enumerate(sorted_conversations):
            if not isinstance(conv, dict) or "summary" not in conv:
                continue
            
            conv_text = f"\nConversation {i+1}: {conv['summary']}"
            
            # Add key themes
            if "key_themes" in conv and conv["key_themes"]:
                themes = conv["key_themes"]
                if isinstance(themes, list) and themes:
                    conv_text += f"\nKey themes: {', '.join(themes)}"
            
            # Add metadata
            metadata_parts = []
            if "timestamp" in conv:
                timestamp = conv["timestamp"]
                if isinstance(timestamp, str) and len(timestamp) >= 10:
                    metadata_parts.append(f"Date: {timestamp[:10]}")
            
            if "insights_count" in conv:
                try:
                    count = int(conv["insights_count"])
                    metadata_parts.append(f"Insights generated: {count}")
                except (ValueError, TypeError):
                    pass
            
            if metadata_parts:
                conv_text += f"\n{' | '.join(metadata_parts)}"
            
            sections.append(conv_text)
        
        return "\n".join(sections)
    
    def _format_metadata_section(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata section with comprehensive information
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            str: Formatted metadata section
        """
        if not metadata:
            return ""
        
        sections = ["=== MEMORY METADATA ==="]
        
        # Core statistics
        if "total_insights" in metadata:
            sections.append(f"Total insights: {metadata['total_insights']}")
        
        if "last_updated" in metadata:
            last_updated = metadata["last_updated"]
            if isinstance(last_updated, str):
                try:
                    # Parse and format timestamp
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    sections.append(f"Last updated: {dt.strftime('%Y-%m-%d %H:%M')}")
                except ValueError:
                    sections.append(f"Last updated: {last_updated}")
        
        if "version" in metadata:
            sections.append(f"Memory version: {metadata['version']}")
        
        # Additional metadata
        for key, value in metadata.items():
            if key not in ["total_insights", "last_updated", "version"]:
                sections.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(sections)
    
    def _create_memory_chunks(self, formatted_sections: List[str], memory_data: Dict[str, Any]) -> List[MemoryChunk]:
        """
        Create memory chunks for large datasets with proper size management
        
        Args:
            formatted_sections: List of formatted content sections
            memory_data: Original memory data for metadata
            
        Returns:
            List[MemoryChunk]: List of memory chunks
        """
        chunks = []
        chunk_id = 1
        
        for section in formatted_sections:
            # If a single section is too large, split it further
            if len(section) > self.max_chunk_size_chars:
                section_chunks = self._split_large_section(section, chunk_id)
                chunks.extend(section_chunks)
                chunk_id += len(section_chunks)
            else:
                # Create chunk from single section
                chunk = MemoryChunk(
                    chunk_id=f"chunk_{chunk_id}",
                    content=section,
                    metadata=self._extract_chunk_metadata(section, memory_data),
                    size_bytes=len(section.encode('utf-8')),
                    insights_count=self._count_insights_in_chunk(section),
                    conversations_count=self._count_conversations_in_chunk(section)
                )
                chunks.append(chunk)
                chunk_id += 1
        
        logger.info(f"Created {len(chunks)} memory chunks for analysis")
        return chunks
    
    def _split_large_section(self, section: str, start_chunk_id: int) -> List[MemoryChunk]:
        """
        Split a large section into smaller chunks
        
        Args:
            section: Large section to split
            start_chunk_id: Starting chunk ID
            
        Returns:
            List[MemoryChunk]: List of smaller chunks
        """
        chunks = []
        lines = section.split('\n')
        current_chunk_lines = []
        current_size = 0
        chunk_id = start_chunk_id
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            # If adding this line would exceed chunk size and we have content, create chunk
            if current_size + line_size > self.max_chunk_size_chars and current_chunk_lines:
                chunk_content = '\n'.join(current_chunk_lines)
                chunk = MemoryChunk(
                    chunk_id=f"chunk_{chunk_id}",
                    content=chunk_content,
                    metadata=self._extract_chunk_metadata(chunk_content, {}),
                    size_bytes=len(chunk_content.encode('utf-8')),
                    insights_count=self._count_insights_in_chunk(chunk_content),
                    conversations_count=self._count_conversations_in_chunk(chunk_content)
                )
                chunks.append(chunk)
                
                # Reset for next chunk
                current_chunk_lines = []
                current_size = 0
                chunk_id += 1
            
            # Add line to current chunk
            current_chunk_lines.append(line)
            current_size += line_size
        
        # Create final chunk if there's remaining content
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunk = MemoryChunk(
                chunk_id=f"chunk_{chunk_id}",
                content=chunk_content,
                metadata=self._extract_chunk_metadata(chunk_content, {}),
                size_bytes=len(chunk_content.encode('utf-8')),
                insights_count=self._count_insights_in_chunk(chunk_content),
                conversations_count=self._count_conversations_in_chunk(chunk_content)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_chunk_metadata(self, chunk_content: str, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata for a memory chunk
        
        Args:
            chunk_content: Content of the chunk
            memory_data: Original memory data
            
        Returns:
            dict: Chunk metadata
        """
        metadata = {
            "content_length": len(chunk_content),
            "has_insights": "=== INSIGHTS" in chunk_content,
            "has_conversations": "=== CONVERSATION" in chunk_content,
            "has_metadata": "=== MEMORY METADATA" in chunk_content,
            "categories": []
        }
        
        # Extract categories mentioned in chunk
        lines = chunk_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and '(' in line and line.replace('(', '').replace(')', '').replace(':', '').isupper():
                # This looks like a category header like "TECHNICAL (3 insights):"
                category_part = line.split('(')[0].strip()
                if category_part and category_part.replace(':', '').isupper():
                    category = category_part.replace(':', '').lower()
                    if category not in metadata["categories"] and category not in ['insights and knowledge', 'conversation summaries', 'memory metadata']:
                        metadata["categories"].append(category)
        
        return metadata
    
    def _count_insights_in_chunk(self, chunk_content: str) -> int:
        """Count insights in a chunk by counting bullet points in insights section"""
        if "=== INSIGHTS" not in chunk_content:
            return 0
        
        lines = chunk_content.split('\n')
        in_insights_section = False
        count = 0
        
        for line in lines:
            if "=== INSIGHTS" in line:
                in_insights_section = True
                continue
            elif line.startswith("=== ") and in_insights_section:
                break
            elif in_insights_section and line.strip().startswith("•"):
                count += 1
        
        return count
    
    def _count_conversations_in_chunk(self, chunk_content: str) -> int:
        """Count conversations in a chunk"""
        if "=== CONVERSATION" not in chunk_content:
            return 0
        
        return chunk_content.count("Conversation ")
    
    def _generate_formatted_cache_key(self, memory_data: Dict[str, Any]) -> str:
        """
        Generate cache key for formatted memory data
        
        Args:
            memory_data: Memory data
            
        Returns:
            str: Cache key
        """
        try:
            # Create a hash based on the structure and content
            key_data = {
                "insights_count": len(memory_data.get("insights", [])),
                "conversations_count": len(memory_data.get("conversation_summaries", [])),
                "chunk_size": self.max_chunk_size_chars
            }
            
            # Add hash of first few insights and conversations for content sensitivity
            insights = memory_data.get("insights", [])[:5]  # First 5 insights
            conversations = memory_data.get("conversation_summaries", [])[:3]  # First 3 conversations
            
            # Create a simple string representation for hashing
            content_str = f"insights:{len(insights)}_conversations:{len(conversations)}"
            for i, insight in enumerate(insights):
                if isinstance(insight, dict) and "content" in insight:
                    content_str += f"_i{i}:{insight['content'][:50]}"
            
            for i, conv in enumerate(conversations):
                if isinstance(conv, dict) and "summary" in conv:
                    content_str += f"_c{i}:{conv['summary'][:50]}"
            
            content_hash = hashlib.md5(content_str.encode()).hexdigest()
            key_data["content_hash"] = content_hash
            
            # Create final key
            key_str = f"{key_data['insights_count']}_{key_data['conversations_count']}_{key_data['chunk_size']}_{content_hash}"
            return hashlib.md5(key_str.encode()).hexdigest()
            
        except Exception as e:
            # Fallback to simple key if anything fails
            logger.warning(f"Failed to generate formatted cache key: {e}")
            return hashlib.md5(f"fallback_{time.time()}".encode()).hexdigest()
    
    @handle_service_error(ErrorCategory.SERENDIPITY_SERVICE, ErrorSeverity.HIGH)
    def _discover_connections(self, formatted_memory: str, enable_streaming: bool = False) -> Dict[str, Any]:
        """
        Use AI to discover connections and patterns in the formatted memory with advanced error handling
        
        Args:
            formatted_memory: Formatted memory text for analysis
            enable_streaming: Whether to use streaming for long analyses
            
        Returns:
            dict: Parsed analysis results
            
        Raises:
            SerendipityServiceError: If AI analysis fails
        """
        # Check cache first
        cache_key = self._generate_analysis_cache_key(formatted_memory)
        
        with self._cache_lock:
            if cache_key in self._analysis_cache:
                cache_entry = self._analysis_cache[cache_key]
                if not cache_entry.is_expired():
                    logger.info("Using cached analysis results")
                    return cache_entry.access()
                else:
                    del self._analysis_cache[cache_key]
        
        # Prepare enhanced conversation for AI
        conversation = [
            {
                "role": "user",
                "content": f"""Analyze the following personal knowledge and conversation data to discover hidden connections, patterns, and serendipitous insights. Focus on non-obvious relationships and provide specific, actionable insights.

MEMORY DATA:
{formatted_memory}

Please provide your analysis in the exact JSON format specified in your system prompt. Be specific about which insights connect and why the connections are meaningful."""
            }
        ]
        
        # Determine if we should use streaming based on content size
        memory_size = len(formatted_memory)
        use_streaming = enable_streaming and memory_size > 5000  # Use streaming for large analyses
        
        # Dynamic timeout based on content size (optimize for smaller analyses)
        if memory_size < 1000:
            dynamic_timeout = min(60, self.analysis_timeout)  # 1 minute for small analyses
        elif memory_size < 3000:
            dynamic_timeout = min(90, self.analysis_timeout)  # 1.5 minutes for medium analyses  
        else:
            dynamic_timeout = self.analysis_timeout  # Full timeout for large analyses
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending memory data to AI for serendipity analysis (attempt {attempt + 1}/{max_retries}, "
                           f"size: {memory_size} chars, streaming: {use_streaming})")
                start_time = time.time()
                
                if use_streaming:
                    # Use streaming for long analyses
                    ai_response = self._handle_streaming_analysis(conversation, start_time, dynamic_timeout)
                else:
                    # Regular analysis with timeout
                    ai_response = self._handle_regular_analysis(conversation, start_time, dynamic_timeout)
                
                analysis_time = time.time() - start_time
                logger.info(f"AI analysis completed in {analysis_time:.2f}s")
                
                # Parse and validate JSON response
                analysis_results = self._parse_ai_response_enhanced(ai_response)
                
                # Cache successful results
                with self._cache_lock:
                    self._analysis_cache[cache_key] = CacheEntry(
                        data=analysis_results,
                        timestamp=datetime.now(),
                        ttl_seconds=self.analysis_cache_ttl
                    )
                
                return analysis_results
                
            except AIServiceError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"AI analysis attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                else:
                    self.error_handler.log_error(
                        e,
                        ErrorCategory.SERENDIPITY_SERVICE,
                        ErrorSeverity.HIGH,
                        {"memory_length": len(formatted_memory), "attempts": max_retries}
                    )
                    # Return fallback response instead of failing completely
                    return self._create_fallback_response(f"AI analysis failed after {max_retries} attempts: {str(e)}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}, retrying: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                else:
                    self.error_handler.log_error(
                        e,
                        ErrorCategory.SERENDIPITY_SERVICE,
                        ErrorSeverity.HIGH,
                        {"memory_length": len(formatted_memory), "attempts": max_retries}
                    )
                    return self._create_fallback_response(f"Unexpected error during analysis: {str(e)}")
    
    def _handle_regular_analysis(self, conversation: List[Dict[str, str]], start_time: float, timeout: int = None) -> str:
        """
        Handle regular (non-streaming) AI analysis with timeout
        
        Args:
            conversation: Conversation messages for AI
            start_time: Analysis start time
            timeout: Custom timeout (uses default if None)
            
        Returns:
            str: AI response text
            
        Raises:
            AIServiceError: If analysis fails or times out
        """
        try:
            # Set timeout based on configuration or custom value
            analysis_timeout = timeout if timeout is not None else self.analysis_timeout
            timeout_start = time.time()
            
            ai_response = self.ai_service.chat(conversation, stream=False)
            
            # Check if we exceeded timeout
            elapsed = time.time() - timeout_start
            if elapsed > analysis_timeout:
                raise AIServiceError(f"Analysis timed out after {elapsed:.1f}s (limit: {analysis_timeout}s)")
            
            if not ai_response or not ai_response.strip():
                raise AIServiceError("AI returned empty response")
            
            return ai_response
            
        except Exception as e:
            raise AIServiceError(f"Regular analysis failed: {str(e)}")
    
    def _handle_streaming_analysis(self, conversation: List[Dict[str, str]], start_time: float, timeout: int = None) -> str:
        """
        Handle streaming AI analysis for long analyses
        
        Args:
            conversation: Conversation messages for AI
            start_time: Analysis start time
            timeout: Custom timeout (uses default if None)
            
        Returns:
            str: Complete AI response text
            
        Raises:
            AIServiceError: If streaming analysis fails
        """
        try:
            logger.info("Using streaming analysis for large memory dataset")
            
            analysis_timeout = timeout if timeout is not None else self.analysis_timeout
            full_response = ""
            chunk_count = 0
            last_chunk_time = time.time()
            
            # Get streaming response
            stream = self.ai_service.chat(conversation, stream=True)
            
            for chunk in stream:
                chunk_count += 1
                current_time = time.time()
                
                # Check for timeout
                if current_time - start_time > analysis_timeout:
                    raise AIServiceError(f"Streaming analysis timed out after {current_time - start_time:.1f}s")
                
                # Check for stalled stream (no chunks for too long)
                if current_time - last_chunk_time > 30:  # 30 seconds without chunks
                    raise AIServiceError("Streaming analysis stalled - no response chunks received")
                
                if chunk.get("error"):
                    raise AIServiceError(f"Streaming error: {chunk['error']}")
                
                if chunk.get("content"):
                    full_response += chunk["content"]
                    last_chunk_time = current_time
                
                if chunk.get("done"):
                    logger.info(f"Streaming analysis completed: {chunk_count} chunks, "
                               f"{len(full_response)} characters")
                    break
            
            if not full_response.strip():
                raise AIServiceError("Streaming analysis produced empty response")
            
            return full_response
            
        except Exception as e:
            raise AIServiceError(f"Streaming analysis failed: {str(e)}")
    
    def _generate_analysis_cache_key(self, formatted_memory: str) -> str:
        """
        Generate cache key for analysis results
        
        Args:
            formatted_memory: Formatted memory content
            
        Returns:
            str: Cache key
        """
        try:
            # Create hash based on content and configuration
            key_data = f"{formatted_memory[:1000]}:{len(formatted_memory)}:{self.config.OLLAMA_MODEL}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            # Fallback key
            return hashlib.md5(f"fallback_{time.time()}".encode()).hexdigest()
    
    def _parse_ai_response_enhanced(self, ai_response: str) -> Dict[str, Any]:
        """
        Enhanced AI response parsing with comprehensive validation and error recovery
        
        Args:
            ai_response: Raw AI response text
            
        Returns:
            dict: Parsed and validated analysis results
        """
        try:
            # Multiple strategies for JSON extraction
            analysis_results = self._extract_json_from_response(ai_response)
            
            if not analysis_results:
                logger.warning("No valid JSON found, attempting recovery strategies")
                analysis_results = self._attempt_json_recovery_strategies(ai_response)
            
            if not analysis_results:
                return self._create_fallback_response("Could not extract valid JSON from AI response")
            
            # Comprehensive validation and cleaning
            validated_results = self._validate_and_clean_analysis_results(analysis_results)
            
            logger.info(f"Successfully parsed AI response: {len(validated_results['connections'])} connections, "
                       f"{len(validated_results['meta_patterns'])} patterns")
            
            return validated_results
            
        except Exception as e:
            self.error_handler.log_error(
                e,
                ErrorCategory.SERENDIPITY_SERVICE,
                ErrorSeverity.MEDIUM,
                {"response_length": len(ai_response)}
            )
            return self._create_fallback_response(f"Error parsing AI response: {str(e)}")
    
    def _extract_json_from_response(self, ai_response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from AI response using multiple strategies
        
        Args:
            ai_response: Raw AI response text
            
        Returns:
            dict or None: Extracted JSON data if successful
        """
        # Strategy 1: Find first complete JSON object
        try:
            json_start = ai_response.find('{')
            if json_start == -1:
                return None
            
            # Find matching closing brace
            brace_count = 0
            json_end = json_start
            
            for i, char in enumerate(ai_response[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if brace_count == 0:
                json_text = ai_response[json_start:json_end]
                return json.loads(json_text)
                
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Look for JSON between code blocks
        try:
            import re
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, ai_response, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            pass
        
        # Strategy 3: Try to find JSON after common prefixes
        try:
            prefixes = ["Here's the analysis:", "Analysis:", "Result:", "JSON:", "```json"]
            
            for prefix in prefixes:
                prefix_pos = ai_response.lower().find(prefix.lower())
                if prefix_pos != -1:
                    remaining_text = ai_response[prefix_pos + len(prefix):]
                    json_start = remaining_text.find('{')
                    if json_start != -1:
                        try:
                            # Try to parse from this position
                            potential_json = remaining_text[json_start:]
                            json_end = potential_json.find('\n```')  # End of code block
                            if json_end != -1:
                                potential_json = potential_json[:json_end]
                            
                            return json.loads(potential_json)
                        except json.JSONDecodeError:
                            continue
                            
        except Exception:
            pass
        
        return None
    
    def _attempt_json_recovery_strategies(self, ai_response: str) -> Optional[Dict[str, Any]]:
        """
        Attempt various JSON recovery strategies for malformed responses
        
        Args:
            ai_response: Raw AI response text
            
        Returns:
            dict or None: Recovered JSON data if successful
        """
        # Strategy 1: Fix common JSON issues
        try:
            # Find potential JSON content
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = ai_response[json_start:json_end]
                
                # Fix common issues
                import re
                
                # Remove trailing commas
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                
                # Fix unescaped quotes in strings
                json_text = re.sub(r'(?<!\\)"(?=[^,}\]]*[,}\]])', r'\\"', json_text)
                
                # Try to parse fixed JSON
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass
                    
        except Exception:
            pass
        
        # Strategy 2: Extract structured data even if not valid JSON
        try:
            # Look for key patterns and construct minimal structure
            connections = []
            patterns = []
            summary = ""
            recommendations = []
            
            # Extract connections using regex
            import re
            connection_pattern = r'"title":\s*"([^"]+)".*?"description":\s*"([^"]+)"'
            matches = re.findall(connection_pattern, ai_response, re.DOTALL)
            
            for i, (title, desc) in enumerate(matches[:5]):  # Limit to 5 connections
                connections.append({
                    "title": title[:60],  # Truncate long titles
                    "description": desc[:500],  # Truncate long descriptions
                    "surprise_factor": 0.7,
                    "relevance": 0.8,
                    "connected_insights": [],
                    "connection_type": "emergent",
                    "actionable_insight": "Explore this connection further"
                })
            
            # Extract summary
            summary_pattern = r'"serendipity_summary":\s*"([^"]+)"'
            summary_match = re.search(summary_pattern, ai_response)
            if summary_match:
                summary = summary_match.group(1)[:1000]  # Truncate long summaries
            
            if connections or summary:
                return {
                    "connections": connections,
                    "meta_patterns": patterns,
                    "serendipity_summary": summary or "Analysis completed with partial results",
                    "recommendations": recommendations or ["Continue building your memory through diverse conversations"]
                }
                
        except Exception:
            pass
        
        return None
    
    def _validate_and_clean_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation and cleaning of analysis results
        
        Args:
            analysis_results: Raw analysis results
            
        Returns:
            dict: Validated and cleaned results
        """
        # Ensure required structure
        required_keys = ["connections", "meta_patterns", "serendipity_summary", "recommendations"]
        for key in required_keys:
            if key not in analysis_results:
                logger.warning(f"Missing required key '{key}' in AI response, adding default")
                if key == "connections":
                    analysis_results[key] = []
                elif key == "meta_patterns":
                    analysis_results[key] = []
                elif key == "recommendations":
                    analysis_results[key] = []
                else:
                    analysis_results[key] = ""
        
        # Validate and clean connections
        validated_connections = []
        connections = analysis_results.get("connections", [])
        
        if not isinstance(connections, list):
            logger.warning("Connections is not a list, converting")
            connections = []
        
        for i, conn in enumerate(connections):
            if not isinstance(conn, dict):
                logger.warning(f"Connection {i} is not a dictionary, skipping")
                continue
                
            cleaned_conn = self._validate_and_clean_connection(conn, i)
            if cleaned_conn:
                validated_connections.append(cleaned_conn)
        
        # Validate and clean meta patterns
        validated_patterns = []
        patterns = analysis_results.get("meta_patterns", [])
        
        if not isinstance(patterns, list):
            logger.warning("Meta patterns is not a list, converting")
            patterns = []
        
        for i, pattern in enumerate(patterns):
            if not isinstance(pattern, dict):
                logger.warning(f"Meta pattern {i} is not a dictionary, skipping")
                continue
                
            cleaned_pattern = self._validate_and_clean_meta_pattern(pattern, i)
            if cleaned_pattern:
                validated_patterns.append(cleaned_pattern)
        
        # Clean summary
        summary = analysis_results.get("serendipity_summary", "")
        if not isinstance(summary, str):
            summary = str(summary) if summary else ""
        summary = summary.strip()[:2000]  # Limit length
        
        # Clean recommendations
        recommendations = analysis_results.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        
        cleaned_recommendations = []
        for rec in recommendations:
            if isinstance(rec, str) and rec.strip():
                cleaned_recommendations.append(rec.strip()[:200])  # Limit length
        
        # Ensure we have at least some content
        if not validated_connections and not validated_patterns and not summary:
            summary = "Analysis completed but no significant patterns were identified in the current data."
        
        if not cleaned_recommendations:
            cleaned_recommendations = [
                "Continue building your memory through diverse conversations",
                "Look for patterns across different domains of your interests"
            ]
        
        return {
            "connections": validated_connections,
            "meta_patterns": validated_patterns,
            "serendipity_summary": summary,
            "recommendations": cleaned_recommendations
        }
    
    def _validate_and_clean_connection(self, connection: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        Validate and clean a single connection object
        
        Args:
            connection: Connection object to validate
            index: Index for logging
            
        Returns:
            dict or None: Cleaned connection if valid, None if invalid
        """
        try:
            # Required fields
            title = connection.get("title", "").strip()
            description = connection.get("description", "").strip()
            
            if not title or not description:
                logger.warning(f"Connection {index} missing title or description")
                return None
            
            # Clean and validate fields
            cleaned_connection = {
                "title": title[:60],  # Limit title length
                "description": description[:500],  # Limit description length
                "surprise_factor": self._validate_numeric_field(connection.get("surprise_factor"), 0.5, 0.0, 1.0),
                "relevance": self._validate_numeric_field(connection.get("relevance"), 0.7, 0.0, 1.0),
                "connected_insights": self._validate_list_field(connection.get("connected_insights"), []),
                "connection_type": self._validate_connection_type(connection.get("connection_type")),
                "actionable_insight": str(connection.get("actionable_insight", "")).strip()[:300]
            }
            
            return cleaned_connection
            
        except Exception as e:
            logger.warning(f"Error validating connection {index}: {e}")
            return None
    
    def _validate_and_clean_meta_pattern(self, pattern: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        Validate and clean a single meta pattern object
        
        Args:
            pattern: Meta pattern object to validate
            index: Index for logging
            
        Returns:
            dict or None: Cleaned pattern if valid, None if invalid
        """
        try:
            # Required fields
            pattern_name = pattern.get("pattern_name", "").strip()
            description = pattern.get("description", "").strip()
            
            if not pattern_name or not description:
                logger.warning(f"Meta pattern {index} missing name or description")
                return None
            
            # Clean and validate fields
            cleaned_pattern = {
                "pattern_name": pattern_name[:100],  # Limit name length
                "description": description[:500],  # Limit description length
                "evidence_count": max(1, int(pattern.get("evidence_count", 1))),
                "confidence": self._validate_numeric_field(pattern.get("confidence"), 0.6, 0.0, 1.0)
            }
            
            return cleaned_pattern
            
        except Exception as e:
            logger.warning(f"Error validating meta pattern {index}: {e}")
            return None
    
    def _validate_numeric_field(self, value: Any, default: float, min_val: float, max_val: float) -> float:
        """
        Validate and clean a numeric field
        
        Args:
            value: Value to validate
            default: Default value if invalid
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            float: Validated numeric value
        """
        try:
            num_val = float(value)
            return max(min_val, min(max_val, num_val))
        except (ValueError, TypeError):
            return default
    
    def _validate_list_field(self, value: Any, default: List[Any]) -> List[Any]:
        """
        Validate and clean a list field
        
        Args:
            value: Value to validate
            default: Default value if invalid
            
        Returns:
            list: Validated list
        """
        if isinstance(value, list):
            return [str(item).strip() for item in value if item][:10]  # Limit to 10 items
        return default
    
    def _validate_connection_type(self, value: Any) -> str:
        """
        Validate connection type field
        
        Args:
            value: Value to validate
            
        Returns:
            str: Valid connection type
        """
        valid_types = ["cross_domain", "temporal", "contradictory", "emergent", "thematic"]
        if isinstance(value, str) and value.lower() in valid_types:
            return value.lower()
        return "emergent"  # Default type
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility
        
        Args:
            ai_response: Raw AI response text
            
        Returns:
            dict: Parsed analysis results
        """
        return self._parse_ai_response_enhanced(ai_response)
    
    def _validate_connection(self, connection: Dict[str, Any]) -> bool:
        """
        Validate a connection object structure
        
        Args:
            connection: Connection object to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["title", "description"]
        
        for field in required_fields:
            if field not in connection or not connection[field]:
                logger.warning(f"Connection missing required field '{field}'")
                return False
        
        # Validate numeric fields
        numeric_fields = ["surprise_factor", "relevance"]
        for field in numeric_fields:
            if field in connection:
                try:
                    value = float(connection[field])
                    if not (0.0 <= value <= 1.0):
                        logger.warning(f"Connection {field} out of range: {value}")
                        connection[field] = max(0.0, min(1.0, value))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid {field} value in connection")
                    connection[field] = 0.5  # Default value
        
        return True
    
    def _validate_meta_pattern(self, pattern: Dict[str, Any]) -> bool:
        """
        Validate a meta pattern object structure
        
        Args:
            pattern: Meta pattern object to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["pattern_name", "description"]
        
        for field in required_fields:
            if field not in pattern or not pattern[field]:
                logger.warning(f"Meta pattern missing required field '{field}'")
                return False
        
        # Validate numeric fields
        if "confidence" in pattern:
            try:
                value = float(pattern["confidence"])
                if not (0.0 <= value <= 1.0):
                    logger.warning(f"Meta pattern confidence out of range: {value}")
                    pattern["confidence"] = max(0.0, min(1.0, value))
            except (ValueError, TypeError):
                logger.warning("Invalid confidence value in meta pattern")
                pattern["confidence"] = 0.5
        
        if "evidence_count" in pattern:
            try:
                pattern["evidence_count"] = max(0, int(pattern["evidence_count"]))
            except (ValueError, TypeError):
                logger.warning("Invalid evidence_count in meta pattern")
                pattern["evidence_count"] = 1
        
        return True
    
    def _generate_analysis_metadata(self, memory_data: Dict[str, Any], formatted_memory: Union[str, List[MemoryChunk]], 
                                   start_time: float, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive metadata for analysis results with detailed context
        
        Args:
            memory_data: Original memory data
            formatted_memory: Formatted memory for analysis
            start_time: Analysis start time
            analysis_results: Analysis results
            
        Returns:
            dict: Comprehensive metadata
        """
        end_time = time.time()
        analysis_duration = round(end_time - start_time, 3)
        
        # Basic metadata
        metadata = {
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_id": self._generate_analysis_id(),
            "model_used": self.config.OLLAMA_MODEL,
            "service_version": "1.1.0",
            "analysis_duration": analysis_duration,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat()
        }
        
        # Memory data statistics
        insights = memory_data.get("insights", [])
        conversations = memory_data.get("conversation_summaries", [])
        
        metadata["memory_statistics"] = {
            "insights_analyzed": len(insights),
            "conversations_analyzed": len(conversations),
            "total_items_analyzed": len(insights) + len(conversations),
            "memory_categories": self._extract_memory_categories(insights),
            "date_range": self._calculate_memory_date_range(insights, conversations),
            "content_statistics": self._calculate_content_statistics(insights, conversations)
        }
        
        # Processing metadata
        is_chunked = isinstance(formatted_memory, list)
        metadata["processing_metadata"] = {
            "chunked_analysis": is_chunked,
            "chunks_processed": len(formatted_memory) if is_chunked else 1,
            "total_content_size": self._calculate_total_content_size(formatted_memory),
            "processing_method": "chunked" if is_chunked else "single_pass",
            "cache_hits": self._get_cache_statistics()
        }
        
        # Analysis results metadata
        connections = analysis_results.get("connections", [])
        patterns = analysis_results.get("meta_patterns", [])
        
        metadata["results_metadata"] = {
            "connections_discovered": len(connections),
            "meta_patterns_identified": len(patterns),
            "recommendations_generated": len(analysis_results.get("recommendations", [])),
            "connection_types": self._analyze_connection_types(connections),
            "average_surprise_factor": self._calculate_average_surprise_factor(connections),
            "average_relevance": self._calculate_average_relevance(connections),
            "pattern_confidence_distribution": self._analyze_pattern_confidence(patterns)
        }
        
        # Performance metrics
        metadata["performance_metrics"] = {
            "analysis_speed": {
                "items_per_second": round((len(insights) + len(conversations)) / analysis_duration, 2),
                "characters_per_second": round(self._calculate_total_content_size(formatted_memory) / analysis_duration, 2),
                "connections_per_second": round(len(connections) / analysis_duration, 2)
            },
            "efficiency_metrics": {
                "connections_per_insight": round(len(connections) / max(len(insights), 1), 2),
                "patterns_per_connection": round(len(patterns) / max(len(connections), 1), 2),
                "processing_overhead": round((analysis_duration - self._estimate_ai_processing_time()) / max(analysis_duration, 0.001), 2)
            },
            "resource_usage": {
                "memory_cache_size": len(self._memory_cache),
                "analysis_cache_size": len(self._analysis_cache),
                "formatted_cache_size": len(self._formatted_cache)
            }
        }
        
        # System context
        metadata["system_context"] = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "hostname": platform.node(),
            "process_id": os.getpid(),
            "thread_id": threading.get_ident(),
            "timezone": str(datetime.now().astimezone().tzinfo)
        }
        
        # Configuration snapshot
        metadata["configuration"] = {
            "min_insights_required": self.min_insights_required,
            "max_memory_size_mb": self.max_memory_size_mb,
            "analysis_timeout": self.analysis_timeout,
            "max_chunk_size_chars": self.max_chunk_size_chars,
            "chunk_overlap_chars": self.chunk_overlap_chars,
            "cache_ttl_settings": {
                "memory_cache_ttl": self.memory_cache_ttl,
                "analysis_cache_ttl": self.analysis_cache_ttl,
                "formatted_cache_ttl": self.formatted_cache_ttl
            }
        }
        
        return metadata
    
    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(f"{time.time()}_{threading.get_ident()}".encode()).hexdigest()[:8]
        return f"analysis_{timestamp}_{random_suffix}"
    
    def _extract_memory_categories(self, insights: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract and count memory categories"""
        categories = defaultdict(int)
        for insight in insights:
            if isinstance(insight, dict) and "category" in insight:
                category = insight["category"].lower().strip()
                if category:
                    categories[category] += 1
        return dict(categories)
    
    def _calculate_memory_date_range(self, insights: List[Dict[str, Any]], 
                                   conversations: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """Calculate date range of memory data"""
        dates = []
        
        # Extract dates from insights
        for insight in insights:
            if isinstance(insight, dict) and "timestamp" in insight:
                timestamp = insight["timestamp"]
                if isinstance(timestamp, str):
                    try:
                        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        dates.append(date)
                    except ValueError:
                        continue
        
        # Extract dates from conversations
        for conv in conversations:
            if isinstance(conv, dict) and "timestamp" in conv:
                timestamp = conv["timestamp"]
                if isinstance(timestamp, str):
                    try:
                        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        dates.append(date)
                    except ValueError:
                        continue
        
        if not dates:
            return {"earliest": None, "latest": None, "span_days": 0}
        
        earliest = min(dates)
        latest = max(dates)
        span_days = (latest - earliest).days
        
        return {
            "earliest": earliest.isoformat(),
            "latest": latest.isoformat(),
            "span_days": span_days
        }
    
    def _calculate_content_statistics(self, insights: List[Dict[str, Any]], 
                                    conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate content statistics"""
        stats = {
            "total_characters": 0,
            "total_words": 0,
            "average_insight_length": 0,
            "average_conversation_length": 0,
            "longest_content": 0,
            "shortest_content": float('inf')
        }
        
        insight_lengths = []
        conversation_lengths = []
        
        # Process insights
        for insight in insights:
            if isinstance(insight, dict) and "content" in insight:
                content = insight["content"]
                if isinstance(content, str):
                    length = len(content)
                    insight_lengths.append(length)
                    stats["total_characters"] += length
                    stats["total_words"] += len(content.split())
                    stats["longest_content"] = max(stats["longest_content"], length)
                    stats["shortest_content"] = min(stats["shortest_content"], length)
        
        # Process conversations
        for conv in conversations:
            if isinstance(conv, dict) and "summary" in conv:
                summary = conv["summary"]
                if isinstance(summary, str):
                    length = len(summary)
                    conversation_lengths.append(length)
                    stats["total_characters"] += length
                    stats["total_words"] += len(summary.split())
                    stats["longest_content"] = max(stats["longest_content"], length)
                    stats["shortest_content"] = min(stats["shortest_content"], length)
        
        # Calculate averages
        if insight_lengths:
            stats["average_insight_length"] = round(sum(insight_lengths) / len(insight_lengths), 1)
        if conversation_lengths:
            stats["average_conversation_length"] = round(sum(conversation_lengths) / len(conversation_lengths), 1)
        
        # Handle edge case
        if stats["shortest_content"] == float('inf'):
            stats["shortest_content"] = 0
        
        return stats
    
    def _calculate_total_content_size(self, formatted_memory: Union[str, List[MemoryChunk]]) -> int:
        """Calculate total content size"""
        if isinstance(formatted_memory, str):
            return len(formatted_memory)
        elif isinstance(formatted_memory, list):
            return sum(chunk.size_bytes for chunk in formatted_memory)
        return 0
    
    def _get_cache_statistics(self) -> Dict[str, int]:
        """Get cache hit statistics"""
        return {
            "memory_cache_entries": len(self._memory_cache),
            "analysis_cache_entries": len(self._analysis_cache),
            "formatted_cache_entries": len(self._formatted_cache)
        }
    
    def _analyze_connection_types(self, connections: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of connection types"""
        types = defaultdict(int)
        for connection in connections:
            if isinstance(connection, dict) and "connection_type" in connection:
                conn_type = connection["connection_type"]
                if isinstance(conn_type, str):
                    types[conn_type] += 1
        return dict(types)
    
    def _calculate_average_surprise_factor(self, connections: List[Dict[str, Any]]) -> float:
        """Calculate average surprise factor"""
        surprise_factors = []
        for connection in connections:
            if isinstance(connection, dict) and "surprise_factor" in connection:
                try:
                    surprise = float(connection["surprise_factor"])
                    surprise_factors.append(surprise)
                except (ValueError, TypeError):
                    continue
        
        return round(sum(surprise_factors) / len(surprise_factors), 3) if surprise_factors else 0.0
    
    def _calculate_average_relevance(self, connections: List[Dict[str, Any]]) -> float:
        """Calculate average relevance"""
        relevances = []
        for connection in connections:
            if isinstance(connection, dict) and "relevance" in connection:
                try:
                    relevance = float(connection["relevance"])
                    relevances.append(relevance)
                except (ValueError, TypeError):
                    continue
        
        return round(sum(relevances) / len(relevances), 3) if relevances else 0.0
    
    def _analyze_pattern_confidence(self, patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze pattern confidence distribution"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for pattern in patterns:
            if isinstance(pattern, dict) and "confidence" in pattern:
                try:
                    confidence = float(pattern["confidence"])
                    if confidence >= 0.8:
                        distribution["high"] += 1
                    elif confidence >= 0.5:
                        distribution["medium"] += 1
                    else:
                        distribution["low"] += 1
                except (ValueError, TypeError):
                    continue
        
        return distribution
    
    def _estimate_ai_processing_time(self) -> float:
        """Estimate time spent in AI processing (rough estimate)"""
        # This is a rough estimate - in practice, you'd track this more precisely
        return 0.001  # Minimum processing time to avoid division by zero
    
    def _store_analysis_history(self, analysis_results: Dict[str, Any]) -> None:
        """
        Store analysis in persistent history with context preservation
        
        Args:
            analysis_results: Complete analysis results with metadata
        """
        try:
            history_file = Path(self.config.MEMORY_FILE).parent / "serendipity_history.json"
            
            # Load existing history
            history = self._load_analysis_history()
            
            # Create history entry
            history_entry = {
                "analysis_id": analysis_results["metadata"]["analysis_id"],
                "timestamp": analysis_results["metadata"]["analysis_timestamp"],
                "summary": {
                    "connections_count": len(analysis_results.get("connections", [])),
                    "patterns_count": len(analysis_results.get("meta_patterns", [])),
                    "recommendations_count": len(analysis_results.get("recommendations", [])),
                    "analysis_duration": analysis_results["metadata"]["analysis_duration"],
                    "memory_items_analyzed": analysis_results["metadata"]["memory_statistics"]["total_items_analyzed"]
                },
                "performance_snapshot": {
                    "analysis_speed": analysis_results["metadata"]["performance_metrics"]["analysis_speed"],
                    "efficiency_metrics": analysis_results["metadata"]["performance_metrics"]["efficiency_metrics"]
                },
                "context": {
                    "model_used": analysis_results["metadata"]["model_used"],
                    "chunked_analysis": analysis_results["metadata"]["processing_metadata"]["chunked_analysis"],
                    "memory_categories": analysis_results["metadata"]["memory_statistics"]["memory_categories"],
                    "date_range": analysis_results["metadata"]["memory_statistics"]["date_range"]
                },
                "results_preview": {
                    "top_connections": [
                        {
                            "title": conn.get("title", ""),
                            "surprise_factor": conn.get("surprise_factor", 0),
                            "relevance": conn.get("relevance", 0)
                        }
                        for conn in analysis_results.get("connections", [])[:3]  # Top 3 connections
                    ],
                    "key_patterns": [
                        {
                            "pattern_name": pattern.get("pattern_name", ""),
                            "confidence": pattern.get("confidence", 0)
                        }
                        for pattern in analysis_results.get("meta_patterns", [])[:2]  # Top 2 patterns
                    ]
                }
            }
            
            # Add to history
            history["analyses"].append(history_entry)
            
            # Maintain history size limit (keep last 50 analyses)
            max_history_size = getattr(self.config, 'SERENDIPITY_MAX_HISTORY_SIZE', 50)
            if len(history["analyses"]) > max_history_size:
                history["analyses"] = history["analyses"][-max_history_size:]
            
            # Update metadata
            history["metadata"]["last_updated"] = datetime.now().isoformat()
            history["metadata"]["total_analyses"] = len(history["analyses"])
            
            # Save history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis stored in history: {analysis_results['metadata']['analysis_id']}")
            
        except Exception as e:
            logger.error(f"Failed to store analysis history: {e}")
            # Don't raise exception - history storage failure shouldn't break analysis
    
    def _load_analysis_history(self) -> Dict[str, Any]:
        """
        Load analysis history from persistent storage
        
        Returns:
            dict: Analysis history data
        """
        try:
            history_file = Path(self.config.MEMORY_FILE).parent / "serendipity_history.json"
            
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # Validate structure
                if not isinstance(history, dict) or "analyses" not in history:
                    raise ValueError("Invalid history file structure")
                
                return history
            
        except Exception as e:
            logger.warning(f"Failed to load analysis history: {e}")
        
        # Return default structure
        return {
            "analyses": [],
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_analyses": 0,
                "version": "1.0"
            }
        }
    
    def _track_usage_analytics(self, analysis_results: Dict[str, Any]) -> None:
        """
        Track usage analytics and user engagement metrics
        
        Args:
            analysis_results: Complete analysis results with metadata
        """
        try:
            analytics_file = Path(self.config.MEMORY_FILE).parent / "serendipity_analytics.json"
            
            # Load existing analytics
            analytics = self._load_usage_analytics()
            
            # Update usage statistics
            analytics["usage_statistics"]["total_analyses"] += 1
            analytics["usage_statistics"]["total_connections_discovered"] += len(analysis_results.get("connections", []))
            analytics["usage_statistics"]["total_patterns_identified"] += len(analysis_results.get("meta_patterns", []))
            analytics["usage_statistics"]["total_analysis_time"] += analysis_results["metadata"]["analysis_duration"]
            
            # Track daily usage
            today = datetime.now().date().isoformat()
            if today not in analytics["daily_usage"]:
                analytics["daily_usage"][today] = {
                    "analyses_count": 0,
                    "total_duration": 0,
                    "connections_discovered": 0,
                    "patterns_identified": 0
                }
            
            daily_stats = analytics["daily_usage"][today]
            daily_stats["analyses_count"] += 1
            daily_stats["total_duration"] += analysis_results["metadata"]["analysis_duration"]
            daily_stats["connections_discovered"] += len(analysis_results.get("connections", []))
            daily_stats["patterns_identified"] += len(analysis_results.get("meta_patterns", []))
            
            # Track performance metrics
            performance = analysis_results["metadata"]["performance_metrics"]
            analytics["performance_trends"]["analysis_durations"].append(analysis_results["metadata"]["analysis_duration"])
            analytics["performance_trends"]["items_per_second"].append(performance["analysis_speed"]["items_per_second"])
            analytics["performance_trends"]["connections_per_insight"].append(performance["efficiency_metrics"]["connections_per_insight"])
            
            # Limit trend data size
            max_trend_size = 100
            for trend_key in analytics["performance_trends"]:
                if len(analytics["performance_trends"][trend_key]) > max_trend_size:
                    analytics["performance_trends"][trend_key] = analytics["performance_trends"][trend_key][-max_trend_size:]
            
            # Track model usage
            model = analysis_results["metadata"]["model_used"]
            if model not in analytics["model_usage"]:
                analytics["model_usage"][model] = 0
            analytics["model_usage"][model] += 1
            
            # Track connection types
            for connection in analysis_results.get("connections", []):
                if isinstance(connection, dict) and "connection_type" in connection:
                    conn_type = connection["connection_type"]
                    if conn_type not in analytics["connection_type_distribution"]:
                        analytics["connection_type_distribution"][conn_type] = 0
                    analytics["connection_type_distribution"][conn_type] += 1
            
            # Update metadata
            analytics["metadata"]["last_updated"] = datetime.now().isoformat()
            analytics["metadata"]["last_analysis_id"] = analysis_results["metadata"]["analysis_id"]
            
            # Clean up old daily usage data (keep last 90 days)
            cutoff_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            analytics["daily_usage"] = {
                date: stats for date, stats in analytics["daily_usage"].items()
                if date >= cutoff_date
            }
            
            # Save analytics
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Usage analytics updated for analysis: {analysis_results['metadata']['analysis_id']}")
            
        except Exception as e:
            logger.error(f"Failed to track usage analytics: {e}")
            # Don't raise exception - analytics failure shouldn't break analysis
    
    def _load_usage_analytics(self) -> Dict[str, Any]:
        """
        Load usage analytics from persistent storage
        
        Returns:
            dict: Usage analytics data
        """
        try:
            analytics_file = Path(self.config.MEMORY_FILE).parent / "serendipity_analytics.json"
            
            if analytics_file.exists():
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    analytics = json.load(f)
                
                # Validate and update structure if needed
                analytics = self._validate_analytics_structure(analytics)
                return analytics
            
        except Exception as e:
            logger.warning(f"Failed to load usage analytics: {e}")
        
        # Return default structure
        return self._create_default_analytics_structure()
    
    def _validate_analytics_structure(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and update analytics structure"""
        default_structure = self._create_default_analytics_structure()
        
        # Ensure all required keys exist
        for key, default_value in default_structure.items():
            if key not in analytics:
                analytics[key] = default_value
            elif isinstance(default_value, dict):
                # Recursively validate nested dictionaries
                for nested_key, nested_default in default_value.items():
                    if nested_key not in analytics[key]:
                        analytics[key][nested_key] = nested_default
        
        return analytics
    
    def _create_default_analytics_structure(self) -> Dict[str, Any]:
        """Create default analytics structure"""
        return {
            "usage_statistics": {
                "total_analyses": 0,
                "total_connections_discovered": 0,
                "total_patterns_identified": 0,
                "total_analysis_time": 0.0,
                "first_analysis_date": None,
                "most_recent_analysis_date": None
            },
            "daily_usage": {},
            "performance_trends": {
                "analysis_durations": [],
                "items_per_second": [],
                "connections_per_insight": []
            },
            "model_usage": {},
            "connection_type_distribution": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "last_analysis_id": None
            }
        }
    
    def get_analysis_history(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get analysis history with optional limit
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            dict: Analysis history data
        """
        history = self._load_analysis_history()
        
        if limit is not None and limit >= 0:
            if limit == 0:
                history["analyses"] = []
            elif len(history["analyses"]) > limit:
                history["analyses"] = history["analyses"][-limit:]
        
        return history
    
    def get_usage_analytics(self) -> Dict[str, Any]:
        """
        Get usage analytics data
        
        Returns:
            dict: Usage analytics data
        """
        return self._load_usage_analytics()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics
        
        Returns:
            dict: Performance metrics
        """
        analytics = self._load_usage_analytics()
        
        # Calculate recent performance averages
        recent_durations = analytics["performance_trends"]["analysis_durations"][-10:]  # Last 10
        recent_speeds = analytics["performance_trends"]["items_per_second"][-10:]
        recent_efficiency = analytics["performance_trends"]["connections_per_insight"][-10:]
        
        metrics = {
            "recent_performance": {
                "average_duration": round(sum(recent_durations) / len(recent_durations), 2) if recent_durations else 0,
                "average_speed": round(sum(recent_speeds) / len(recent_speeds), 2) if recent_speeds else 0,
                "average_efficiency": round(sum(recent_efficiency) / len(recent_efficiency), 2) if recent_efficiency else 0
            },
            "cache_performance": self.get_cache_stats(),
            "service_status": self.get_service_status(),
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    def _create_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create a fallback response when AI analysis fails
        
        Args:
            error_message: Error message to include
            
        Returns:
            dict: Fallback response structure
        """
        return {
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": f"Analysis could not be completed: {error_message}",
            "recommendations": [
                "Try having more conversations to build up your memory",
                "Ensure your insights cover diverse topics for better analysis",
                "Check that the AI service is running properly"
            ],
            "error": error_message
        }
    
    def _discover_connections_chunked(self, memory_chunks: List[MemoryChunk]) -> Dict[str, Any]:
        """
        Discover connections across multiple memory chunks
        
        Args:
            memory_chunks: List of memory chunks to analyze
            
        Returns:
            dict: Combined analysis results from all chunks
        """
        logger.info(f"Starting chunked analysis of {len(memory_chunks)} chunks")
        
        all_connections = []
        all_meta_patterns = []
        chunk_summaries = []
        
        for i, chunk in enumerate(memory_chunks):
            logger.info(f"Analyzing chunk {i+1}/{len(memory_chunks)} ({chunk.size_bytes} bytes)")
            
            try:
                # Analyze individual chunk
                chunk_results = self._discover_connections(chunk.content)
                
                # Collect results
                all_connections.extend(chunk_results.get("connections", []))
                all_meta_patterns.extend(chunk_results.get("meta_patterns", []))
                
                # Store chunk summary
                chunk_summaries.append({
                    "chunk_id": chunk.chunk_id,
                    "summary": chunk_results.get("serendipity_summary", ""),
                    "connections_found": len(chunk_results.get("connections", [])),
                    "patterns_found": len(chunk_results.get("meta_patterns", [])),
                    "insights_count": chunk.insights_count,
                    "conversations_count": chunk.conversations_count
                })
                
            except Exception as e:
                logger.error(f"Error analyzing chunk {chunk.chunk_id}: {str(e)}")
                chunk_summaries.append({
                    "chunk_id": chunk.chunk_id,
                    "error": str(e),
                    "connections_found": 0,
                    "patterns_found": 0
                })
        
        # Merge and deduplicate results
        merged_results = self._merge_chunked_results(all_connections, all_meta_patterns, chunk_summaries)
        
        logger.info(f"Chunked analysis complete: {len(merged_results['connections'])} connections, "
                   f"{len(merged_results['meta_patterns'])} patterns")
        
        return merged_results
    
    def _merge_chunked_results(self, all_connections: List[Dict], all_meta_patterns: List[Dict], 
                              chunk_summaries: List[Dict]) -> Dict[str, Any]:
        """
        Merge and deduplicate results from multiple chunks
        
        Args:
            all_connections: All connections from chunks
            all_meta_patterns: All meta patterns from chunks
            chunk_summaries: Summaries from each chunk
            
        Returns:
            dict: Merged analysis results
        """
        # Deduplicate connections based on title similarity
        unique_connections = self._deduplicate_connections(all_connections)
        
        # Deduplicate meta patterns based on pattern name similarity
        unique_patterns = self._deduplicate_meta_patterns(all_meta_patterns)
        
        # Create overall summary
        total_connections = sum(cs.get("connections_found", 0) for cs in chunk_summaries)
        total_patterns = sum(cs.get("patterns_found", 0) for cs in chunk_summaries)
        
        overall_summary = (
            f"Cross-chunk analysis revealed {len(unique_connections)} unique connections "
            f"and {len(unique_patterns)} meta-patterns across {len(chunk_summaries)} data chunks. "
            f"The analysis processed insights spanning multiple categories and time periods, "
            f"identifying both local patterns within individual chunks and global patterns "
            f"that emerge across the entire memory dataset."
        )
        
        # Generate cross-chunk recommendations
        recommendations = self._generate_cross_chunk_recommendations(unique_connections, unique_patterns, chunk_summaries)
        
        return {
            "connections": unique_connections,
            "meta_patterns": unique_patterns,
            "serendipity_summary": overall_summary,
            "recommendations": recommendations,
            "chunk_analysis": {
                "chunks_processed": len(chunk_summaries),
                "total_connections_found": total_connections,
                "total_patterns_found": total_patterns,
                "unique_connections": len(unique_connections),
                "unique_patterns": len(unique_patterns),
                "chunk_summaries": chunk_summaries
            }
        }
    
    def _deduplicate_connections(self, connections: List[Dict]) -> List[Dict]:
        """
        Remove duplicate connections based on title similarity
        
        Args:
            connections: List of connection dictionaries
            
        Returns:
            List[Dict]: Deduplicated connections
        """
        if not connections:
            return []
        
        unique_connections = []
        seen_titles = set()
        
        # Sort by relevance and surprise factor
        sorted_connections = sorted(
            connections,
            key=lambda x: (x.get("relevance", 0) + x.get("surprise_factor", 0)) / 2,
            reverse=True
        )
        
        for conn in sorted_connections:
            title = conn.get("title", "").lower().strip()
            
            # Check for similar titles
            is_duplicate = False
            for seen_title in seen_titles:
                if self._calculate_title_similarity(title, seen_title) > 0.85:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_connections.append(conn)
                seen_titles.add(title)
        
        return unique_connections[:20]  # Limit to top 20 connections
    
    def _deduplicate_meta_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Remove duplicate meta patterns based on pattern name similarity
        
        Args:
            patterns: List of meta pattern dictionaries
            
        Returns:
            List[Dict]: Deduplicated patterns
        """
        if not patterns:
            return []
        
        unique_patterns = []
        seen_names = set()
        
        # Sort by confidence and evidence count
        sorted_patterns = sorted(
            patterns,
            key=lambda x: (x.get("confidence", 0), x.get("evidence_count", 0)),
            reverse=True
        )
        
        for pattern in sorted_patterns:
            name = pattern.get("pattern_name", "").lower().strip()
            
            # Check for similar names
            is_duplicate = False
            for seen_name in seen_names:
                if self._calculate_title_similarity(name, seen_name) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_patterns.append(pattern)
                seen_names.add(name)
        
        return unique_patterns[:10]  # Limit to top 10 patterns
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using simple word overlap
        
        Args:
            title1: First title
            title2: Second title
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not title1 or not title2:
            return 0.0
        
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_cross_chunk_recommendations(self, connections: List[Dict], patterns: List[Dict], 
                                            chunk_summaries: List[Dict]) -> List[str]:
        """
        Generate recommendations based on cross-chunk analysis
        
        Args:
            connections: Unique connections found
            patterns: Unique patterns found
            chunk_summaries: Summaries from each chunk
            
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        # Analyze connection diversity
        if len(connections) > 10:
            recommendations.append(
                "Your memory shows rich interconnections across different domains. "
                "Consider exploring the strongest connections for new project ideas."
            )
        elif len(connections) < 3:
            recommendations.append(
                "Limited connections found. Try having more diverse conversations "
                "to build richer cross-domain insights."
            )
        
        # Analyze pattern strength
        high_confidence_patterns = [p for p in patterns if p.get("confidence", 0) > 0.8]
        if high_confidence_patterns:
            recommendations.append(
                f"Found {len(high_confidence_patterns)} strong recurring patterns. "
                "These represent core themes in your thinking that could guide future learning."
            )
        
        # Analyze chunk distribution
        successful_chunks = [cs for cs in chunk_summaries if cs.get("connections_found", 0) > 0]
        if len(successful_chunks) < len(chunk_summaries) * 0.5:
            recommendations.append(
                "Some data chunks yielded fewer insights. Consider having more "
                "detailed conversations to enrich your memory database."
            )
        
        # Default recommendations
        if not recommendations:
            recommendations.extend([
                "Continue building your memory through diverse conversations",
                "Explore the connections found to discover new learning opportunities",
                "Consider how the patterns identified relate to your current goals"
            ])
        
        return recommendations
    
    def clear_cache(self, cache_type: Optional[str] = None) -> Dict[str, int]:
        """
        Clear cached data
        
        Args:
            cache_type: Type of cache to clear ('memory', 'analysis', 'formatted', or None for all)
            
        Returns:
            dict: Number of entries cleared for each cache type
        """
        cleared_counts = {}
        
        with self._cache_lock:
            if cache_type is None or cache_type == "memory":
                cleared_counts["memory"] = len(self._memory_cache)
                self._memory_cache.clear()
            
            if cache_type is None or cache_type == "analysis":
                cleared_counts["analysis"] = len(self._analysis_cache)
                self._analysis_cache.clear()
            
            if cache_type is None or cache_type == "formatted":
                cleared_counts["formatted"] = len(self._formatted_cache)
                self._formatted_cache.clear()
        
        logger.info(f"Cleared cache: {cleared_counts}")
        return cleared_counts
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        with self._cache_lock:
            stats = {
                "memory_cache": {
                    "entries": len(self._memory_cache),
                    "expired": sum(1 for entry in self._memory_cache.values() if entry.is_expired()),
                    "total_accesses": sum(entry.access_count for entry in self._memory_cache.values())
                },
                "analysis_cache": {
                    "entries": len(self._analysis_cache),
                    "expired": sum(1 for entry in self._analysis_cache.values() if entry.is_expired()),
                    "total_accesses": sum(entry.access_count for entry in self._analysis_cache.values())
                },
                "formatted_cache": {
                    "entries": len(self._formatted_cache),
                    "expired": sum(1 for entry in self._formatted_cache.values() if entry.is_expired()),
                    "total_accesses": sum(entry.access_count for entry in self._formatted_cache.values())
                }
            }
        
        return stats
    
    def cleanup_expired_cache(self) -> Dict[str, int]:
        """
        Remove expired cache entries
        
        Returns:
            dict: Number of expired entries removed from each cache
        """
        removed_counts = {"memory": 0, "analysis": 0, "formatted": 0}
        
        with self._cache_lock:
            # Clean memory cache
            expired_keys = [key for key, entry in self._memory_cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._memory_cache[key]
                removed_counts["memory"] += 1
            
            # Clean analysis cache
            expired_keys = [key for key, entry in self._analysis_cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._analysis_cache[key]
                removed_counts["analysis"] += 1
            
            # Clean formatted cache
            expired_keys = [key for key, entry in self._formatted_cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._formatted_cache[key]
                removed_counts["formatted"] += 1
        
        if sum(removed_counts.values()) > 0:
            logger.info(f"Cleaned up expired cache entries: {removed_counts}")
        
        return removed_counts
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status and configuration
        
        Returns:
            dict: Service status information
        """
        status = {
            "enabled": self.config.ENABLE_SERENDIPITY_ENGINE,
            "ai_service_available": self.ai_service is not None,
            "model": self.config.OLLAMA_MODEL,
            "min_insights_required": self.min_insights_required,
            "max_memory_size_mb": self.max_memory_size_mb,
            "analysis_timeout": self.analysis_timeout,
            "memory_file": self.config.MEMORY_FILE,
            "timestamp": datetime.now().isoformat()
        }
        
        # Test AI service if available
        if self.ai_service:
            try:
                # Only test connection if it's a real AI service, not a mock
                if hasattr(self.ai_service, 'test_connection') and callable(self.ai_service.test_connection):
                    ai_status = self.ai_service.test_connection()
                    # Ensure the status is JSON serializable
                    if isinstance(ai_status, dict):
                        status["ai_service_status"] = ai_status
                    else:
                        status["ai_service_status"] = {"status": "available"}
                else:
                    status["ai_service_status"] = {"status": "available"}
            except Exception as e:
                status["ai_service_status"] = {"error": str(e)}
        
        return status

# Global serendipity service instance
_serendipity_service_instance = None

def get_serendipity_service(config=None) -> SerendipityService:
    """
    Get or create the global serendipity service instance
    
    Args:
        config: Configuration object (uses default if None)
        
    Returns:
        SerendipityService: The serendipity service instance
    """
    global _serendipity_service_instance
    
    if _serendipity_service_instance is None:
        _serendipity_service_instance = SerendipityService(config=config)
    
    return _serendipity_service_instance

def reset_serendipity_service():
    """Reset the global serendipity service instance (useful for testing)"""
    global _serendipity_service_instance
    _serendipity_service_instance = None