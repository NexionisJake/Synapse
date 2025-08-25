#!/usr/bin/env python3
"""
Automated test runner for Synapse Streaming Markdown Rendering
Tests various scenarios and reports any issues found.
"""

import asyncio
import json
import time
import requests
import sys
from typing import Dict, List, Tuple

class MarkdownStreamingTester:
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{status_symbol} {test_name}: {status} - {details}")
    
    def test_health_check(self) -> bool:
        """Test if the application is running and responding"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", "PASS", "Application is running")
                    return True
                else:
                    self.log_test("Health Check", "FAIL", f"Unhealthy status: {data}")
                    return False
            else:
                self.log_test("Health Check", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Connection error: {str(e)}")
            return False
    
    def test_basic_chat_response(self) -> bool:
        """Test basic chat functionality"""
        try:
            payload = {
                "conversation": [
                    {
                        "role": "user",
                        "content": "Please respond with a simple message containing **bold text** and a list with 2 items."
                    }
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and data["response"]:
                    self.log_test("Basic Chat Response", "PASS", f"Got response: {len(data['response'])} chars")
                    return True
                else:
                    self.log_test("Basic Chat Response", "FAIL", "No response content")
                    return False
            else:
                self.log_test("Basic Chat Response", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Basic Chat Response", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_streaming_response(self) -> bool:
        """Test streaming chat functionality"""
        try:
            payload = {
                "conversation": [
                    {
                        "role": "user",
                        "content": "Please provide a structured response with markdown formatting including headers, lists, and bold text."
                    }
                ],
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                chunks_received = 0
                total_content = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data.get('content'):
                                    chunks_received += 1
                                    total_content += data['content']
                                if data.get('done'):
                                    break
                            except json.JSONDecodeError:
                                continue
                
                if chunks_received > 0:
                    self.log_test("Streaming Response", "PASS", f"Received {chunks_received} chunks, {len(total_content)} chars")
                    return True
                else:
                    self.log_test("Streaming Response", "FAIL", "No streaming chunks received")
                    return False
            else:
                self.log_test("Streaming Response", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Streaming Response", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_markdown_prompt_effectiveness(self) -> bool:
        """Test if the AI is generating proper Markdown syntax"""
        try:
            payload = {
                "conversation": [
                    {
                        "role": "user",
                        "content": "Please create a response with exactly these elements: 1) A heading using #, 2) A bulleted list with * symbols, 3) Bold text using **, 4) A blockquote using >"
                    }
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "")
                
                # Check for Markdown elements
                checks = {
                    "heading": content.count("#") > 0,
                    "bullet_list": content.count("*") >= 2,  # At least 2 bullets
                    "bold_text": content.count("**") >= 2,  # At least one bold (open and close)
                    "blockquote": content.count(">") > 0
                }
                
                passed_checks = sum(checks.values())
                total_checks = len(checks)
                
                if passed_checks == total_checks:
                    self.log_test("Markdown Prompt Effectiveness", "PASS", f"All {total_checks} Markdown elements found")
                    return True
                else:
                    missing = [k for k, v in checks.items() if not v]
                    self.log_test("Markdown Prompt Effectiveness", "FAIL", f"Missing: {', '.join(missing)}")
                    return False
            else:
                self.log_test("Markdown Prompt Effectiveness", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Markdown Prompt Effectiveness", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_response_time_performance(self) -> bool:
        """Test response time performance"""
        try:
            start_time = time.time()
            
            payload = {
                "conversation": [
                    {
                        "role": "user",
                        "content": "Please provide a brief response."
                    }
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                if response_time < 10000:  # Less than 10 seconds
                    self.log_test("Response Time Performance", "PASS", f"{response_time:.1f}ms")
                    return True
                else:
                    self.log_test("Response Time Performance", "WARN", f"Slow response: {response_time:.1f}ms")
                    return True  # Still pass but warn
            else:
                self.log_test("Response Time Performance", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Response Time Performance", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        try:
            # Test with malformed request
            response = requests.post(
                f"{self.base_url}/chat",
                json={"invalid": "request"},
                timeout=10
            )
            
            # Should get an error response, not a 500
            if response.status_code in [400, 422]:  # Client error, handled gracefully
                self.log_test("Error Handling", "PASS", f"Graceful error handling: HTTP {response.status_code}")
                return True
            elif response.status_code == 500:
                self.log_test("Error Handling", "FAIL", "Server error on invalid request")
                return False
            else:
                self.log_test("Error Handling", "WARN", f"Unexpected status: {response.status_code}")
                return True
        except Exception as e:
            self.log_test("Error Handling", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests and return summary"""
        print("🧪 Starting Synapse Streaming Markdown Tests...")
        print("=" * 50)
        
        tests = [
            self.test_health_check,
            self.test_basic_chat_response,
            self.test_streaming_response,
            self.test_markdown_prompt_effectiveness,
            self.test_response_time_performance,
            self.test_error_handling
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(1)  # Brief delay between tests
            except Exception as e:
                print(f"Test execution error: {e}")
        
        print("=" * 50)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        # Print detailed results
        if self.test_results:
            print("\n📝 Detailed Results:")
            for result in self.test_results:
                status_color = "🟢" if result["status"] == "PASS" else "🔴" if result["status"] == "FAIL" else "🟡"
                print(f"{status_color} {result['test']}: {result['details']}")
        
        # Identify critical issues
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and r["test"] in ["Health Check", "Basic Chat Response"]]
        if critical_failures:
            print("\n🚨 Critical Issues Found:")
            for failure in critical_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print("\nPlease fix these issues before proceeding.")
            return False
        
        # Check for Markdown-specific issues
        markdown_failures = [r for r in self.test_results if r["status"] == "FAIL" and "Markdown" in r["test"]]
        if markdown_failures:
            print("\n📝 Markdown Rendering Issues:")
            for failure in markdown_failures:
                print(f"   - {failure['test']}: {failure['details']}")
        
        return len(critical_failures) == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Synapse Streaming Markdown Rendering")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Base URL for Synapse application")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    tester = MarkdownStreamingTester(args.url)
    success = tester.run_all_tests()
    
    if args.json:
        print(json.dumps(tester.test_results, indent=2))
    
    sys.exit(0 if success else 1)
