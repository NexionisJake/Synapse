"""
Performance Monitoring and Optimization Module for Synapse AI Web Application

This module provides comprehensive performance monitoring, resource tracking,
and automatic optimization for the serendipity analysis system.
"""

import time
import psutil
import threading
import queue
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
import gc
import sys

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis operations"""
    operation_id: str
    operation_type: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    ai_response_time: Optional[float] = None
    data_size_mb: float = 0.0
    chunk_count: int = 0
    error_occurred: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, error: Optional[Exception] = None):
        """Mark the operation as complete"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        if error:
            self.error_occurred = True
            self.error_message = str(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class SystemResourceSnapshot:
    """Snapshot of system resources at a point in time"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    process_memory_mb: float
    process_cpu_percent: float
    thread_count: int
    open_files: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class CacheStatistics:
    """Statistics for cache performance"""
    cache_name: str
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_size_mb: float = 0.0
    average_access_time_ms: float = 0.0
    hit_rate: float = 0.0
    
    def update_hit_rate(self):
        """Update the hit rate calculation"""
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class QueueMetrics:
    """Metrics for request queue management"""
    queue_name: str
    current_size: int = 0
    max_size: int = 0
    total_processed: int = 0
    total_failed: int = 0
    average_wait_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0
    throughput_per_minute: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for serendipity analysis
    """
    
    def __init__(self, config=None):
        """Initialize performance monitor"""
        from config import get_config
        self.config = config or get_config()
        
        # Performance tracking
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 operations
        self.resource_history: deque = deque(maxlen=500)   # Keep last 500 resource snapshots
        self.cache_stats: Dict[str, CacheStatistics] = {}
        self.queue_metrics: Dict[str, QueueMetrics] = {}
        
        # Monitoring configuration
        self.monitoring_enabled = self.config.ENABLE_PERFORMANCE_MONITORING
        self.resource_check_interval = 30  # seconds
        self.metrics_retention_hours = 24
        
        # Resource monitoring thread
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.RLock()
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # percent
        self.memory_threshold = 85.0  # percent
        self.disk_threshold = 90.0  # percent
        self.response_time_threshold = 30.0  # seconds
        
        # Optimization flags
        self.auto_optimization_enabled = True
        self.gc_optimization_enabled = True
        
        # Start monitoring if enabled
        if self.monitoring_enabled:
            self.start_monitoring()
        
        logger.info("Performance monitor initialized")
    
    def start_monitoring(self):
        """Start background resource monitoring"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background resource monitoring"""
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5)
            logger.info("Performance monitoring stopped")
    
    def _monitor_resources(self):
        """Background thread for monitoring system resources"""
        while not self._stop_monitoring.wait(self.resource_check_interval):
            try:
                snapshot = self._capture_resource_snapshot()
                
                with self._lock:
                    self.resource_history.append(snapshot)
                
                # Check for resource issues and trigger optimization
                if self.auto_optimization_enabled:
                    self._check_and_optimize(snapshot)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
    
    def _capture_resource_snapshot(self) -> SystemResourceSnapshot:
        """Capture current system resource usage"""
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024 * 1024)  # MB
            process_cpu = process.cpu_percent()
            
            # Additional process metrics
            try:
                thread_count = process.num_threads()
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                thread_count = 0
                open_files = 0
            
            return SystemResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                process_memory_mb=process_memory,
                process_cpu_percent=process_cpu,
                thread_count=thread_count,
                open_files=open_files
            )
        
        except Exception as e:
            logger.error(f"Error capturing resource snapshot: {e}")
            return SystemResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                process_memory_mb=0.0,
                process_cpu_percent=0.0,
                thread_count=0,
                open_files=0
            )
    
    def _check_and_optimize(self, snapshot: SystemResourceSnapshot):
        """Check resource usage and trigger optimizations if needed"""
        optimizations_triggered = []
        
        # Check CPU usage
        if snapshot.cpu_percent > self.cpu_threshold:
            logger.warning(f"High CPU usage detected: {snapshot.cpu_percent:.1f}%")
            optimizations_triggered.append("cpu_optimization")
        
        # Check memory usage
        if snapshot.memory_percent > self.memory_threshold:
            logger.warning(f"High memory usage detected: {snapshot.memory_percent:.1f}%")
            if self.gc_optimization_enabled:
                self._trigger_garbage_collection()
                optimizations_triggered.append("garbage_collection")
        
        # Check disk usage
        if snapshot.disk_usage_percent > self.disk_threshold:
            logger.warning(f"High disk usage detected: {snapshot.disk_usage_percent:.1f}%")
            optimizations_triggered.append("disk_cleanup")
        
        # Log optimizations
        if optimizations_triggered:
            logger.info(f"Triggered optimizations: {', '.join(optimizations_triggered)}")
    
    def _trigger_garbage_collection(self):
        """Trigger garbage collection to free memory"""
        try:
            before_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            # Force garbage collection
            collected = gc.collect()
            
            after_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            freed_mb = before_memory - after_memory
            
            logger.info(f"Garbage collection freed {freed_mb:.1f}MB, collected {collected} objects")
            
        except Exception as e:
            logger.error(f"Error during garbage collection: {e}")
    
    def start_operation(self, operation_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking a performance operation
        
        Args:
            operation_type: Type of operation (e.g., 'memory_load', 'ai_analysis', 'cache_lookup')
            metadata: Additional metadata for the operation
            
        Returns:
            str: Operation ID for tracking
        """
        operation_id = f"{operation_type}_{int(time.time() * 1000)}_{id(threading.current_thread())}"
        
        # Capture initial resource snapshot
        initial_snapshot = self._capture_resource_snapshot()
        
        metrics = PerformanceMetrics(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=time.time(),
            memory_usage_mb=initial_snapshot.process_memory_mb,
            cpu_usage_percent=initial_snapshot.process_cpu_percent,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics_history.append(metrics)
        
        return operation_id
    
    def complete_operation(self, operation_id: str, 
                          cache_hits: int = 0, 
                          cache_misses: int = 0,
                          ai_response_time: Optional[float] = None,
                          data_size_mb: float = 0.0,
                          chunk_count: int = 0,
                          error: Optional[Exception] = None):
        """
        Complete tracking of a performance operation
        
        Args:
            operation_id: Operation ID from start_operation
            cache_hits: Number of cache hits during operation
            cache_misses: Number of cache misses during operation
            ai_response_time: Time taken for AI response (if applicable)
            data_size_mb: Size of data processed in MB
            chunk_count: Number of chunks processed
            error: Exception if operation failed
        """
        with self._lock:
            # Find the metrics entry
            metrics = None
            for m in reversed(self.metrics_history):
                if m.operation_id == operation_id:
                    metrics = m
                    break
            
            if not metrics:
                logger.warning(f"Operation ID not found: {operation_id}")
                return
            
            # Capture final resource snapshot
            final_snapshot = self._capture_resource_snapshot()
            
            # Update metrics
            metrics.complete(error)
            metrics.cache_hits = cache_hits
            metrics.cache_misses = cache_misses
            metrics.ai_response_time = ai_response_time
            metrics.data_size_mb = data_size_mb
            metrics.chunk_count = chunk_count
            
            # Calculate resource usage during operation
            if metrics.duration and metrics.duration > 0:
                metrics.memory_usage_mb = final_snapshot.process_memory_mb
                metrics.cpu_usage_percent = final_snapshot.process_cpu_percent
        
        logger.debug(f"Completed operation {operation_id} in {metrics.duration:.2f}s")
    
    def update_cache_stats(self, cache_name: str, hit: bool, access_time_ms: float = 0.0):
        """
        Update cache statistics
        
        Args:
            cache_name: Name of the cache
            hit: Whether this was a cache hit or miss
            access_time_ms: Time taken to access cache in milliseconds
        """
        with self._lock:
            if cache_name not in self.cache_stats:
                self.cache_stats[cache_name] = CacheStatistics(cache_name=cache_name)
            
            stats = self.cache_stats[cache_name]
            stats.total_requests += 1
            
            if hit:
                stats.cache_hits += 1
            else:
                stats.cache_misses += 1
            
            # Update average access time
            if access_time_ms > 0:
                current_total_time = stats.average_access_time_ms * (stats.total_requests - 1)
                stats.average_access_time_ms = (current_total_time + access_time_ms) / stats.total_requests
            
            stats.update_hit_rate()
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            dict: Performance summary
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            # Filter recent metrics
            recent_metrics = [m for m in self.metrics_history 
                            if m.start_time >= cutoff_time and m.duration is not None]
            
            # Filter recent resource snapshots
            recent_resources = [r for r in self.resource_history 
                              if r.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No performance data available for the specified period"}
        
        # Calculate operation statistics
        operation_stats = defaultdict(list)
        for metrics in recent_metrics:
            operation_stats[metrics.operation_type].append(metrics)
        
        # Aggregate statistics by operation type
        aggregated_stats = {}
        for op_type, metrics_list in operation_stats.items():
            durations = [m.duration for m in metrics_list if m.duration]
            memory_usage = [m.memory_usage_mb for m in metrics_list]
            cache_hits = sum(m.cache_hits for m in metrics_list)
            cache_misses = sum(m.cache_misses for m in metrics_list)
            errors = sum(1 for m in metrics_list if m.error_occurred)
            
            aggregated_stats[op_type] = {
                "count": len(metrics_list),
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "avg_memory_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                "total_cache_hits": cache_hits,
                "total_cache_misses": cache_misses,
                "cache_hit_rate": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
                "error_count": errors,
                "error_rate": errors / len(metrics_list) if metrics_list else 0
            }
        
        # Calculate resource statistics
        resource_stats = {}
        if recent_resources:
            cpu_values = [r.cpu_percent for r in recent_resources]
            memory_values = [r.memory_percent for r in recent_resources]
            process_memory_values = [r.process_memory_mb for r in recent_resources]
            
            resource_stats = {
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
                "max_cpu_percent": max(cpu_values),
                "avg_memory_percent": sum(memory_values) / len(memory_values),
                "max_memory_percent": max(memory_values),
                "avg_process_memory_mb": sum(process_memory_values) / len(process_memory_values),
                "max_process_memory_mb": max(process_memory_values),
                "current_memory_available_mb": recent_resources[-1].memory_available_mb,
                "current_disk_free_gb": recent_resources[-1].disk_free_gb
            }
        
        # Get cache statistics
        cache_summary = {}
        for cache_name, stats in self.cache_stats.items():
            cache_summary[cache_name] = stats.to_dict()
        
        return {
            "time_period_hours": hours,
            "total_operations": len(recent_metrics),
            "operation_statistics": aggregated_stats,
            "resource_statistics": resource_stats,
            "cache_statistics": cache_summary,
            "queue_metrics": {name: metrics.to_dict() for name, metrics in self.queue_metrics.items()},
            "generated_at": datetime.now().isoformat()
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations based on performance data
        
        Returns:
            list: List of optimization recommendations
        """
        recommendations = []
        
        # Analyze recent performance
        summary = self.get_performance_summary(hours=1)
        
        if "error" in summary:
            return recommendations
        
        resource_stats = summary.get("resource_statistics", {})
        operation_stats = summary.get("operation_statistics", {})
        cache_stats = summary.get("cache_statistics", {})
        
        # CPU optimization recommendations
        avg_cpu = resource_stats.get("avg_cpu_percent", 0)
        max_cpu = resource_stats.get("max_cpu_percent", 0)
        
        if avg_cpu > 70:
            recommendations.append({
                "type": "cpu_optimization",
                "priority": "high" if avg_cpu > 85 else "medium",
                "title": "High CPU Usage Detected",
                "description": f"Average CPU usage is {avg_cpu:.1f}% (max: {max_cpu:.1f}%)",
                "suggestions": [
                    "Consider implementing request queuing to limit concurrent operations",
                    "Optimize AI model parameters for faster processing",
                    "Implement chunking for large memory datasets",
                    "Consider using a more powerful server or scaling horizontally"
                ]
            })
        
        # Memory optimization recommendations
        avg_memory = resource_stats.get("avg_memory_percent", 0)
        max_memory = resource_stats.get("max_memory_percent", 0)
        
        if avg_memory > 75:
            recommendations.append({
                "type": "memory_optimization",
                "priority": "high" if avg_memory > 90 else "medium",
                "title": "High Memory Usage Detected",
                "description": f"Average memory usage is {avg_memory:.1f}% (max: {max_memory:.1f}%)",
                "suggestions": [
                    "Implement more aggressive cache eviction policies",
                    "Reduce cache TTL values to free memory faster",
                    "Implement memory-efficient data structures",
                    "Consider processing data in smaller chunks",
                    "Enable automatic garbage collection optimization"
                ]
            })
        
        # Cache optimization recommendations
        for cache_name, stats in cache_stats.items():
            hit_rate = stats.get("hit_rate", 0)
            
            if hit_rate < 0.5:  # Less than 50% hit rate
                recommendations.append({
                    "type": "cache_optimization",
                    "priority": "medium",
                    "title": f"Low Cache Hit Rate for {cache_name}",
                    "description": f"Cache hit rate is only {hit_rate:.1%}",
                    "suggestions": [
                        "Increase cache TTL if data doesn't change frequently",
                        "Implement cache warming strategies",
                        "Review cache key generation for better locality",
                        "Consider increasing cache size limits"
                    ]
                })
        
        # Performance optimization recommendations
        for op_type, stats in operation_stats.items():
            avg_duration = stats.get("avg_duration", 0)
            error_rate = stats.get("error_rate", 0)
            
            if avg_duration > self.response_time_threshold:
                recommendations.append({
                    "type": "performance_optimization",
                    "priority": "medium",
                    "title": f"Slow {op_type} Operations",
                    "description": f"Average duration is {avg_duration:.1f}s (threshold: {self.response_time_threshold}s)",
                    "suggestions": [
                        "Implement operation timeout handling",
                        "Optimize data processing algorithms",
                        "Consider parallel processing for large datasets",
                        "Implement progressive loading for better user experience"
                    ]
                })
            
            if error_rate > 0.1:  # More than 10% error rate
                recommendations.append({
                    "type": "reliability_optimization",
                    "priority": "high",
                    "title": f"High Error Rate for {op_type}",
                    "description": f"Error rate is {error_rate:.1%}",
                    "suggestions": [
                        "Implement better error handling and retry logic",
                        "Add input validation and sanitization",
                        "Implement circuit breaker patterns for external services",
                        "Add comprehensive logging for error diagnosis"
                    ]
                })
        
        return recommendations
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """
        Export performance metrics to a file
        
        Args:
            filepath: Path to export file
            hours: Number of hours of data to export
        """
        try:
            summary = self.get_performance_summary(hours)
            recommendations = self.get_optimization_recommendations()
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "performance_summary": summary,
                "optimization_recommendations": recommendations,
                "configuration": {
                    "monitoring_enabled": self.monitoring_enabled,
                    "resource_check_interval": self.resource_check_interval,
                    "cpu_threshold": self.cpu_threshold,
                    "memory_threshold": self.memory_threshold,
                    "response_time_threshold": self.response_time_threshold
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Performance metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            raise

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor(config=None) -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)
    return _performance_monitor

def cleanup_performance_monitor():
    """Cleanup global performance monitor"""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.stop_monitoring()
        _performance_monitor = None