"""
Performance Benchmarking and Testing Suite for Synapse AI Web Application

This module provides comprehensive performance benchmarking, load testing,
and optimization validation for the serendipity analysis system.
"""

import time
import threading
import concurrent.futures
import statistics
import json
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import psutil
import gc
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Result of a performance benchmark"""
    benchmark_name: str
    test_type: str
    start_time: float
    end_time: float
    duration: float
    operations_count: int
    operations_per_second: float
    success_count: int
    failure_count: int
    success_rate: float
    
    # Performance metrics
    min_response_time: float
    max_response_time: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Resource metrics
    initial_memory_mb: float
    peak_memory_mb: float
    memory_delta_mb: float
    initial_cpu_percent: float
    peak_cpu_percent: float
    avg_cpu_percent: float
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # Additional metrics
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class LoadTestConfiguration:
    """Configuration for load testing"""
    concurrent_users: int = 10
    requests_per_user: int = 10
    ramp_up_time_seconds: int = 30
    test_duration_seconds: int = 300
    think_time_seconds: float = 1.0
    timeout_seconds: int = 60
    memory_data_sizes: List[str] = field(default_factory=lambda: ["small", "medium", "large"])
    enable_resource_monitoring: bool = True
    monitoring_interval_seconds: float = 1.0

class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking system
    """
    
    def __init__(self, serendipity_service=None, config=None):
        """Initialize the benchmark system"""
        self.serendipity_service = serendipity_service
        self.config = config
        
        # Test data generators
        self.test_data_generators = {
            "small": self._generate_small_memory_data,
            "medium": self._generate_medium_memory_data,
            "large": self._generate_large_memory_data,
            "xlarge": self._generate_xlarge_memory_data
        }
        
        # Benchmark results storage
        self.results: List[BenchmarkResult] = []
        
        # Resource monitoring
        self.resource_snapshots: List[Dict[str, Any]] = []
        self._monitoring_active = False
        self._monitoring_thread = None
        
        logger.info("Performance benchmark system initialized")
    
    @contextmanager
    def resource_monitoring(self, interval_seconds: float = 1.0):
        """Context manager for resource monitoring during tests"""
        self._start_resource_monitoring(interval_seconds)
        try:
            yield
        finally:
            self._stop_resource_monitoring()
    
    def _start_resource_monitoring(self, interval_seconds: float):
        """Start background resource monitoring"""
        self._monitoring_active = True
        self.resource_snapshots.clear()
        
        def monitor():
            while self._monitoring_active:
                try:
                    snapshot = {
                        "timestamp": time.time(),
                        "cpu_percent": psutil.cpu_percent(),
                        "memory_percent": psutil.virtual_memory().percent,
                        "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
                        "process_memory_mb": psutil.Process().memory_info().rss / (1024 * 1024),
                        "process_cpu_percent": psutil.Process().cpu_percent(),
                        "thread_count": threading.active_count()
                    }
                    self.resource_snapshots.append(snapshot)
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Error in resource monitoring: {e}")
        
        self._monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self._monitoring_thread.start()
    
    def _stop_resource_monitoring(self):
        """Stop background resource monitoring"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
    
    def _generate_small_memory_data(self) -> Dict[str, Any]:
        """Generate small test memory data (5-10 insights)"""
        insights = []
        for i in range(random.randint(5, 10)):
            insights.append({
                "content": f"Test insight {i}: " + self._random_text(50, 150),
                "category": random.choice(["technical", "personal", "creative", "analytical"]),
                "confidence": random.uniform(0.6, 0.95),
                "tags": [self._random_word() for _ in range(random.randint(1, 3))],
                "timestamp": datetime.now().isoformat()
            })
        
        conversations = []
        for i in range(random.randint(2, 5)):
            conversations.append({
                "summary": f"Conversation {i}: " + self._random_text(100, 300),
                "key_themes": [self._random_word() for _ in range(random.randint(2, 4))],
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "insights": insights,
            "conversation_summaries": conversations,
            "metadata": {
                "total_insights": len(insights),
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _generate_medium_memory_data(self) -> Dict[str, Any]:
        """Generate medium test memory data (20-50 insights)"""
        insights = []
        for i in range(random.randint(20, 50)):
            insights.append({
                "content": f"Medium insight {i}: " + self._random_text(100, 400),
                "category": random.choice(["technical", "personal", "creative", "analytical", "philosophical", "practical"]),
                "confidence": random.uniform(0.5, 0.98),
                "tags": [self._random_word() for _ in range(random.randint(2, 5))],
                "evidence": self._random_text(50, 200),
                "timestamp": datetime.now().isoformat()
            })
        
        conversations = []
        for i in range(random.randint(10, 20)):
            conversations.append({
                "summary": f"Medium conversation {i}: " + self._random_text(200, 600),
                "key_themes": [self._random_word() for _ in range(random.randint(3, 6))],
                "insights_count": random.randint(1, 5),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "insights": insights,
            "conversation_summaries": conversations,
            "metadata": {
                "total_insights": len(insights),
                "last_updated": datetime.now().isoformat(),
                "version": "2.0"
            }
        }
    
    def _generate_large_memory_data(self) -> Dict[str, Any]:
        """Generate large test memory data (100-200 insights)"""
        insights = []
        categories = ["technical", "personal", "creative", "analytical", "philosophical", "practical", "strategic", "emotional"]
        
        for i in range(random.randint(100, 200)):
            insights.append({
                "content": f"Large insight {i}: " + self._random_text(200, 800),
                "category": random.choice(categories),
                "confidence": random.uniform(0.4, 0.99),
                "tags": [self._random_word() for _ in range(random.randint(3, 8))],
                "evidence": self._random_text(100, 500),
                "timestamp": datetime.now().isoformat(),
                "source": f"source_{random.randint(1, 20)}"
            })
        
        conversations = []
        for i in range(random.randint(30, 60)):
            conversations.append({
                "summary": f"Large conversation {i}: " + self._random_text(400, 1200),
                "key_themes": [self._random_word() for _ in range(random.randint(4, 10))],
                "insights_count": random.randint(2, 8),
                "duration_minutes": random.randint(15, 120),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "insights": insights,
            "conversation_summaries": conversations,
            "metadata": {
                "total_insights": len(insights),
                "total_conversations": len(conversations),
                "last_updated": datetime.now().isoformat(),
                "version": "2.1",
                "data_quality_score": random.uniform(0.7, 0.95)
            }
        }
    
    def _generate_xlarge_memory_data(self) -> Dict[str, Any]:
        """Generate extra large test memory data (500+ insights)"""
        insights = []
        categories = ["technical", "personal", "creative", "analytical", "philosophical", "practical", 
                     "strategic", "emotional", "social", "professional", "academic", "artistic"]
        
        for i in range(random.randint(500, 1000)):
            insights.append({
                "content": f"XLarge insight {i}: " + self._random_text(300, 1500),
                "category": random.choice(categories),
                "confidence": random.uniform(0.3, 0.99),
                "tags": [self._random_word() for _ in range(random.randint(4, 12))],
                "evidence": self._random_text(200, 800),
                "timestamp": datetime.now().isoformat(),
                "source": f"source_{random.randint(1, 50)}",
                "complexity_score": random.uniform(0.1, 1.0),
                "related_insights": [random.randint(0, i) for _ in range(random.randint(0, 3))]
            })
        
        conversations = []
        for i in range(random.randint(100, 200)):
            conversations.append({
                "summary": f"XLarge conversation {i}: " + self._random_text(600, 2000),
                "key_themes": [self._random_word() for _ in range(random.randint(5, 15))],
                "insights_count": random.randint(3, 15),
                "duration_minutes": random.randint(20, 180),
                "participants": random.randint(1, 5),
                "timestamp": datetime.now().isoformat(),
                "quality_rating": random.uniform(0.5, 1.0)
            })
        
        return {
            "insights": insights,
            "conversation_summaries": conversations,
            "metadata": {
                "total_insights": len(insights),
                "total_conversations": len(conversations),
                "last_updated": datetime.now().isoformat(),
                "version": "3.0",
                "data_quality_score": random.uniform(0.6, 0.9),
                "processing_notes": "Generated for performance testing"
            }
        }
    
    def _random_text(self, min_length: int, max_length: int) -> str:
        """Generate random text of specified length"""
        words = [
            "analysis", "insight", "pattern", "connection", "discovery", "understanding",
            "knowledge", "wisdom", "experience", "learning", "growth", "development",
            "innovation", "creativity", "solution", "problem", "challenge", "opportunity",
            "strategy", "approach", "method", "technique", "process", "system",
            "framework", "model", "theory", "concept", "idea", "thought"
        ]
        
        text = ""
        target_length = random.randint(min_length, max_length)
        
        while len(text) < target_length:
            word = random.choice(words)
            if text:
                text += " " + word
            else:
                text = word
        
        return text[:target_length]
    
    def _random_word(self) -> str:
        """Generate a random word"""
        return ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 12)))
    
    def benchmark_memory_loading(self, data_sizes: List[str] = None, iterations: int = 10) -> BenchmarkResult:
        """
        Benchmark memory data loading performance
        
        Args:
            data_sizes: List of data sizes to test
            iterations: Number of iterations per size
            
        Returns:
            BenchmarkResult: Benchmark results
        """
        if not self.serendipity_service:
            raise ValueError("Serendipity service not available for benchmarking")
        
        data_sizes = data_sizes or ["small", "medium", "large"]
        
        logger.info(f"Starting memory loading benchmark with {len(data_sizes)} sizes, {iterations} iterations each")
        
        all_response_times = []
        success_count = 0
        failure_count = 0
        cache_hits = 0
        cache_misses = 0
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        initial_cpu = psutil.cpu_percent()
        peak_memory = initial_memory
        cpu_readings = []
        
        with self.resource_monitoring():
            for size in data_sizes:
                generator = self.test_data_generators.get(size)
                if not generator:
                    logger.warning(f"No generator for size {size}")
                    continue
                
                for i in range(iterations):
                    try:
                        # Generate test data
                        test_data = generator()
                        
                        # Create temporary file
                        test_file = f"test_memory_{size}_{i}.json"
                        with open(test_file, 'w') as f:
                            json.dump(test_data, f)
                        
                        # Benchmark loading
                        load_start = time.time()
                        memory_data = self.serendipity_service._load_memory_data(test_file)
                        load_end = time.time()
                        
                        response_time = load_end - load_start
                        all_response_times.append(response_time)
                        success_count += 1
                        
                        # Track memory usage
                        current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                        peak_memory = max(peak_memory, current_memory)
                        
                        # Track CPU
                        cpu_readings.append(psutil.cpu_percent())
                        
                        # Clean up
                        Path(test_file).unlink(missing_ok=True)
                        
                    except Exception as e:
                        logger.error(f"Error in memory loading benchmark: {e}")
                        failure_count += 1
                        Path(f"test_memory_{size}_{i}.json").unlink(missing_ok=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate statistics
        operations_count = success_count + failure_count
        operations_per_second = operations_count / duration if duration > 0 else 0
        success_rate = success_count / operations_count if operations_count > 0 else 0
        
        # Response time statistics
        if all_response_times:
            all_response_times.sort()
            min_response = min(all_response_times)
            max_response = max(all_response_times)
            avg_response = statistics.mean(all_response_times)
            median_response = statistics.median(all_response_times)
            p95_response = all_response_times[int(0.95 * len(all_response_times))]
            p99_response = all_response_times[int(0.99 * len(all_response_times))]
        else:
            min_response = max_response = avg_response = median_response = p95_response = p99_response = 0.0
        
        # CPU statistics
        avg_cpu = statistics.mean(cpu_readings) if cpu_readings else initial_cpu
        peak_cpu = max(cpu_readings) if cpu_readings else initial_cpu
        
        result = BenchmarkResult(
            benchmark_name="memory_loading",
            test_type="performance",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            operations_count=operations_count,
            operations_per_second=operations_per_second,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            min_response_time=min_response,
            max_response_time=max_response,
            avg_response_time=avg_response,
            median_response_time=median_response,
            p95_response_time=p95_response,
            p99_response_time=p99_response,
            initial_memory_mb=initial_memory,
            peak_memory_mb=peak_memory,
            memory_delta_mb=peak_memory - initial_memory,
            initial_cpu_percent=initial_cpu,
            peak_cpu_percent=peak_cpu,
            avg_cpu_percent=avg_cpu,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
            metadata={
                "data_sizes": data_sizes,
                "iterations_per_size": iterations,
                "resource_snapshots_count": len(self.resource_snapshots)
            }
        )
        
        self.results.append(result)
        logger.info(f"Memory loading benchmark completed: {success_count}/{operations_count} successful operations")
        
        return result
    
    def benchmark_cache_performance(self, cache_name: str = "memory_cache", 
                                  operations: int = 1000) -> BenchmarkResult:
        """
        Benchmark cache performance
        
        Args:
            cache_name: Name of cache to benchmark
            operations: Number of operations to perform
            
        Returns:
            BenchmarkResult: Benchmark results
        """
        from enhanced_cache import get_cache
        
        cache = get_cache(cache_name)
        
        logger.info(f"Starting cache performance benchmark with {operations} operations")
        
        # Test data
        test_keys = [f"test_key_{i}" for i in range(operations)]
        test_values = [{"data": self._random_text(100, 500), "id": i} for i in range(operations)]
        
        put_times = []
        get_times = []
        success_count = 0
        failure_count = 0
        cache_hits = 0
        cache_misses = 0
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        initial_cpu = psutil.cpu_percent()
        peak_memory = initial_memory
        cpu_readings = []
        
        with self.resource_monitoring():
            # Benchmark PUT operations
            for i in range(operations // 2):
                try:
                    put_start = time.time()
                    cache.put(test_keys[i], test_values[i])
                    put_end = time.time()
                    
                    put_times.append(put_end - put_start)
                    success_count += 1
                    
                    # Track resources
                    current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    peak_memory = max(peak_memory, current_memory)
                    cpu_readings.append(psutil.cpu_percent())
                    
                except Exception as e:
                    logger.error(f"Error in cache PUT: {e}")
                    failure_count += 1
            
            # Benchmark GET operations (mix of hits and misses)
            for i in range(operations // 2):
                try:
                    # 70% chance of cache hit, 30% chance of miss
                    if random.random() < 0.7 and i < len(test_keys) // 2:
                        key = test_keys[i]  # Should be a hit
                    else:
                        key = f"missing_key_{i}"  # Should be a miss
                    
                    get_start = time.time()
                    value = cache.get(key)
                    get_end = time.time()
                    
                    get_times.append(get_end - get_start)
                    
                    if value is not None:
                        cache_hits += 1
                    else:
                        cache_misses += 1
                    
                    success_count += 1
                    
                    # Track resources
                    current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    peak_memory = max(peak_memory, current_memory)
                    cpu_readings.append(psutil.cpu_percent())
                    
                except Exception as e:
                    logger.error(f"Error in cache GET: {e}")
                    failure_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Combine all response times
        all_response_times = put_times + get_times
        
        # Calculate statistics
        operations_count = success_count + failure_count
        operations_per_second = operations_count / duration if duration > 0 else 0
        success_rate = success_count / operations_count if operations_count > 0 else 0
        
        # Response time statistics
        if all_response_times:
            all_response_times.sort()
            min_response = min(all_response_times)
            max_response = max(all_response_times)
            avg_response = statistics.mean(all_response_times)
            median_response = statistics.median(all_response_times)
            p95_response = all_response_times[int(0.95 * len(all_response_times))]
            p99_response = all_response_times[int(0.99 * len(all_response_times))]
        else:
            min_response = max_response = avg_response = median_response = p95_response = p99_response = 0.0
        
        # CPU statistics
        avg_cpu = statistics.mean(cpu_readings) if cpu_readings else initial_cpu
        peak_cpu = max(cpu_readings) if cpu_readings else initial_cpu
        
        result = BenchmarkResult(
            benchmark_name="cache_performance",
            test_type="performance",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            operations_count=operations_count,
            operations_per_second=operations_per_second,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            min_response_time=min_response,
            max_response_time=max_response,
            avg_response_time=avg_response,
            median_response_time=median_response,
            p95_response_time=p95_response,
            p99_response_time=p99_response,
            initial_memory_mb=initial_memory,
            peak_memory_mb=peak_memory,
            memory_delta_mb=peak_memory - initial_memory,
            initial_cpu_percent=initial_cpu,
            peak_cpu_percent=peak_cpu,
            avg_cpu_percent=avg_cpu,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
            metadata={
                "cache_name": cache_name,
                "put_operations": len(put_times),
                "get_operations": len(get_times),
                "avg_put_time": statistics.mean(put_times) if put_times else 0,
                "avg_get_time": statistics.mean(get_times) if get_times else 0,
                "cache_statistics": cache.get_statistics()
            }
        )
        
        self.results.append(result)
        logger.info(f"Cache performance benchmark completed: {success_count}/{operations_count} successful operations")
        
        return result
    
    def run_load_test(self, config: LoadTestConfiguration) -> BenchmarkResult:
        """
        Run a comprehensive load test
        
        Args:
            config: Load test configuration
            
        Returns:
            BenchmarkResult: Load test results
        """
        if not self.serendipity_service:
            raise ValueError("Serendipity service not available for load testing")
        
        logger.info(f"Starting load test: {config.concurrent_users} users, "
                   f"{config.requests_per_user} requests each")
        
        all_response_times = []
        success_count = 0
        failure_count = 0
        cache_hits = 0
        cache_misses = 0
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        initial_cpu = psutil.cpu_percent()
        peak_memory = initial_memory
        cpu_readings = []
        
        def user_simulation(user_id: int) -> List[Tuple[float, bool, int, int]]:
            """Simulate a user performing requests"""
            user_results = []
            
            # Ramp up delay
            ramp_delay = (config.ramp_up_time_seconds / config.concurrent_users) * user_id
            time.sleep(ramp_delay)
            
            for request_id in range(config.requests_per_user):
                try:
                    # Generate test data
                    data_size = random.choice(config.memory_data_sizes)
                    generator = self.test_data_generators.get(data_size)
                    if not generator:
                        continue
                    
                    test_data = generator()
                    test_file = f"load_test_{user_id}_{request_id}.json"
                    
                    with open(test_file, 'w') as f:
                        json.dump(test_data, f)
                    
                    # Perform analysis
                    request_start = time.time()
                    result = self.serendipity_service.analyze_memory(test_file)
                    request_end = time.time()
                    
                    response_time = request_end - request_start
                    
                    # Extract cache stats
                    hits = result.get("metadata", {}).get("cache_stats", {}).get("hits", 0)
                    misses = result.get("metadata", {}).get("cache_stats", {}).get("misses", 0)
                    
                    user_results.append((response_time, True, hits, misses))
                    
                    # Clean up
                    Path(test_file).unlink(missing_ok=True)
                    
                    # Think time
                    if config.think_time_seconds > 0:
                        time.sleep(config.think_time_seconds)
                
                except Exception as e:
                    logger.error(f"Error in user {user_id} request {request_id}: {e}")
                    user_results.append((0.0, False, 0, 0))
                    Path(f"load_test_{user_id}_{request_id}.json").unlink(missing_ok=True)
            
            return user_results
        
        # Run load test with resource monitoring
        with self.resource_monitoring(config.monitoring_interval_seconds):
            with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrent_users) as executor:
                # Submit all user simulations
                futures = [
                    executor.submit(user_simulation, user_id)
                    for user_id in range(config.concurrent_users)
                ]
                
                # Collect results
                for future in concurrent.futures.as_completed(futures, timeout=config.timeout_seconds):
                    try:
                        user_results = future.result()
                        for response_time, success, hits, misses in user_results:
                            if success:
                                all_response_times.append(response_time)
                                success_count += 1
                                cache_hits += hits
                                cache_misses += misses
                            else:
                                failure_count += 1
                        
                        # Track peak memory
                        current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                        peak_memory = max(peak_memory, current_memory)
                        cpu_readings.append(psutil.cpu_percent())
                        
                    except concurrent.futures.TimeoutError:
                        logger.error("Load test timeout")
                        failure_count += 1
                    except Exception as e:
                        logger.error(f"Error collecting load test results: {e}")
                        failure_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate statistics
        operations_count = success_count + failure_count
        operations_per_second = operations_count / duration if duration > 0 else 0
        success_rate = success_count / operations_count if operations_count > 0 else 0
        
        # Response time statistics
        if all_response_times:
            all_response_times.sort()
            min_response = min(all_response_times)
            max_response = max(all_response_times)
            avg_response = statistics.mean(all_response_times)
            median_response = statistics.median(all_response_times)
            p95_response = all_response_times[int(0.95 * len(all_response_times))]
            p99_response = all_response_times[int(0.99 * len(all_response_times))]
        else:
            min_response = max_response = avg_response = median_response = p95_response = p99_response = 0.0
        
        # CPU statistics
        avg_cpu = statistics.mean(cpu_readings) if cpu_readings else initial_cpu
        peak_cpu = max(cpu_readings) if cpu_readings else initial_cpu
        
        result = BenchmarkResult(
            benchmark_name="load_test",
            test_type="load",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            operations_count=operations_count,
            operations_per_second=operations_per_second,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            min_response_time=min_response,
            max_response_time=max_response,
            avg_response_time=avg_response,
            median_response_time=median_response,
            p95_response_time=p95_response,
            p99_response_time=p99_response,
            initial_memory_mb=initial_memory,
            peak_memory_mb=peak_memory,
            memory_delta_mb=peak_memory - initial_memory,
            initial_cpu_percent=initial_cpu,
            peak_cpu_percent=peak_cpu,
            avg_cpu_percent=avg_cpu,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
            metadata={
                "concurrent_users": config.concurrent_users,
                "requests_per_user": config.requests_per_user,
                "ramp_up_time_seconds": config.ramp_up_time_seconds,
                "think_time_seconds": config.think_time_seconds,
                "data_sizes": config.memory_data_sizes,
                "resource_snapshots_count": len(self.resource_snapshots)
            }
        )
        
        self.results.append(result)
        logger.info(f"Load test completed: {success_count}/{operations_count} successful operations")
        
        return result
    
    def export_results(self, filepath: str):
        """
        Export benchmark results to a file
        
        Args:
            filepath: Path to export file
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "benchmark_results": [result.to_dict() for result in self.results],
                "resource_snapshots": self.resource_snapshots,
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024 * 1024 * 1024),
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Benchmark results exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting benchmark results: {e}")
            raise
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all benchmark results"""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        summary = {
            "total_benchmarks": len(self.results),
            "benchmark_types": list(set(r.test_type for r in self.results)),
            "total_operations": sum(r.operations_count for r in self.results),
            "total_successes": sum(r.success_count for r in self.results),
            "total_failures": sum(r.failure_count for r in self.results),
            "overall_success_rate": 0.0,
            "performance_metrics": {},
            "resource_metrics": {},
            "cache_metrics": {}
        }
        
        # Calculate overall success rate
        total_ops = summary["total_operations"]
        if total_ops > 0:
            summary["overall_success_rate"] = summary["total_successes"] / total_ops
        
        # Aggregate performance metrics
        response_times = []
        throughputs = []
        for result in self.results:
            if result.avg_response_time > 0:
                response_times.append(result.avg_response_time)
            if result.operations_per_second > 0:
                throughputs.append(result.operations_per_second)
        
        if response_times:
            summary["performance_metrics"] = {
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times)
            }
        
        if throughputs:
            summary["performance_metrics"]["avg_throughput"] = statistics.mean(throughputs)
            summary["performance_metrics"]["max_throughput"] = max(throughputs)
        
        # Aggregate resource metrics
        memory_deltas = [r.memory_delta_mb for r in self.results if r.memory_delta_mb > 0]
        cpu_peaks = [r.peak_cpu_percent for r in self.results if r.peak_cpu_percent > 0]
        
        if memory_deltas:
            summary["resource_metrics"]["avg_memory_delta_mb"] = statistics.mean(memory_deltas)
            summary["resource_metrics"]["max_memory_delta_mb"] = max(memory_deltas)
        
        if cpu_peaks:
            summary["resource_metrics"]["avg_peak_cpu"] = statistics.mean(cpu_peaks)
            summary["resource_metrics"]["max_peak_cpu"] = max(cpu_peaks)
        
        # Aggregate cache metrics
        total_cache_hits = sum(r.cache_hits for r in self.results)
        total_cache_misses = sum(r.cache_misses for r in self.results)
        
        if total_cache_hits + total_cache_misses > 0:
            summary["cache_metrics"] = {
                "total_cache_hits": total_cache_hits,
                "total_cache_misses": total_cache_misses,
                "overall_cache_hit_rate": total_cache_hits / (total_cache_hits + total_cache_misses)
            }
        
        return summary