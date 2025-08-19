/**
 * Validation script for the comprehensive error handling system
 * Tests both StreamingErrorHandler and ChartErrorHandler functionality
 */

// Test configuration
const TEST_CONFIG = {
    timeout: 5000, // 5 seconds timeout for tests
    verbose: true
};

// Test results tracking
let testResults = {
    passed: 0,
    failed: 0,
    total: 0,
    details: []
};

/**
 * Main validation function
 */
async function validateErrorHandlingSystem() {
    console.log('🧪 Starting Error Handling System Validation...\n');
    
    // Test 1: Check if error handlers are properly initialized
    await testErrorHandlerInitialization();
    
    // Test 2: Test streaming error categorization
    await testStreamingErrorCategorization();
    
    // Test 3: Test chart error categorization
    await testChartErrorCategorization();
    
    // Test 4: Test error logging functionality
    await testErrorLogging();
    
    // Test 5: Test error recovery mechanisms
    await testErrorRecovery();
    
    // Test 6: Test error UI generation
    await testErrorUIGeneration();
    
    // Test 7: Test error statistics
    await testErrorStatistics();
    
    // Print final results
    printTestResults();
}

/**
 * Test error handler initialization
 */
async function testErrorHandlerInitialization() {
    const testName = 'Error Handler Initialization';
    console.log(`Testing: ${testName}`);
    
    try {
        // Check if global error handlers exist
        const streamingHandlerExists = typeof window.streamingErrorHandler !== 'undefined';
        const chartHandlerExists = typeof window.chartErrorHandler !== 'undefined';
        
        if (streamingHandlerExists && chartHandlerExists) {
            // Check if handlers have required methods
            const streamingMethods = [
                'handleStreamingError',
                'categorizeError',
                'retryStreaming',
                'fallbackToStandard',
                'logError',
                'getErrorStats',
                'reset'
            ];
            
            const chartMethods = [
                'handleChartError',
                'categorizeChartError',
                'retryChart',
                'refreshAllCharts',
                'logError',
                'getErrorStats',
                'reset'
            ];
            
            const streamingMethodsExist = streamingMethods.every(method => 
                typeof window.streamingErrorHandler[method] === 'function'
            );
            
            const chartMethodsExist = chartMethods.every(method => 
                typeof window.chartErrorHandler[method] === 'function'
            );
            
            if (streamingMethodsExist && chartMethodsExist) {
                passTest(testName, 'All error handlers initialized with required methods');
            } else {
                failTest(testName, 'Error handlers missing required methods');
            }
        } else {
            failTest(testName, 'Error handlers not found in global scope');
        }
    } catch (error) {
        failTest(testName, `Initialization test failed: ${error.message}`);
    }
}

/**
 * Test streaming error categorization
 */
async function testStreamingErrorCategorization() {
    const testName = 'Streaming Error Categorization';
    console.log(`Testing: ${testName}`);
    
    try {
        const handler = window.streamingErrorHandler;
        if (!handler) {
            failTest(testName, 'Streaming error handler not available');
            return;
        }
        
        // Test different error types
        const testCases = [
            { error: new Error('timeout'), name: 'AbortError', expected: 'timeout' },
            { error: new Error('fetch failed'), name: 'TypeError', expected: 'network' },
            { error: new Error('AI service unavailable'), name: 'Error', expected: 'ai_service' },
            { error: new Error('validation failed'), name: 'Error', expected: 'validation' },
            { error: new Error('rate limit exceeded'), name: 'Error', expected: 'rate_limit' },
            { error: new Error('unknown issue'), name: 'Error', expected: 'unknown' }
        ];
        
        let passed = 0;
        for (const testCase of testCases) {
            testCase.error.name = testCase.name;
            const category = handler.categorizeError(testCase.error);
            
            if (category === testCase.expected) {
                passed++;
                if (TEST_CONFIG.verbose) {
                    console.log(`  ✅ ${testCase.error.message} -> ${category}`);
                }
            } else {
                if (TEST_CONFIG.verbose) {
                    console.log(`  ❌ ${testCase.error.message} -> ${category} (expected ${testCase.expected})`);
                }
            }
        }
        
        if (passed === testCases.length) {
            passTest(testName, `All ${testCases.length} error types categorized correctly`);
        } else {
            failTest(testName, `${passed}/${testCases.length} error types categorized correctly`);
        }
    } catch (error) {
        failTest(testName, `Categorization test failed: ${error.message}`);
    }
}

/**
 * Test chart error categorization
 */
async function testChartErrorCategorization() {
    const testName = 'Chart Error Categorization';
    console.log(`Testing: ${testName}`);
    
    try {
        const handler = window.chartErrorHandler;
        if (!handler) {
            failTest(testName, 'Chart error handler not available');
            return;
        }
        
        // Test different chart error types
        const testCases = [
            { error: new Error('Canvas is already in use'), expected: 'canvas_error' },
            { error: new Error('Invalid data format'), expected: 'data_error' },
            { error: new Error('fetch failed'), expected: 'network_error' },
            { error: new Error('Chart.js error'), expected: 'chart_library_error' },
            { error: new Error('Memory allocation failed'), expected: 'memory_error' },
            { error: new Error('unknown chart issue'), expected: 'unknown_error' }
        ];
        
        let passed = 0;
        for (const testCase of testCases) {
            const category = handler.categorizeChartError(testCase.error);
            
            if (category === testCase.expected) {
                passed++;
                if (TEST_CONFIG.verbose) {
                    console.log(`  ✅ ${testCase.error.message} -> ${category}`);
                }
            } else {
                if (TEST_CONFIG.verbose) {
                    console.log(`  ❌ ${testCase.error.message} -> ${category} (expected ${testCase.expected})`);
                }
            }
        }
        
        if (passed === testCases.length) {
            passTest(testName, `All ${testCases.length} chart error types categorized correctly`);
        } else {
            failTest(testName, `${passed}/${testCases.length} chart error types categorized correctly`);
        }
    } catch (error) {
        failTest(testName, `Chart categorization test failed: ${error.message}`);
    }
}

/**
 * Test error logging functionality
 */
async function testErrorLogging() {
    const testName = 'Error Logging';
    console.log(`Testing: ${testName}`);
    
    try {
        const streamingHandler = window.streamingErrorHandler;
        const chartHandler = window.chartErrorHandler;
        
        if (!streamingHandler || !chartHandler) {
            failTest(testName, 'Error handlers not available');
            return;
        }
        
        // Clear existing logs
        streamingHandler.reset();
        chartHandler.reset();
        
        // Test streaming error logging
        const streamingError = new Error('Test streaming error');
        streamingHandler.logError('streaming', streamingError, { test: true });
        
        // Test chart error logging
        const chartError = new Error('Test chart error');
        chartHandler.logError('test-chart', 'bar', chartError, { test: true });
        
        // Check if errors were logged
        const streamingStats = streamingHandler.getErrorStats();
        const chartStats = chartHandler.getErrorStats();
        
        if (streamingStats.totalErrors === 1 && chartStats.totalErrors === 1) {
            passTest(testName, 'Error logging working correctly');
        } else {
            failTest(testName, `Expected 1 error each, got streaming: ${streamingStats.totalErrors}, chart: ${chartStats.totalErrors}`);
        }
    } catch (error) {
        failTest(testName, `Error logging test failed: ${error.message}`);
    }
}

/**
 * Test error recovery mechanisms
 */
async function testErrorRecovery() {
    const testName = 'Error Recovery Mechanisms';
    console.log(`Testing: ${testName}`);
    
    try {
        const handler = window.streamingErrorHandler;
        if (!handler) {
            failTest(testName, 'Streaming error handler not available');
            return;
        }
        
        // Test retry mechanism
        const originalRetryAttempts = handler.retryAttempts;
        handler.retryAttempts = 0;
        
        // Check if retry is available
        const canRetry = handler.retryAttempts < handler.maxRetries;
        
        if (canRetry) {
            passTest(testName, 'Error recovery mechanisms available');
        } else {
            failTest(testName, 'Error recovery mechanisms not working');
        }
        
        // Restore original state
        handler.retryAttempts = originalRetryAttempts;
    } catch (error) {
        failTest(testName, `Error recovery test failed: ${error.message}`);
    }
}

/**
 * Test error UI generation
 */
async function testErrorUIGeneration() {
    const testName = 'Error UI Generation';
    console.log(`Testing: ${testName}`);
    
    try {
        const handler = window.streamingErrorHandler;
        if (!handler) {
            failTest(testName, 'Streaming error handler not available');
            return;
        }
        
        // Test error configuration generation
        const errorTypes = ['timeout', 'network', 'ai_service', 'validation', 'unknown'];
        let configsGenerated = 0;
        
        for (const errorType of errorTypes) {
            const config = handler.getErrorConfig(errorType, new Error('test'));
            if (config && config.icon && config.title && config.message) {
                configsGenerated++;
            }
        }
        
        if (configsGenerated === errorTypes.length) {
            passTest(testName, 'Error UI configurations generated correctly');
        } else {
            failTest(testName, `${configsGenerated}/${errorTypes.length} error UI configurations generated`);
        }
    } catch (error) {
        failTest(testName, `Error UI generation test failed: ${error.message}`);
    }
}

/**
 * Test error statistics
 */
async function testErrorStatistics() {
    const testName = 'Error Statistics';
    console.log(`Testing: ${testName}`);
    
    try {
        const streamingHandler = window.streamingErrorHandler;
        const chartHandler = window.chartErrorHandler;
        
        if (!streamingHandler || !chartHandler) {
            failTest(testName, 'Error handlers not available');
            return;
        }
        
        // Get statistics
        const streamingStats = streamingHandler.getErrorStats();
        const chartStats = chartHandler.getErrorStats();
        
        // Check if statistics have required properties
        const streamingStatsValid = streamingStats && 
            typeof streamingStats.totalErrors === 'number' &&
            typeof streamingStats.errorsByType === 'object' &&
            Array.isArray(streamingStats.recentErrors);
        
        const chartStatsValid = chartStats && 
            typeof chartStats.totalErrors === 'number' &&
            typeof chartStats.errorsByChart === 'object' &&
            typeof chartStats.errorsByType === 'object' &&
            Array.isArray(chartStats.recentErrors);
        
        if (streamingStatsValid && chartStatsValid) {
            passTest(testName, 'Error statistics working correctly');
        } else {
            failTest(testName, 'Error statistics not properly structured');
        }
    } catch (error) {
        failTest(testName, `Error statistics test failed: ${error.message}`);
    }
}

/**
 * Helper function to record passed test
 */
function passTest(testName, message) {
    testResults.passed++;
    testResults.total++;
    testResults.details.push({ test: testName, status: 'PASS', message });
    console.log(`✅ PASS: ${testName} - ${message}\n`);
}

/**
 * Helper function to record failed test
 */
function failTest(testName, message) {
    testResults.failed++;
    testResults.total++;
    testResults.details.push({ test: testName, status: 'FAIL', message });
    console.log(`❌ FAIL: ${testName} - ${message}\n`);
}

/**
 * Print final test results
 */
function printTestResults() {
    console.log('📊 ERROR HANDLING SYSTEM VALIDATION RESULTS');
    console.log('='.repeat(50));
    console.log(`Total Tests: ${testResults.total}`);
    console.log(`Passed: ${testResults.passed}`);
    console.log(`Failed: ${testResults.failed}`);
    console.log(`Success Rate: ${Math.round((testResults.passed / testResults.total) * 100)}%`);
    console.log('='.repeat(50));
    
    if (testResults.failed > 0) {
        console.log('\n❌ FAILED TESTS:');
        testResults.details
            .filter(result => result.status === 'FAIL')
            .forEach(result => {
                console.log(`  • ${result.test}: ${result.message}`);
            });
    }
    
    if (testResults.passed === testResults.total) {
        console.log('\n🎉 ALL TESTS PASSED! Error handling system is working correctly.');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the error handling implementation.');
    }
}

// Export for use in browser or Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { validateErrorHandlingSystem };
} else if (typeof window !== 'undefined') {
    window.validateErrorHandlingSystem = validateErrorHandlingSystem;
}

// Auto-run validation if loaded in browser
if (typeof window !== 'undefined' && window.document) {
    document.addEventListener('DOMContentLoaded', function() {
        // Wait for error handlers to initialize
        setTimeout(() => {
            validateErrorHandlingSystem();
        }, 2000);
    });
}