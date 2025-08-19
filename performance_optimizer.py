"""
Performance Optimizer Module for Synapse AI Web Application

This module provides performance monitoring and optimization functionality
including conversation history management, response time tracking, and
efficient file operations.
"""

import time
import json
import os
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import deque, defaultdict
import gc

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, memory monitoring will be limited")

class PerformanceMetrics:
    """Track and manage performance metrics"""
    
    def __init__(self):
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        self.memory_usage = deque(maxlen=50)     # Keep last 50 memory readings
        self.file_operations = deque(maxlen=50)  # Keep last 50 file operation times
        self.conversation_stats = defaultdict(int)
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record_response_time(self, endpoint: str, duration: float):
        """Record response time for an endpoint"""
        with self._lock:
            self.response_times.append({
                'endpoint': endpoint,
                'duration': duration,
                'timestamp': time.time()
            })
    
    def record_memory_usage(self):
        """Record current memory usage"""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_info = process.memory_info()
                with self._lock:
                    self.memory_usage.append({
                        'rss': memory_info.rss,
                        'vms': memory_info.vms,
                        'timestamp': time.time()
                    })
            else:
                # Fallback to basic memory info if available
                import resource
                memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                with self._lock:
                    self.memory_usage.append({
                        'rss': memory_usage * 1024,  # Convert to bytes on Unix
                        'vms': 0,
                        'timestamp': time.time()
                    })
        except Exception as e:
            logger.warning(f"Failed to record memory usage: {e}")
    
    def record_file_operation(self, operation: str, duration: float, file_size: int = 0):
        """Record file operation performance"""
        with self._lock:
            self.file_operations.append({
                'operation': operation,
                'duration': duration,
                'file_size': file_size,
                'timestamp': time.time()
            })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            # Calculate response time statistics
            response_durations = [r['duration'] for r in self.response_times]
            avg_response_time = sum(response_durations) / len(response_durations) if response_durations else 0
            max_response_time = max(response_durations) if response_durations else 0
            
            # Calculate memory statistics
            if self.memory_usage:
                current_memory = self.memory_usage[-1]['rss'] / 1024 / 1024  # MB
                avg_memory = sum(m['rss'] for m in self.memory_usage) / len(self.memory_usage) / 1024 / 1024
            else:
                current_memory = avg_memory = 0
            
            # Calculate file operation statistics
            file_durations = [f['duration'] for f in self.file_operations]
            avg_file_time = sum(file_durations) / len(file_durations) if file_durations else 0
            
            return {
                'uptime_seconds': time.time() - self.start_time,
                'response_times': {
                    'average': avg_response_time,
                    'maximum': max_response_time,
                    'count': len(self.response_times)
                },
                'memory_usage': {
                    'current_mb': current_memory,
                    'average_mb': avg_memory
                },
                'file_operations': {
                    'average_duration': avg_file_time,
                    'count': len(self.file_operations)
                },
                'conversation_stats': dict(self.conversation_stats)
            }

class ConversationHistoryManager:
    """Manage conversation history with limits and cleanup"""
    
    def __init__(self, max_messages: int = 100, max_age_hours: int = 24):
        """
        Initialize conversation history manager
        
        Args:
            max_messages: Maximum number of messages to keep in history
            max_age_hours: Maximum age of messages in hours
        """
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self.cleanup_threshold = max_messages * 0.8  # Start cleanup at 80% capacity
    
    def cleanup_conversation_history(self, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean up conversation history based on limits and age
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            List of cleaned conversation messages
        """
        if not conversation_history:
            return conversation_history
        
        # Remove messages older than max_age_hours
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        cleaned_history = []
        
        for message in conversation_history:
            # Check if message has timestamp
            if 'timestamp' in message:
                try:
                    msg_time = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
                    if msg_time > cutoff_time:
                        cleaned_history.append(message)
                except (ValueError, TypeError):
                    # If timestamp parsing fails, keep the message
                    cleaned_history.append(message)
            else:
                # If no timestamp, keep the message but add current timestamp
                message['timestamp'] = datetime.now().isoformat()
                cleaned_history.append(message)
        
        # Limit number of messages
        if len(cleaned_history) > self.max_messages:
            # Keep the most recent messages, but preserve conversation flow
            # Always keep pairs of user/assistant messages together
            messages_to_keep = self.max_messages
            result = []
            
            # Start from the end and work backwards
            i = len(cleaned_history) - 1
            while i >= 0 and len(result) < messages_to_keep:
                message = cleaned_history[i]
                result.insert(0, message)
                
                # If this is an assistant message, try to keep the preceding user message
                if (message.get('role') == 'assistant' and 
                    i > 0 and 
                    cleaned_history[i-1].get('role') == 'user' and 
                    len(result) < messages_to_keep):
                    result.insert(0, cleaned_history[i-1])
                    i -= 1
                
                i -= 1
            
            cleaned_history = result
        
        logger.info(f"Cleaned conversation history: {len(conversation_history)} -> {len(cleaned_history)} messages")
        return cleaned_history
    
    def should_cleanup(self, conversation_length: int) -> bool:
        """Check if conversation history should be cleaned up"""
        return conversation_length >= self.cleanup_threshold
    
    def get_conversation_stats(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about conversation history"""
        if not conversation_history:
            return {
                'total_messages': 0,
                'user_messages': 0,
                'assistant_messages': 0,
                'total_characters': 0,
                'oldest_message': None,
                'newest_message': None
            }
        
        user_count = sum(1 for msg in conversation_history if msg.get('role') == 'user')
        assistant_count = sum(1 for msg in conversation_history if msg.get('role') == 'assistant')
        total_chars = sum(len(msg.get('content', '')) for msg in conversation_history)
        
        # Find oldest and newest messages with timestamps
        timestamped_messages = [msg for msg in conversation_history if 'timestamp' in msg]
        oldest = newest = None
        
        if timestamped_messages:
            try:
                timestamps = []
                for msg in timestamped_messages:
                    try:
                        ts = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                        timestamps.append(ts)
                    except (ValueError, TypeError):
                        continue
                
                if timestamps:
                    oldest = min(timestamps).isoformat()
                    newest = max(timestamps).isoformat()
            except Exception as e:
                logger.warning(f"Error calculating message timestamps: {e}")
        
        return {
            'total_messages': len(conversation_history),
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'total_characters': total_chars,
            'oldest_message': oldest,
            'newest_message': newest
        }

class FileOperationOptimizer:
    """Optimize file I/O operations for better performance"""
    
    def __init__(self):
        self.file_cache = {}
        self.cache_timestamps = {}
        self.cache_max_age = 300  # 5 minutes
        self.cache_max_size = 10  # Maximum number of cached files
        self._lock = threading.Lock()
    
    def cached_file_read(self, file_path: str, max_age_seconds: int = None) -> Optional[Dict[str, Any]]:
        """
        Read file with caching to improve performance
        
        Args:
            file_path: Path to file to read
            max_age_seconds: Maximum age of cached data in seconds
            
        Returns:
            File content as dictionary or None if file doesn't exist
        """
        max_age = max_age_seconds or self.cache_max_age
        
        with self._lock:
            # Check if file is in cache and still valid
            if (file_path in self.file_cache and 
                file_path in self.cache_timestamps and
                time.time() - self.cache_timestamps[file_path] < max_age):
                
                # Verify file hasn't been modified
                try:
                    if os.path.exists(file_path):
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime <= self.cache_timestamps[file_path]:
                            logger.debug(f"Using cached data for {file_path}")
                            return self.file_cache[file_path].copy()
                except OSError:
                    pass
            
            # Read file and update cache
            try:
                if not os.path.exists(file_path):
                    return None
                
                start_time = time.time()
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                duration = time.time() - start_time
                file_size = os.path.getsize(file_path)
                
                # Update cache
                self._update_cache(file_path, data)
                
                # Record performance metrics
                performance_metrics.record_file_operation('read', duration, file_size)
                
                logger.debug(f"Read and cached {file_path} ({file_size} bytes in {duration:.3f}s)")
                return data
                
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return None
    
    def optimized_file_write(self, file_path: str, data: Dict[str, Any], 
                           create_backup: bool = True) -> bool:
        """
        Write file with optimizations and safety measures
        
        Args:
            file_path: Path to file to write
            data: Data to write
            create_backup: Whether to create backup before writing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            start_time = time.time()
            
            # Create backup if requested and file exists
            if create_backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            # Write to temporary file first
            temp_path = f"{file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Verify written data
            with open(temp_path, 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise an exception if JSON is invalid
            
            # Atomic rename
            if os.name == 'nt':  # Windows
                if os.path.exists(file_path):
                    os.remove(file_path)
            os.rename(temp_path, file_path)
            
            duration = time.time() - start_time
            file_size = os.path.getsize(file_path)
            
            # Update cache
            with self._lock:
                self._update_cache(file_path, data)
            
            # Record performance metrics
            performance_metrics.record_file_operation('write', duration, file_size)
            
            logger.debug(f"Wrote {file_path} ({file_size} bytes in {duration:.3f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            # Clean up temp file if it exists
            temp_path = f"{file_path}.tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False
    
    def _update_cache(self, file_path: str, data: Dict[str, Any]):
        """Update file cache with new data"""
        # Remove oldest entries if cache is full
        if len(self.file_cache) >= self.cache_max_size:
            oldest_file = min(self.cache_timestamps.keys(), 
                            key=lambda k: self.cache_timestamps[k])
            del self.file_cache[oldest_file]
            del self.cache_timestamps[oldest_file]
        
        # Add new data to cache
        self.file_cache[file_path] = data.copy()
        self.cache_timestamps[file_path] = time.time()
    
    def clear_cache(self):
        """Clear file cache"""
        with self._lock:
            self.file_cache.clear()
            self.cache_timestamps.clear()
        logger.info("File cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'cached_files': len(self.file_cache),
                'cache_max_size': self.cache_max_size,
                'cache_max_age': self.cache_max_age,
                'oldest_cache_age': time.time() - min(self.cache_timestamps.values()) if self.cache_timestamps else 0
            }

class ResponseTimeMonitor:
    """Monitor and optimize response times"""
    
    def __init__(self):
        self.slow_request_threshold = 5.0  # seconds
        self.very_slow_threshold = 10.0    # seconds
        self.optimization_suggestions = []
    
    def monitor_request(self, func: Callable) -> Callable:
        """Decorator to monitor request response times"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics
                endpoint = getattr(func, '__name__', 'unknown')
                performance_metrics.record_response_time(endpoint, duration)
                
                # Check for slow requests
                if duration > self.very_slow_threshold:
                    logger.warning(f"Very slow request: {endpoint} took {duration:.2f}s")
                    self._suggest_optimization(endpoint, duration, 'very_slow')
                elif duration > self.slow_request_threshold:
                    logger.info(f"Slow request: {endpoint} took {duration:.2f}s")
                    self._suggest_optimization(endpoint, duration, 'slow')
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Request failed after {duration:.2f}s: {e}")
                raise
        
        return wrapper
    
    def _suggest_optimization(self, endpoint: str, duration: float, severity: str):
        """Generate optimization suggestions for slow requests"""
        suggestion = {
            'endpoint': endpoint,
            'duration': duration,
            'severity': severity,
            'timestamp': time.time(),
            'suggestions': []
        }
        
        if 'chat' in endpoint.lower():
            suggestion['suggestions'].extend([
                'Consider implementing conversation history limits',
                'Add response streaming for better perceived performance',
                'Optimize AI model parameters for faster responses'
            ])
        elif 'memory' in endpoint.lower():
            suggestion['suggestions'].extend([
                'Implement memory file caching',
                'Consider background processing for insight extraction',
                'Optimize JSON parsing and file I/O operations'
            ])
        elif 'serendipity' in endpoint.lower():
            suggestion['suggestions'].extend([
                'Cache serendipity analysis results',
                'Implement progressive analysis for large datasets',
                'Consider background processing for complex analysis'
            ])
        
        self.optimization_suggestions.append(suggestion)
        
        # Keep only recent suggestions
        cutoff_time = time.time() - 3600  # 1 hour
        self.optimization_suggestions = [
            s for s in self.optimization_suggestions 
            if s['timestamp'] > cutoff_time
        ]
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get current optimization suggestions"""
        return self.optimization_suggestions.copy()

# Global instances
performance_metrics = PerformanceMetrics()
conversation_manager = ConversationHistoryManager()
file_optimizer = FileOperationOptimizer()
response_monitor = ResponseTimeMonitor()

def cleanup_system_resources():
    """Perform system-wide cleanup to free resources"""
    try:
        # Force garbage collection
        gc.collect()
        
        # Clear file cache
        file_optimizer.clear_cache()
        
        # Record memory usage after cleanup
        performance_metrics.record_memory_usage()
        
        logger.info("System resources cleaned up")
        
    except Exception as e:
        logger.error(f"Error during system cleanup: {e}")

def get_performance_status() -> Dict[str, Any]:
    """Get comprehensive performance status"""
    return {
        'metrics': performance_metrics.get_performance_summary(),
        'file_cache': file_optimizer.get_cache_stats(),
        'optimization_suggestions': response_monitor.get_optimization_suggestions(),
        'timestamp': datetime.now().isoformat()
    }

# Background cleanup thread
def start_background_cleanup():
    """Start background thread for periodic cleanup"""
    def cleanup_worker():
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                cleanup_system_resources()
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("Background cleanup thread started")

# Initialize background cleanup
start_background_cleanup()