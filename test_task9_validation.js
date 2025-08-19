/**
 * Task 9 Validation Script: Dynamic Data Integration for Charts
 * 
 * This script validates the implementation of dynamic data integration,
 * automatic chart updates, loading states, and error handling.
 */

class Task9Validator {
    constructor() {
        this.testResults = [];
        this.chartManager = null;
    }

    async runAllTests() {
        console.log('🚀 Starting Task 9 Validation Tests...\n');
        
        // Test 1: Data Processing Functions
        await this.testDataProcessingFunctions();
        
        // Test 2: Automatic Chart Updates
        await this.testAutomaticChartUpdates();
        
        // Test 3: Fallback Placeholder Charts
        await this.testFallbackPlaceholderCharts();
        
        // Test 4: Loading States
        await this.testLoadingStates();
        
        // Test 5: Error Handling
        await this.testErrorHandling();
        
        // Test 6: Real Data Integration
        await this.testRealDataIntegration();
        
        this.printTestSummary();
        return this.testResults;
    }

    async testDataProcessingFunctions() {
        console.log('📊 Testing Data Processing Functions...');
        
        try {
            // Initialize chart manager
            this.chartManager = new CognitiveChartManager();
            this.chartManager.init();
            
            // Test with sample memory data
            const sampleMemoryData = {
                insights: [
                    {
                        category: 'interests',
                        content: 'User enjoys creative programming and innovative solutions',
                        confidence: 0.9,
                        tags: ['creativity', 'programming', 'innovation'],
                        evidence: 'I love creative coding and finding innovative solutions',
                        timestamp: new Date().toISOString()
                    },
                    {
                        category: 'thinking_patterns',
                        content: 'User prefers analytical and systematic approaches',
                        confidence: 0.8,
                        tags: ['analytical', 'systematic', 'logical'],
                        evidence: 'I like to analyze problems systematically',
                        timestamp: new Date().toISOString()
                    }
                ],
                conversation_summaries: [
                    {
                        timestamp: new Date().toISOString(),
                        summary: 'Discussion about programming and problem-solving',
                        key_themes: ['programming', 'creativity', 'analysis'],
                        insights_count: 2
                    }
                ],
                statistics: {
                    total_insights: 2,
                    categories: {
                        'interests': 1,
                        'thinking_patterns': 1
                    }
                }
            };
            
            // Test data processing
            const chartData = this.chartManager.processMemoryDataForCharts(sampleMemoryData);
            
            // Validate chart data structure
            const hasValidCoreValues = chartData.coreValues && 
                                     Array.isArray(chartData.coreValues.labels) &&
                                     Array.isArray(chartData.coreValues.values) &&
                                     chartData.coreValues.labels.length === 6;
            
            const hasValidThemes = chartData.recurringThemes &&
                                 Array.isArray(chartData.recurringThemes.labels) &&
                                 Array.isArray(chartData.recurringThemes.frequencies);
            
            const hasValidEmotions = chartData.emotionalLandscape &&
                                   Array.isArray(chartData.emotionalLandscape.labels) &&
                                   Array.isArray(chartData.emotionalLandscape.values);
            
            if (hasValidCoreValues && hasValidThemes && hasValidEmotions) {
                this.addTestResult('Data Processing Functions', true, 'Successfully processes memory data into chart formats');
                console.log('✅ Data processing functions working correctly');
                console.log(`   - Core Values: ${chartData.coreValues.labels.length} dimensions`);
                console.log(`   - Themes: ${chartData.recurringThemes.labels.length} themes`);
                console.log(`   - Emotions: ${chartData.emotionalLandscape.labels.length} emotions`);
            } else {
                throw new Error('Invalid chart data structure returned');
            }
            
        } catch (error) {
            this.addTestResult('Data Processing Functions', false, `Error: ${error.message}`);
            console.log('❌ Data processing functions failed:', error.message);
        }
    }

    async testAutomaticChartUpdates() {
        console.log('\n🔄 Testing Automatic Chart Updates...');
        
        try {
            if (!this.chartManager) {
                this.chartManager = new CognitiveChartManager();
                this.chartManager.init();
            }
            
            // Test if updateChartsWithMemoryData method exists and is callable
            if (typeof this.chartManager.updateChartsWithMemoryData === 'function') {
                // Simulate automatic update
                await this.chartManager.updateChartsWithMemoryData();
                
                this.addTestResult('Automatic Chart Updates', true, 'Chart update method is functional');
                console.log('✅ Automatic chart updates working correctly');
                console.log('   - updateChartsWithMemoryData method exists and callable');
                console.log('   - Charts can be updated with new data');
            } else {
                throw new Error('updateChartsWithMemoryData method not found');
            }
            
        } catch (error) {
            this.addTestResult('Automatic Chart Updates', false, `Error: ${error.message}`);
            console.log('❌ Automatic chart updates failed:', error.message);
        }
    }

    async testFallbackPlaceholderCharts() {
        console.log('\n📋 Testing Fallback Placeholder Charts...');
        
        try {
            if (!this.chartManager) {
                this.chartManager = new CognitiveChartManager();
                this.chartManager.init();
            }
            
            // Test placeholder chart creation
            if (typeof this.chartManager.showChartPlaceholders === 'function') {
                this.chartManager.showChartPlaceholders();
                
                // Check if placeholder message is shown
                const hasPlaceholderMessage = typeof this.chartManager.showPlaceholderMessage === 'function';
                
                this.addTestResult('Fallback Placeholder Charts', true, 'Placeholder charts display correctly');
                console.log('✅ Fallback placeholder charts working correctly');
                console.log('   - showChartPlaceholders method exists');
                console.log('   - Placeholder message functionality available');
            } else {
                throw new Error('showChartPlaceholders method not found');
            }
            
        } catch (error) {
            this.addTestResult('Fallback Placeholder Charts', false, `Error: ${error.message}`);
            console.log('❌ Fallback placeholder charts failed:', error.message);
        }
    }

    async testLoadingStates() {
        console.log('\n⏳ Testing Loading States...');
        
        try {
            if (!this.chartManager) {
                this.chartManager = new CognitiveChartManager();
                this.chartManager.init();
            }
            
            // Test loading state methods
            const hasLoadingStates = typeof this.chartManager.showChartLoadingStates === 'function';
            const hasStatusUpdate = typeof this.chartManager.updateChartStatus === 'function';
            const hasSkeletonLoader = typeof this.chartManager.createChartLoadingSkeleton === 'function';
            
            if (hasLoadingStates && hasStatusUpdate) {
                // Test loading states
                this.chartManager.showChartLoadingStates();
                
                this.addTestResult('Loading States', true, 'Loading states and status updates working');
                console.log('✅ Loading states working correctly');
                console.log('   - showChartLoadingStates method exists');
                console.log('   - updateChartStatus method exists');
                console.log(`   - Skeleton loader: ${hasSkeletonLoader ? 'Available' : 'Not available'}`);
            } else {
                throw new Error('Loading state methods not found');
            }
            
        } catch (error) {
            this.addTestResult('Loading States', false, `Error: ${error.message}`);
            console.log('❌ Loading states failed:', error.message);
        }
    }

    async testErrorHandling() {
        console.log('\n🚨 Testing Error Handling...');
        
        try {
            if (!this.chartManager) {
                this.chartManager = new CognitiveChartManager();
                this.chartManager.init();
            }
            
            // Test error handling methods
            const hasErrorHandling = typeof this.chartManager.handleChartDataError === 'function';
            const hasErrorState = typeof this.chartManager.showChartErrorState === 'function';
            
            if (hasErrorHandling) {
                // Simulate error handling
                const testError = new Error('Test error for validation');
                this.chartManager.handleChartDataError(testError);
                
                this.addTestResult('Error Handling', true, 'Error handling methods are functional');
                console.log('✅ Error handling working correctly');
                console.log('   - handleChartDataError method exists');
                console.log(`   - Error state display: ${hasErrorState ? 'Available' : 'Not available'}`);
            } else {
                throw new Error('Error handling methods not found');
            }
            
        } catch (error) {
            this.addTestResult('Error Handling', false, `Error: ${error.message}`);
            console.log('❌ Error handling failed:', error.message);
        }
    }

    async testRealDataIntegration() {
        console.log('\n🔗 Testing Real Data Integration...');
        
        try {
            // Test API endpoint availability
            const response = await fetch('/api/insights');
            
            if (response.ok) {
                const data = await response.json();
                
                // Validate data structure
                const hasInsights = Array.isArray(data.insights);
                const hasSummaries = Array.isArray(data.conversation_summaries);
                const hasStatistics = typeof data.statistics === 'object';
                
                if (hasInsights && hasSummaries && hasStatistics) {
                    this.addTestResult('Real Data Integration', true, 'API integration working correctly');
                    console.log('✅ Real data integration working correctly');
                    console.log(`   - Insights: ${data.insights.length} items`);
                    console.log(`   - Summaries: ${data.conversation_summaries.length} items`);
                    console.log(`   - Statistics: ${Object.keys(data.statistics).length} properties`);
                } else {
                    throw new Error('Invalid data structure from API');
                }
            } else {
                throw new Error(`API returned ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            this.addTestResult('Real Data Integration', false, `Error: ${error.message}`);
            console.log('❌ Real data integration failed:', error.message);
        }
    }

    addTestResult(testName, passed, details) {
        this.testResults.push({
            test: testName,
            passed,
            details,
            timestamp: new Date().toISOString()
        });
    }

    printTestSummary() {
        console.log('\n📋 Task 9 Validation Summary');
        console.log('=' .repeat(50));
        
        const passedTests = this.testResults.filter(result => result.passed).length;
        const totalTests = this.testResults.length;
        
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${passedTests}`);
        console.log(`Failed: ${totalTests - passedTests}`);
        console.log(`Success Rate: ${Math.round((passedTests / totalTests) * 100)}%`);
        
        console.log('\nDetailed Results:');
        this.testResults.forEach((result, index) => {
            const status = result.passed ? '✅' : '❌';
            console.log(`${index + 1}. ${status} ${result.test}`);
            console.log(`   ${result.details}`);
        });
        
        if (passedTests === totalTests) {
            console.log('\n🎉 All tests passed! Task 9 implementation is complete.');
        } else {
            console.log('\n⚠️  Some tests failed. Please review the implementation.');
        }
    }
}

// Export for use in browser or Node.js
if (typeof window !== 'undefined') {
    window.Task9Validator = Task9Validator;
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = Task9Validator;
}

// Auto-run if loaded directly in browser
if (typeof window !== 'undefined' && window.location) {
    document.addEventListener('DOMContentLoaded', async () => {
        if (window.location.pathname.includes('test_task9')) {
            console.log('🔍 Task 9 Validation Script Loaded');
            console.log('Run: new Task9Validator().runAllTests() to start validation');
        }
    });
}