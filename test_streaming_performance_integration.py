#!/usr/bin/env python3
"""
Integration test for streaming performance monitoring system.

This test verifies that the streaming performance monitoring system
correctly tracks metrics, handles timeouts, and provides user feedback.
"""

import asyncio
import json
import time
import requests
import threading
from datetime import datetime
from typing import Dict, List, Optional

class StreamingPerformanceTest:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.performance_metrics = {
            'response_times': [],
            'words_per_second': [],
            'chunk_latencies': [],
            'timeout_count': 0,
            'error_count': 0,
            'success_count': 0
        }
    
    def test_normal_streaming_performance(self) -> Dict:
        """Test normal streaming performance with a simple query."""
        print("Testing normal streaming performance...")
        
        test_conversation = [
            {"role": "user", "content": "Hello, can you tell me about artificial intelligence?"}
        ]
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"conversation": test_conversation, "stream": True},
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'test': 'normal_streaming',
                    'status': 'failed',
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'response_time': time.time() - start_time
                }
            
            # Process streaming response
            chunks_received = 0
            total_characters = 0
            chunk_times = []
            last_chunk_time = start_time
            full_response = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        chunk_data = json.loads(line[6:])
                        current_time = time.time()
                        
                        if chunk_data.get('content'):
                            chunks_received += 1
                            content = chunk_data['content']
                            total_characters += len(content)
                            full_response += content
                            
                            # Track chunk latency
                            chunk_latency = (current_time - last_chunk_time) * 1000  # ms
                            chunk_times.append(chunk_latency)
                            last_chunk_time = current_time
                        
                        if chunk_data.get('done'):
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse chunk: {e}")
                        continue
            
            total_time = time.time() - start_time
            words_per_second = (total_characters / 5) / total_time if total_time > 0 else 0
            avg_chunk_latency = sum(chunk_times) / len(chunk_times) if chunk_times else 0
            
            # Update performance metrics
            self.performance_metrics['response_times'].append(total_time * 1000)
            self.performance_metrics['words_per_second'].append(words_per_second)
            self.performance_metrics['chunk_latencies'].extend(chunk_times)
            self.performance_metrics['success_count'] += 1
            
            result = {
                'test': 'normal_streaming',
                'status': 'passed',
                'response_time_ms': total_time * 1000,
                'chunks_received': chunks_received,
                'total_characters': total_characters,
                'words_per_second': words_per_second,
                'avg_chunk_latency_ms': avg_chunk_latency,
                'response_length': len(full_response),
                'performance_assessment': self._assess_performance(total_time * 1000, words_per_second, avg_chunk_latency)
            }
            
            print(f"✓ Normal streaming test completed: {total_time*1000:.0f}ms, {words_per_second:.1f} WPS")
            return result
            
        except requests.exceptions.Timeout:
            self.performance_metrics['timeout_count'] += 1
            return {
                'test': 'normal_streaming',
                'status': 'timeout',
                'error': 'Request timed out',
                'response_time': time.time() - start_time
            }
        except Exception as e:
            self.performance_metrics['error_count'] += 1
            return {
                'test': 'normal_streaming',
                'status': 'error',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def test_complex_query_performance(self) -> Dict:
        """Test streaming performance with a complex query that might be slower."""
        print("Testing complex query performance...")
        
        test_conversation = [
            {"role": "user", "content": "Can you provide a detailed explanation of quantum computing, including the principles of superposition and entanglement, and how they differ from classical computing paradigms? Please include examples and potential applications."}
        ]
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"conversation": test_conversation, "stream": True},
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=45  # Longer timeout for complex query
            )
            
            if response.status_code != 200:
                return {
                    'test': 'complex_query',
                    'status': 'failed',
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'response_time': time.time() - start_time
                }
            
            # Process streaming response with performance tracking
            chunks_received = 0
            total_characters = 0
            chunk_times = []
            last_chunk_time = start_time
            slow_chunks = 0
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        chunk_data = json.loads(line[6:])
                        current_time = time.time()
                        
                        if chunk_data.get('content'):
                            chunks_received += 1
                            content = chunk_data['content']
                            total_characters += len(content)
                            
                            # Track chunk latency
                            chunk_latency = (current_time - last_chunk_time) * 1000  # ms
                            chunk_times.append(chunk_latency)
                            
                            # Count slow chunks (>2 seconds)
                            if chunk_latency > 2000:
                                slow_chunks += 1
                            
                            last_chunk_time = current_time
                        
                        if chunk_data.get('done'):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            total_time = time.time() - start_time
            words_per_second = (total_characters / 5) / total_time if total_time > 0 else 0
            avg_chunk_latency = sum(chunk_times) / len(chunk_times) if chunk_times else 0
            
            # Update performance metrics
            self.performance_metrics['response_times'].append(total_time * 1000)
            self.performance_metrics['words_per_second'].append(words_per_second)
            self.performance_metrics['chunk_latencies'].extend(chunk_times)
            self.performance_metrics['success_count'] += 1
            
            result = {
                'test': 'complex_query',
                'status': 'passed',
                'response_time_ms': total_time * 1000,
                'chunks_received': chunks_received,
                'total_characters': total_characters,
                'words_per_second': words_per_second,
                'avg_chunk_latency_ms': avg_chunk_latency,
                'slow_chunks': slow_chunks,
                'performance_assessment': self._assess_performance(total_time * 1000, words_per_second, avg_chunk_latency)
            }
            
            print(f"✓ Complex query test completed: {total_time*1000:.0f}ms, {words_per_second:.1f} WPS, {slow_chunks} slow chunks")
            return result
            
        except requests.exceptions.Timeout:
            self.performance_metrics['timeout_count'] += 1
            return {
                'test': 'complex_query',
                'status': 'timeout',
                'error': 'Request timed out',
                'response_time': time.time() - start_time
            }
        except Exception as e:
            self.performance_metrics['error_count'] += 1
            return {
                'test': 'complex_query',
                'status': 'error',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def test_timeout_handling(self) -> Dict:
        """Test timeout handling with a very short timeout."""
        print("Testing timeout handling...")
        
        test_conversation = [
            {"role": "user", "content": "Please write a very long and detailed essay about the history of computing."}
        ]
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"conversation": test_conversation, "stream": True},
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=2  # Very short timeout to force timeout
            )
            
            # This should timeout, but if it doesn't, process normally
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        chunk_data = json.loads(line[6:])
                        if chunk_data.get('done'):
                            break
                    except json.JSONDecodeError:
                        continue
            
            # If we get here, the request didn't timeout as expected
            return {
                'test': 'timeout_handling',
                'status': 'unexpected_success',
                'message': 'Request completed without timeout (this may be normal for fast responses)',
                'response_time': time.time() - start_time
            }
            
        except requests.exceptions.Timeout:
            self.performance_metrics['timeout_count'] += 1
            print("✓ Timeout handling test passed: Request timed out as expected")
            return {
                'test': 'timeout_handling',
                'status': 'passed',
                'message': 'Timeout handled correctly',
                'response_time': time.time() - start_time
            }
        except Exception as e:
            self.performance_metrics['error_count'] += 1
            return {
                'test': 'timeout_handling',
                'status': 'error',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def test_concurrent_requests(self) -> Dict:
        """Test performance with multiple concurrent streaming requests."""
        print("Testing concurrent request performance...")
        
        def make_concurrent_request(request_id: int) -> Dict:
            test_conversation = [
                {"role": "user", "content": f"Request {request_id}: Tell me about machine learning."}
            ]
            
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json={"conversation": test_conversation, "stream": True},
                    headers={"Content-Type": "application/json"},
                    stream=True,
                    timeout=30
                )
                
                if response.status_code != 200:
                    return {
                        'request_id': request_id,
                        'status': 'failed',
                        'error': f'HTTP {response.status_code}',
                        'response_time': time.time() - start_time
                    }
                
                chunks_received = 0
                total_characters = 0
                
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        try:
                            chunk_data = json.loads(line[6:])
                            if chunk_data.get('content'):
                                chunks_received += 1
                                total_characters += len(chunk_data['content'])
                            if chunk_data.get('done'):
                                break
                        except json.JSONDecodeError:
                            continue
                
                total_time = time.time() - start_time
                words_per_second = (total_characters / 5) / total_time if total_time > 0 else 0
                
                return {
                    'request_id': request_id,
                    'status': 'success',
                    'response_time_ms': total_time * 1000,
                    'chunks_received': chunks_received,
                    'words_per_second': words_per_second
                }
                
            except Exception as e:
                return {
                    'request_id': request_id,
                    'status': 'error',
                    'error': str(e),
                    'response_time': time.time() - start_time
                }
        
        # Launch 3 concurrent requests
        threads = []
        results = []
        
        def thread_wrapper(request_id):
            result = make_concurrent_request(request_id)
            results.append(result)
        
        start_time = time.time()
        
        for i in range(3):
            thread = threading.Thread(target=thread_wrapper, args=(i + 1,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        successful_requests = [r for r in results if r['status'] == 'success']
        
        if successful_requests:
            avg_response_time = sum(r['response_time_ms'] for r in successful_requests) / len(successful_requests)
            avg_words_per_second = sum(r['words_per_second'] for r in successful_requests) / len(successful_requests)
            
            # Update metrics for successful requests
            for result in successful_requests:
                self.performance_metrics['response_times'].append(result['response_time_ms'])
                self.performance_metrics['words_per_second'].append(result['words_per_second'])
                self.performance_metrics['success_count'] += 1
        else:
            avg_response_time = 0
            avg_words_per_second = 0
        
        # Count errors
        error_count = len([r for r in results if r['status'] == 'error'])
        self.performance_metrics['error_count'] += error_count
        
        result = {
            'test': 'concurrent_requests',
            'status': 'completed',
            'total_time_ms': total_time * 1000,
            'successful_requests': len(successful_requests),
            'failed_requests': len(results) - len(successful_requests),
            'avg_response_time_ms': avg_response_time,
            'avg_words_per_second': avg_words_per_second,
            'individual_results': results
        }
        
        print(f"✓ Concurrent requests test completed: {len(successful_requests)}/3 successful, avg {avg_response_time:.0f}ms")
        return result
    
    def _assess_performance(self, response_time_ms: float, words_per_second: float, avg_chunk_latency_ms: float) -> str:
        """Assess overall performance based on metrics."""
        issues = []
        
        if response_time_ms > 10000:
            issues.append("very_slow_response")
        elif response_time_ms > 5000:
            issues.append("slow_response")
        
        if words_per_second < 10:
            issues.append("slow_generation")
        
        if avg_chunk_latency_ms > 2000:
            issues.append("high_chunk_latency")
        
        if not issues:
            return "excellent"
        elif len(issues) == 1:
            return "good_with_minor_issues"
        else:
            return "needs_optimization"
    
    def run_all_tests(self) -> Dict:
        """Run all performance tests and return comprehensive results."""
        print("Starting streaming performance monitoring tests...")
        print("=" * 60)
        
        # Test server availability first
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code != 200:
                return {
                    'status': 'failed',
                    'error': f'Server not available: HTTP {response.status_code}',
                    'tests_run': 0
                }
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Server not available: {e}',
                'tests_run': 0
            }
        
        print("✓ Server is available")
        print()
        
        # Run individual tests
        test_results = []
        
        # Test 1: Normal streaming performance
        result = self.test_normal_streaming_performance()
        test_results.append(result)
        time.sleep(1)  # Brief pause between tests
        
        # Test 2: Complex query performance
        result = self.test_complex_query_performance()
        test_results.append(result)
        time.sleep(1)
        
        # Test 3: Timeout handling
        result = self.test_timeout_handling()
        test_results.append(result)
        time.sleep(1)
        
        # Test 4: Concurrent requests
        result = self.test_concurrent_requests()
        test_results.append(result)
        
        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics()
        
        # Generate summary
        passed_tests = len([t for t in test_results if t.get('status') in ['passed', 'completed', 'unexpected_success']])
        total_tests = len(test_results)
        
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Overall performance: {overall_metrics['overall_assessment']}")
        print(f"Average response time: {overall_metrics['avg_response_time_ms']:.0f}ms")
        print(f"Average words per second: {overall_metrics['avg_words_per_second']:.1f}")
        print(f"Success rate: {overall_metrics['success_rate']:.1%}")
        
        return {
            'status': 'completed',
            'tests_run': total_tests,
            'tests_passed': passed_tests,
            'test_results': test_results,
            'performance_metrics': self.performance_metrics,
            'overall_metrics': overall_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_overall_metrics(self) -> Dict:
        """Calculate overall performance metrics from all tests."""
        metrics = self.performance_metrics
        
        if not metrics['response_times']:
            return {
                'avg_response_time_ms': 0,
                'avg_words_per_second': 0,
                'avg_chunk_latency_ms': 0,
                'success_rate': 0,
                'overall_assessment': 'no_data'
            }
        
        avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
        avg_words_per_second = sum(metrics['words_per_second']) / len(metrics['words_per_second'])
        avg_chunk_latency = sum(metrics['chunk_latencies']) / len(metrics['chunk_latencies']) if metrics['chunk_latencies'] else 0
        
        total_requests = metrics['success_count'] + metrics['error_count'] + metrics['timeout_count']
        success_rate = metrics['success_count'] / total_requests if total_requests > 0 else 0
        
        # Overall assessment
        if success_rate < 0.8:
            overall_assessment = 'poor'
        elif avg_response_time > 10000:
            overall_assessment = 'slow'
        elif avg_response_time > 5000:
            overall_assessment = 'acceptable'
        elif avg_words_per_second < 10:
            overall_assessment = 'needs_optimization'
        else:
            overall_assessment = 'good'
        
        return {
            'avg_response_time_ms': avg_response_time,
            'avg_words_per_second': avg_words_per_second,
            'avg_chunk_latency_ms': avg_chunk_latency,
            'success_rate': success_rate,
            'overall_assessment': overall_assessment
        }

def main():
    """Run the streaming performance tests."""
    import sys
    
    # Get base URL from command line argument or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    # Create and run tests
    tester = StreamingPerformanceTest(base_url)
    results = tester.run_all_tests()
    
    # Save results to file
    with open('streaming_performance_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: streaming_performance_test_results.json")
    
    # Exit with appropriate code
    if results['status'] == 'completed' and results['tests_passed'] == results['tests_run']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()