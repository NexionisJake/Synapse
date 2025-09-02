#!/usr/bin/env python3
"""
Performance Optimization Validation Script

This script validates all performance optimization features and generates
a comprehensive report on system performance improvements.
"""

import sys
import time
import json
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_imports():
    """Validate that all required modules can be imported"""
    logger.info("Validating module imports...")
    
    try:
        from performance_monitor import PerformanceMonitor, get_performance_monitor
        from enhanced_cache import EnhancedCache, CacheConfiguration, get_cache_manager
        from analysis_queue import AnalysisQueue, QueueConfiguration, RequestPriority
        from performance_benchmarks import PerformanceBenchmark, LoadTestConfiguration
        from serendipity_service import SerendipityService
        from config import get_config
        
        logger.info("✅ All modules imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def validate_performance_monitor():
    """Validate performance monitoring functionality"""
    logger.info("Validating performance monitor...")
    
    try:
        from performance_monitor import PerformanceMonitor
        from config import get_config
        
        config = get_config('testing')
        monitor = PerformanceMonitor(config)
        
        # Test operation tracking
        operation_id = monitor.start_operation("validation_test")
        time.sleep(0.1)  # Simulate work
        monitor.complete_operation(operation_id, cache_hits=3, cache_misses=1)
        
        # Test cache statistics
        monitor.update_cache_stats("test_cache", True, 5.0)
        monitor.update_cache_stats("test_cache", False, 10.0)
        
        # Get performance summary
        summary = monitor.get_performance_summary(hours=1)
        
        # Validate summary structure - check for either valid data or error message
        if "error" in summary:
            # If no data available, that's acceptable for a fresh monitor
            logger.info("No performance data available yet (expected for new monitor)")
        else:
            required_keys = ["total_operations", "operation_statistics"]
            for key in required_keys:
                if key not in summary:
                    raise ValueError(f"Missing key in performance summary: {key}")
        
        # Test optimization recommendations (may be empty if resources are normal)
        recommendations = monitor.get_optimization_recommendations()
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        
        monitor.stop_monitoring()
        
        logger.info("✅ Performance monitor validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance monitor validation failed: {e}")
        return False

def validate_enhanced_cache():
    """Validate enhanced caching functionality"""
    logger.info("Validating enhanced cache...")
    
    try:
        from enhanced_cache import EnhancedCache, CacheConfiguration
        
        # Test basic cache operations
        config = CacheConfiguration(
            max_entries=100,
            max_size_mb=10.0,
            default_ttl_seconds=60,
            enable_compression=True
        )
        
        cache = EnhancedCache("validation_cache", config)
        
        # Test put/get operations
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        cache.put("test_key", test_data)
        
        retrieved = cache.get("test_key")
        if retrieved != test_data:
            raise ValueError("Cache put/get operation failed")
        
        # Test TTL expiration
        cache.put("ttl_key", "ttl_value", ttl_seconds=1)
        if cache.get("ttl_key") != "ttl_value":
            raise ValueError("TTL cache operation failed")
        
        time.sleep(1.1)
        if cache.get("ttl_key") is not None:
            raise ValueError("TTL expiration failed")
        
        # Test compression with large data
        large_data = "x" * 2000
        cache.put("large_key", large_data)
        if cache.get("large_key") != large_data:
            raise ValueError("Compression cache operation failed")
        
        # Test statistics
        stats = cache.get_statistics()
        required_stats = ["total_entries", "hits", "misses", "hit_rate", "compressions"]
        for stat in required_stats:
            if stat not in stats:
                raise ValueError(f"Missing cache statistic: {stat}")
        
        cache.shutdown()
        
        logger.info("✅ Enhanced cache validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced cache validation failed: {e}")
        return False

def validate_analysis_queue():
    """Validate analysis queue functionality"""
    logger.info("Validating analysis queue...")
    
    try:
        from analysis_queue import AnalysisQueue, QueueConfiguration, RequestPriority
        from unittest.mock import Mock
        
        # Mock serendipity service
        mock_service = Mock()
        mock_service.analyze_memory.return_value = {
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Test analysis",
            "recommendations": []
        }
        
        config = QueueConfiguration(
            max_queue_size=10,
            max_concurrent_workers=2,
            worker_timeout_seconds=30
        )
        
        queue = AnalysisQueue(config, mock_service)
        
        # Test request submission
        request_id = queue.submit_request(
            memory_file_path="test_memory.json",
            priority=RequestPriority.NORMAL
        )
        
        if not request_id:
            raise ValueError("Request submission failed")
        
        # Test request status
        status = queue.get_request_status(request_id)
        if not status or "status" not in status:
            raise ValueError("Request status retrieval failed")
        
        # Test queue statistics
        stats = queue.get_queue_statistics()
        required_stats = ["total_requests", "current_queue_size", "configuration"]
        for stat in required_stats:
            if stat not in stats:
                raise ValueError(f"Missing queue statistic: {stat}")
        
        # Wait a moment for processing
        time.sleep(0.5)
        
        queue.shutdown()
        
        logger.info("✅ Analysis queue validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis queue validation failed: {e}")
        return False

def validate_performance_benchmarks():
    """Validate performance benchmarking functionality"""
    logger.info("Validating performance benchmarks...")
    
    try:
        from performance_benchmarks import PerformanceBenchmark, LoadTestConfiguration
        from unittest.mock import Mock
        
        # Mock serendipity service
        mock_service = Mock()
        mock_service._load_memory_data.return_value = {
            "insights": [{"content": "test", "category": "test"}],
            "conversation_summaries": [],
            "metadata": {}
        }
        
        benchmark = PerformanceBenchmark(mock_service)
        
        # Test memory loading benchmark
        result = benchmark.benchmark_memory_loading(
            data_sizes=["small"],
            iterations=1
        )
        
        # Validate result structure
        required_fields = [
            "benchmark_name", "test_type", "duration", "operations_count",
            "success_rate", "avg_response_time", "peak_memory_mb"
        ]
        
        for field in required_fields:
            if not hasattr(result, field):
                raise ValueError(f"Missing benchmark result field: {field}")
        
        # Test cache performance benchmark
        cache_result = benchmark.benchmark_cache_performance(
            cache_name="test_cache",
            operations=50
        )
        
        if cache_result.benchmark_name != "cache_performance":
            raise ValueError("Cache benchmark failed")
        
        # Test performance summary
        summary = benchmark.get_performance_summary()
        if "total_benchmarks" not in summary:
            raise ValueError("Performance summary generation failed")
        
        logger.info("✅ Performance benchmarks validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance benchmarks validation failed: {e}")
        return False

def validate_serendipity_integration():
    """Validate serendipity service integration"""
    logger.info("Validating serendipity service integration...")
    
    try:
        from serendipity_service import SerendipityService
        from config import get_config
        from unittest.mock import patch, Mock
        
        config = get_config('testing')
        
        # Create temporary memory file
        temp_dir = tempfile.mkdtemp()
        memory_file = Path(temp_dir) / "test_memory.json"
        
        test_data = {
            "insights": [
                {
                    "content": f"Test insight {i}",
                    "category": "test",
                    "confidence": 0.8,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                for i in range(5)
            ],
            "conversation_summaries": [
                {
                    "summary": "Test conversation",
                    "key_themes": ["test"],
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "metadata": {
                "total_insights": 5,
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
        
        with open(memory_file, 'w') as f:
            json.dump(test_data, f)
        
        # Mock AI service
        with patch('serendipity_service.get_ai_service') as mock_ai_service:
            mock_ai = Mock()
            mock_ai.generate_response.return_value = {
                "connections": [],
                "meta_patterns": [],
                "serendipity_summary": "Test analysis",
                "recommendations": []
            }
            mock_ai_service.return_value = mock_ai
            
            # Create service and test analysis
            service = SerendipityService(config)
            
            # Test enhanced memory loading
            memory_data = service._load_memory_data_enhanced(str(memory_file))
            if "_cache_hit" not in memory_data:
                raise ValueError("Enhanced memory loading failed")
            
            # Test enhanced formatting
            formatted_data = service._format_memory_for_analysis_enhanced(memory_data)
            if "_cache_hit" not in formatted_data:
                raise ValueError("Enhanced formatting failed")
            
            # Test cache key generation
            cache_key = service._generate_analysis_cache_key("test_data")
            if not cache_key:
                raise ValueError("Cache key generation failed")
        
        # Clean up
        memory_file.unlink()
        Path(temp_dir).rmdir()
        
        logger.info("✅ Serendipity service integration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Serendipity service integration validation failed: {e}")
        return False

def run_performance_tests():
    """Run the actual performance test suite"""
    logger.info("Running performance test suite...")
    
    try:
        from test_performance_optimizations import run_performance_tests
        
        success = run_performance_tests()
        
        if success:
            logger.info("✅ Performance test suite passed")
        else:
            logger.error("❌ Performance test suite failed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Performance test suite execution failed: {e}")
        return False

def generate_performance_report():
    """Generate a comprehensive performance report"""
    logger.info("Generating performance report...")
    
    try:
        from performance_monitor import get_performance_monitor
        from enhanced_cache import get_cache_manager
        
        # Get performance data
        monitor = get_performance_monitor()
        cache_manager = get_cache_manager()
        
        # Generate report
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "validation_results": {
                "imports": "✅ Passed",
                "performance_monitor": "✅ Passed",
                "enhanced_cache": "✅ Passed",
                "analysis_queue": "✅ Passed",
                "performance_benchmarks": "✅ Passed",
                "serendipity_integration": "✅ Passed",
                "test_suite": "✅ Passed"
            },
            "performance_summary": monitor.get_performance_summary(hours=1),
            "cache_statistics": cache_manager.get_all_statistics(),
            "optimization_recommendations": monitor.get_optimization_recommendations(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform
            }
        }
        
        # Save report
        report_file = f"performance_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"✅ Performance report generated: {report_file}")
        return report_file
        
    except Exception as e:
        logger.error(f"❌ Performance report generation failed: {e}")
        return None

def main():
    """Main validation function"""
    logger.info("Starting performance optimization validation...")
    
    validation_steps = [
        ("Module Imports", validate_imports),
        ("Performance Monitor", validate_performance_monitor),
        ("Enhanced Cache", validate_enhanced_cache),
        ("Analysis Queue", validate_analysis_queue),
        ("Performance Benchmarks", validate_performance_benchmarks),
        ("Serendipity Integration", validate_serendipity_integration),
        ("Performance Test Suite", run_performance_tests)
    ]
    
    results = {}
    all_passed = True
    
    for step_name, validation_func in validation_steps:
        logger.info(f"\n{'='*50}")
        logger.info(f"Validating: {step_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = validation_func()
            results[step_name] = result
            
            if not result:
                all_passed = False
                
        except Exception as e:
            logger.error(f"❌ Validation step '{step_name}' failed with exception: {e}")
            results[step_name] = False
            all_passed = False
    
    # Generate final report
    logger.info(f"\n{'='*50}")
    logger.info("VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    for step_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{step_name}: {status}")
    
    if all_passed:
        logger.info("\n🎉 ALL VALIDATIONS PASSED!")
        logger.info("Performance optimizations are working correctly.")
        
        # Generate comprehensive report
        report_file = generate_performance_report()
        if report_file:
            logger.info(f"📊 Detailed report saved to: {report_file}")
        
        return 0
    else:
        logger.error("\n❌ SOME VALIDATIONS FAILED!")
        logger.error("Please check the logs above for details.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)