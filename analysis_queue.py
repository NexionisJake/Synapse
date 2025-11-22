"""
Analysis Queue Management System for Synapse AI Web Application

This module provides queue management for concurrent serendipity analysis requests,
including priority handling, resource management, and performance optimization.
"""

import time
import threading
import queue
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

class RequestPriority(Enum):
    """Priority levels for analysis requests"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class RequestStatus(Enum):
    """Status of analysis requests"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class AnalysisRequest:
    """Analysis request with metadata and tracking"""
    request_id: str
    user_id: Optional[str]
    memory_file_path: Optional[str]
    priority: RequestPriority
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking fields
    status: RequestStatus = RequestStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    wait_time: Optional[float] = None
    worker_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Resource tracking
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def start_processing(self, worker_id: str):
        """Mark request as started processing"""
        self.status = RequestStatus.PROCESSING
        self.started_at = datetime.now()
        self.worker_id = worker_id
        if self.created_at:
            self.wait_time = (self.started_at - self.created_at).total_seconds()
    
    def complete_processing(self, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Mark request as completed"""
        self.completed_at = datetime.now()
        if error:
            self.status = RequestStatus.FAILED
            self.error = error
        else:
            self.status = RequestStatus.COMPLETED
            self.result = result
        
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "memory_file_path": self.memory_file_path,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time": self.processing_time,
            "wait_time": self.wait_time,
            "worker_id": self.worker_id,
            "error": self.error,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "metadata": self.metadata
        }

@dataclass
class QueueConfiguration:
    """Configuration for the analysis queue"""
    max_queue_size: int = 100
    max_concurrent_workers: int = 3
    worker_timeout_seconds: int = 300  # 5 minutes
    queue_timeout_seconds: int = 600   # 10 minutes
    priority_boost_threshold: int = 60  # seconds to boost priority
    cleanup_interval_seconds: int = 300  # 5 minutes
    max_memory_usage_mb: float = 1000.0
    max_cpu_usage_percent: float = 80.0
    max_memory_usage_percent: float = 85.0  # Add missing attribute
    enable_adaptive_scaling: bool = True
    enable_priority_boosting: bool = True

class AnalysisQueue:
    """
    Queue management system for serendipity analysis requests
    """
    
    def __init__(self, config: Optional[QueueConfiguration] = None, serendipity_service=None):
        """Initialize the analysis queue"""
        self.config = config or QueueConfiguration()
        self.serendipity_service = serendipity_service
        
        # Queue management
        self._request_queues: Dict[RequestPriority, queue.PriorityQueue] = {
            priority: queue.PriorityQueue() for priority in RequestPriority
        }
        self._active_requests: Dict[str, AnalysisRequest] = {}
        self._completed_requests: Dict[str, AnalysisRequest] = {}
        self._request_history: List[AnalysisRequest] = []
        
        # Thread management
        self._executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_workers,
            thread_name_prefix="AnalysisWorker"
        )
        self._active_futures: Dict[str, Future] = {}
        
        # Synchronization
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        
        # Background threads
        self._queue_manager_thread = None
        self._cleanup_thread = None
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "cancelled_requests": 0,
            "timeout_requests": 0,
            "average_wait_time": 0.0,
            "average_processing_time": 0.0,
            "current_queue_size": 0,
            "peak_queue_size": 0,
            "throughput_per_hour": 0.0
        }
        
        # Performance monitoring
        from performance_monitor import get_performance_monitor
        self.performance_monitor = get_performance_monitor()
        
        # Start background threads
        self._start_background_threads()
        
        logger.info(f"Analysis queue initialized with {self.config.max_concurrent_workers} workers")
    
    def _start_background_threads(self):
        """Start background management threads"""
        # Queue manager thread
        self._queue_manager_thread = threading.Thread(
            target=self._manage_queue,
            daemon=True,
            name="QueueManager"
        )
        self._queue_manager_thread.start()
        
        # Cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_completed_requests,
            daemon=True,
            name="QueueCleanup"
        )
        self._cleanup_thread.start()
    
    def submit_request(self, 
                      memory_file_path: Optional[str] = None,
                      user_id: Optional[str] = None,
                      priority: RequestPriority = RequestPriority.NORMAL,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit an analysis request to the queue
        
        Args:
            memory_file_path: Path to memory file (optional)
            user_id: User identifier (optional)
            priority: Request priority
            metadata: Additional metadata
            
        Returns:
            str: Request ID for tracking
            
        Raises:
            queue.Full: If queue is at capacity
        """
        # Check queue capacity
        current_size = self.get_queue_size()
        if current_size >= self.config.max_queue_size:
            raise queue.Full(f"Queue is at capacity ({self.config.max_queue_size})")
        
        # Create request
        request_id = str(uuid.uuid4())
        request = AnalysisRequest(
            request_id=request_id,
            user_id=user_id,
            memory_file_path=memory_file_path,
            priority=priority,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        # Add to appropriate priority queue
        with self._lock:
            # Use negative timestamp for priority queue ordering (earlier = higher priority)
            priority_score = (-time.time(), priority.value)
            self._request_queues[priority].put((priority_score, request))
            
            # Update statistics
            self._stats["total_requests"] += 1
            current_queue_size = self.get_queue_size()
            self._stats["current_queue_size"] = current_queue_size
            if current_queue_size > self._stats["peak_queue_size"]:
                self._stats["peak_queue_size"] = current_queue_size
        
        logger.info(f"Submitted analysis request {request_id} with priority {priority.name}")
        return request_id
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific request
        
        Args:
            request_id: Request ID
            
        Returns:
            dict: Request status information or None if not found
        """
        with self._lock:
            # Check active requests
            if request_id in self._active_requests:
                return self._active_requests[request_id].to_dict()
            
            # Check completed requests
            if request_id in self._completed_requests:
                return self._completed_requests[request_id].to_dict()
            
            # Check queue
            for priority_queue in self._request_queues.values():
                # Note: This is inefficient but necessary for status checking
                # In production, consider maintaining a separate index
                temp_items = []
                found = False
                
                try:
                    while not priority_queue.empty():
                        item = priority_queue.get_nowait()
                        temp_items.append(item)
                        if item[1].request_id == request_id:
                            found = True
                            break
                    
                    # Put items back
                    for item in temp_items:
                        priority_queue.put(item)
                    
                    if found:
                        return item[1].to_dict()
                        
                except queue.Empty:
                    pass
        
        return None
    
    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel a request if it's still queued or processing
        
        Args:
            request_id: Request ID to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        with self._lock:
            # Check if request is currently processing
            if request_id in self._active_requests:
                request = self._active_requests[request_id]
                
                # Try to cancel the future
                if request_id in self._active_futures:
                    future = self._active_futures[request_id]
                    if future.cancel():
                        request.status = RequestStatus.CANCELLED
                        request.completed_at = datetime.now()
                        self._move_to_completed(request)
                        self._stats["cancelled_requests"] += 1
                        logger.info(f"Cancelled processing request {request_id}")
                        return True
                    else:
                        logger.warning(f"Could not cancel processing request {request_id}")
                        return False
            
            # Check queues and remove if found
            for priority_queue in self._request_queues.values():
                temp_items = []
                found = False
                
                try:
                    while not priority_queue.empty():
                        item = priority_queue.get_nowait()
                        if item[1].request_id == request_id:
                            # Mark as cancelled and move to completed
                            request = item[1]
                            request.status = RequestStatus.CANCELLED
                            request.completed_at = datetime.now()
                            self._completed_requests[request_id] = request
                            self._stats["cancelled_requests"] += 1
                            found = True
                            logger.info(f"Cancelled queued request {request_id}")
                        else:
                            temp_items.append(item)
                    
                    # Put non-cancelled items back
                    for item in temp_items:
                        priority_queue.put(item)
                    
                    if found:
                        return True
                        
                except queue.Empty:
                    pass
        
        return False
    
    def get_queue_size(self) -> int:
        """Get total number of requests in all queues"""
        total_size = 0
        for priority_queue in self._request_queues.values():
            total_size += priority_queue.qsize()
        return total_size
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        with self._lock:
            # Calculate throughput
            completed_in_last_hour = 0
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            for request in self._request_history:
                if (request.completed_at and 
                    request.completed_at >= cutoff_time and 
                    request.status == RequestStatus.COMPLETED):
                    completed_in_last_hour += 1
            
            # Calculate average times
            recent_requests = [r for r in self._request_history[-100:] 
                             if r.status == RequestStatus.COMPLETED]
            
            avg_wait_time = 0.0
            avg_processing_time = 0.0
            
            if recent_requests:
                wait_times = [r.wait_time for r in recent_requests if r.wait_time]
                processing_times = [r.processing_time for r in recent_requests if r.processing_time]
                
                if wait_times:
                    avg_wait_time = sum(wait_times) / len(wait_times)
                if processing_times:
                    avg_processing_time = sum(processing_times) / len(processing_times)
            
            # Update statistics
            self._stats.update({
                "current_queue_size": self.get_queue_size(),
                "active_requests": len(self._active_requests),
                "throughput_per_hour": completed_in_last_hour,
                "average_wait_time": avg_wait_time,
                "average_processing_time": avg_processing_time
            })
            
            # Queue breakdown by priority
            queue_breakdown = {}
            for priority in RequestPriority:
                queue_breakdown[priority.name] = self._request_queues[priority].qsize()
            
            return {
                **self._stats,
                "queue_breakdown": queue_breakdown,
                "worker_utilization": len(self._active_requests) / self.config.max_concurrent_workers,
                "configuration": {
                    "max_queue_size": self.config.max_queue_size,
                    "max_concurrent_workers": self.config.max_concurrent_workers,
                    "worker_timeout_seconds": self.config.worker_timeout_seconds,
                    "queue_timeout_seconds": self.config.queue_timeout_seconds
                }
            }
    
    def _manage_queue(self):
        """Background thread for managing the queue and dispatching work"""
        while not self._shutdown_event.wait(1.0):  # Check every second
            try:
                # Check for available worker capacity
                if len(self._active_requests) >= self.config.max_concurrent_workers:
                    continue
                
                # Get next request from highest priority queue
                request = self._get_next_request()
                if not request:
                    continue
                
                # Check resource constraints
                if not self._check_resource_constraints():
                    # Put request back and wait
                    self._put_request_back(request)
                    time.sleep(5)  # Wait before retrying
                    continue
                
                # Start processing the request
                self._start_processing_request(request)
                
            except Exception as e:
                logger.error(f"Error in queue management: {e}")
    
    def _get_next_request(self) -> Optional[AnalysisRequest]:
        """Get the next request to process from priority queues"""
        with self._lock:
            # Check queues in priority order (highest first)
            for priority in sorted(RequestPriority, key=lambda p: p.value, reverse=True):
                priority_queue = self._request_queues[priority]
                
                try:
                    if not priority_queue.empty():
                        _, request = priority_queue.get_nowait()
                        
                        # Check if request has timed out
                        if self._is_request_expired(request):
                            request.status = RequestStatus.TIMEOUT
                            request.completed_at = datetime.now()
                            self._move_to_completed(request)
                            self._stats["timeout_requests"] += 1
                            continue
                        
                        # Apply priority boosting if enabled
                        if (self.config.enable_priority_boosting and 
                            self._should_boost_priority(request)):
                            # Boost priority and put back in higher queue
                            boosted_priority = self._boost_priority(request.priority)
                            if boosted_priority != request.priority:
                                request.priority = boosted_priority
                                priority_score = (-time.time(), boosted_priority.value)
                                self._request_queues[boosted_priority].put((priority_score, request))
                                logger.info(f"Boosted priority of request {request.request_id} to {boosted_priority.name}")
                                continue
                        
                        return request
                        
                except queue.Empty:
                    continue
        
        return None
    
    def _put_request_back(self, request: AnalysisRequest):
        """Put a request back in the queue"""
        with self._lock:
            priority_score = (-time.time(), request.priority.value)
            self._request_queues[request.priority].put((priority_score, request))
    
    def _is_request_expired(self, request: AnalysisRequest) -> bool:
        """Check if a request has exceeded the queue timeout"""
        if not request.created_at:
            return False
        
        age = (datetime.now() - request.created_at).total_seconds()
        return age > self.config.queue_timeout_seconds
    
    def _should_boost_priority(self, request: AnalysisRequest) -> bool:
        """Check if a request should have its priority boosted"""
        if not request.created_at:
            return False
        
        wait_time = (datetime.now() - request.created_at).total_seconds()
        return wait_time > self.config.priority_boost_threshold
    
    def _boost_priority(self, current_priority: RequestPriority) -> RequestPriority:
        """Boost priority to the next level"""
        if current_priority == RequestPriority.LOW:
            return RequestPriority.NORMAL
        elif current_priority == RequestPriority.NORMAL:
            return RequestPriority.HIGH
        elif current_priority == RequestPriority.HIGH:
            return RequestPriority.URGENT
        else:
            return current_priority  # Already at highest priority
    
    def _check_resource_constraints(self) -> bool:
        """Check if system resources allow for another worker"""
        if not self.config.enable_adaptive_scaling:
            return True
        
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > getattr(self.config, 'max_memory_usage_percent', 85.0):
                logger.warning(f"Memory usage too high: {memory.percent:.1f}%")
                return False
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.config.max_cpu_usage_percent:
                logger.warning(f"CPU usage too high: {cpu_percent:.1f}%")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking resource constraints: {e}")
            return True  # Allow processing if we can't check resources
    
    def _start_processing_request(self, request: AnalysisRequest):
        """Start processing a request in a worker thread"""
        worker_id = f"worker_{threading.get_ident()}_{int(time.time())}"
        
        with self._lock:
            request.start_processing(worker_id)
            self._active_requests[request.request_id] = request
        
        # Submit to thread pool
        future = self._executor.submit(self._process_request, request)
        
        with self._lock:
            self._active_futures[request.request_id] = future
        
        # Add completion callback
        future.add_done_callback(lambda f: self._on_request_completed(request.request_id, f))
        
        logger.info(f"Started processing request {request.request_id} with worker {worker_id}")
    
    def _process_request(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Process an analysis request"""
        operation_id = self.performance_monitor.start_operation(
            "queue_analysis",
            {"request_id": request.request_id, "priority": request.priority.name}
        )
        
        try:
            if not self.serendipity_service:
                raise Exception("Serendipity service not available")
            
            # Perform the analysis
            result = self.serendipity_service.analyze_memory(request.memory_file_path)
            
            # Track cache statistics
            cache_hits = 0
            cache_misses = 0
            if "metadata" in result and "cache_stats" in result["metadata"]:
                cache_stats = result["metadata"]["cache_stats"]
                cache_hits = cache_stats.get("hits", 0)
                cache_misses = cache_stats.get("misses", 0)
            
            # Update request with resource usage
            request.cache_hits = cache_hits
            request.cache_misses = cache_misses
            
            # Complete performance tracking
            self.performance_monitor.complete_operation(
                operation_id,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                ai_response_time=result.get("metadata", {}).get("ai_response_time"),
                data_size_mb=result.get("metadata", {}).get("data_size_mb", 0),
                chunk_count=result.get("metadata", {}).get("chunk_count", 0)
            )
            
            return result
            
        except Exception as e:
            self.performance_monitor.complete_operation(operation_id, error=e)
            raise
    
    def _on_request_completed(self, request_id: str, future: Future):
        """Handle completion of a request"""
        with self._lock:
            request = self._active_requests.get(request_id)
            if not request:
                return
            
            # Remove from active tracking
            del self._active_requests[request_id]
            if request_id in self._active_futures:
                del self._active_futures[request_id]
            
            try:
                # Get result or exception
                if future.cancelled():
                    request.status = RequestStatus.CANCELLED
                    self._stats["cancelled_requests"] += 1
                elif future.exception():
                    error = str(future.exception())
                    request.complete_processing(error=error)
                    self._stats["failed_requests"] += 1
                    logger.error(f"Request {request_id} failed: {error}")
                else:
                    result = future.result()
                    request.complete_processing(result=result)
                    self._stats["completed_requests"] += 1
                    logger.info(f"Request {request_id} completed successfully")
                
            except Exception as e:
                request.complete_processing(error=str(e))
                self._stats["failed_requests"] += 1
                logger.error(f"Error handling completion of request {request_id}: {e}")
            
            # Move to completed requests
            self._move_to_completed(request)
    
    def _move_to_completed(self, request: AnalysisRequest):
        """Move a request to completed status"""
        with self._lock:
            self._completed_requests[request.request_id] = request
            self._request_history.append(request)
            
            # Update queue size
            self._stats["current_queue_size"] = self.get_queue_size()
    
    def _cleanup_completed_requests(self):
        """Background thread for cleaning up old completed requests"""
        while not self._shutdown_event.wait(self.config.cleanup_interval_seconds):
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours of history
                
                with self._lock:
                    # Clean up completed requests
                    to_remove = []
                    for request_id, request in self._completed_requests.items():
                        if (request.completed_at and 
                            request.completed_at < cutoff_time):
                            to_remove.append(request_id)
                    
                    for request_id in to_remove:
                        del self._completed_requests[request_id]
                    
                    # Clean up request history (keep last 1000)
                    if len(self._request_history) > 1000:
                        self._request_history = self._request_history[-1000:]
                    
                    if to_remove:
                        logger.info(f"Cleaned up {len(to_remove)} old completed requests")
                
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def shutdown(self, timeout: int = 30):
        """Shutdown the queue system gracefully"""
        logger.info("Shutting down analysis queue...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel all queued requests
        with self._lock:
            cancelled_count = 0
            for priority_queue in self._request_queues.values():
                while not priority_queue.empty():
                    try:
                        _, request = priority_queue.get_nowait()
                        request.status = RequestStatus.CANCELLED
                        request.completed_at = datetime.now()
                        self._completed_requests[request.request_id] = request
                        cancelled_count += 1
                    except queue.Empty:
                        break
            
            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} queued requests")
        
        # Shutdown thread pool
        self._executor.shutdown(wait=True)
        
        # Wait for background threads
        if self._queue_manager_thread:
            self._queue_manager_thread.join(timeout=5)
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        logger.info("Analysis queue shutdown complete")

# Global queue instance
_analysis_queue = None

def get_analysis_queue(config: Optional[QueueConfiguration] = None, 
                      serendipity_service=None) -> AnalysisQueue:
    """Get global analysis queue instance"""
    global _analysis_queue
    if _analysis_queue is None:
        _analysis_queue = AnalysisQueue(config, serendipity_service)
    return _analysis_queue

def shutdown_analysis_queue():
    """Shutdown global analysis queue"""
    global _analysis_queue
    if _analysis_queue:
        _analysis_queue.shutdown()
        _analysis_queue = None