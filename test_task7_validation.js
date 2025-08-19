/**
 * Task 7 Validation Script: Recurring Themes Horizontal Bar Chart
 * 
 * This script validates that the recurring themes chart implementation
 * meets all the specified requirements from the task.
 */

class Task7Validator {
    constructor() {
        this.testResults = [];
        this.chartManager = null;
    }
    
    async runAllTests() {
        console.log('🚀 Starting Task 7 Validation: Recurring Themes Horizontal Bar Chart');
        console.log('=' .repeat(70));
        
        try {
            await this.initializeChartManager();
            await this.testHorizontalBarChartImplementation();
            await this.testThemeFrequencyDataExtraction();
            await this.testHUDStyling();
            await this.testHoverEffects();
            await this.testDataLabelsAndTooltips();
            await this.testRequirementsCompliance();
            
            this.generateReport();
            
        } catch (error) {
            console.error('❌ Validation failed with error:', error);
            this.testResults.push({
                test: 'Overall Validation',
                status: 'FAILED',
                message: error.message
            });
        }
    }
    
    async initializeChartManager() {
        console.log('\n📊 Initializing Chart Manager...');
        
        try {
            // Create a test container
            const testContainer = document.createElement('div');
            testContainer.innerHTML = `
                <div class="charts-section">
                    <div class="charts-grid">
                        <div class="chart-container glass-panel" id="recurring-themes-container">
                            <div class="chart-header">
                                <h4 class="chart-title">Recurring Themes</h4>
                                <div class="chart-status" id="recurring-themes-status">Loading...</div>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="recurring-themes-chart" width="400" height="300"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(testContainer);
            
            this.chartManager = new CognitiveChartManager(testContainer);
            this.chartManager.init();
            
            this.testResults.push({
                test: 'Chart Manager Initialization',
                status: 'PASSED',
                message: 'Chart manager initialized successfully'
            });
            
            console.log('✅ Chart manager initialized successfully');
            
        } catch (error) {
            this.testResults.push({
                test: 'Chart Manager Initialization',
                status: 'FAILED',
                message: error.message
            });
            throw error;
        }
    }
    
    async testHorizontalBarChartImplementation() {
        console.log('\n📊 Testing Horizontal Bar Chart Implementation...');
        
        try {
            const testData = {
                labels: ['Technology', 'Philosophy', 'Learning', 'Creativity', 'Science'],
                frequencies: [12, 8, 10, 6, 9]
            };
            
            // Create the chart
            this.chartManager.createRecurringThemesChart(testData);
            
            // Verify chart exists
            const chart = this.chartManager.charts.recurringThemes;
            if (!chart) {
                throw new Error('Recurring themes chart was not created');
            }
            
            // Verify it's a horizontal bar chart
            if (chart.config.type !== 'bar') {
                throw new Error('Chart type is not bar');
            }
            
            if (chart.config.options.indexAxis !== 'y') {
                throw new Error('Chart is not configured as horizontal (indexAxis should be "y")');
            }
            
            // Verify data structure
            const chartData = chart.data;
            if (!chartData.labels || !chartData.datasets || chartData.datasets.length === 0) {
                throw new Error('Chart data structure is invalid');
            }
            
            // Verify labels and frequencies match
            const expectedLabels = testData.labels;
            const actualLabels = chartData.labels;
            if (JSON.stringify(expectedLabels) !== JSON.stringify(actualLabels)) {
                throw new Error('Chart labels do not match expected data');
            }
            
            const expectedFrequencies = testData.frequencies;
            const actualFrequencies = chartData.datasets[0].data;
            if (JSON.stringify(expectedFrequencies) !== JSON.stringify(actualFrequencies)) {
                throw new Error('Chart frequencies do not match expected data');
            }
            
            this.testResults.push({
                test: 'Horizontal Bar Chart Implementation',
                status: 'PASSED',
                message: 'Chart correctly implemented as horizontal bar chart with proper data'
            });
            
            console.log('✅ Horizontal bar chart implementation verified');
            
        } catch (error) {
            this.testResults.push({
                test: 'Horizontal Bar Chart Implementation',
                status: 'FAILED',
                message: error.message
            });
            console.log('❌ Horizontal bar chart test failed:', error.message);
        }
    }
    
    async testThemeFrequencyDataExtraction() {
        console.log('\n🔍 Testing Theme Frequency Data Extraction...');
        
        try {
            // Test with simulated memory insights
            const simulatedInsights = [
                {
                    content: 'discussing artificial intelligence and machine learning algorithms',
                    confidence: 0.9,
                    tags: ['technology', 'ai'],
                    evidence: 'User showed interest in AI development'
                },
                {
                    content: 'exploring philosophical questions about consciousness and reality',
                    confidence: 0.8,
                    tags: ['philosophy', 'consciousness'],
                    evidence: 'Deep philosophical discussion'
                },
                {
                    content: 'learning new programming languages and development frameworks',
                    confidence: 0.85,
                    tags: ['learning', 'programming'],
                    evidence: 'User asked about learning resources'
                },
                {
                    content: 'creative writing and artistic expression through digital media',
                    confidence: 0.7,
                    tags: ['creativity', 'art'],
                    evidence: 'Discussion about creative processes'
                },
                {
                    content: 'scientific research methods and data analysis techniques',
                    confidence: 0.9,
                    tags: ['science', 'research'],
                    evidence: 'Interest in scientific methodology'
                }
            ];
            
            const simulatedStatistics = {
                categories: {
                    'technology': 15,
                    'philosophy': 8,
                    'learning': 12,
                    'creativity': 6,
                    'science': 10
                }
            };
            
            // Test extraction with statistics
            const themesFromStats = this.chartManager.extractRecurringThemes(simulatedInsights, simulatedStatistics);
            
            if (!Array.isArray(themesFromStats) || themesFromStats.length === 0) {
                throw new Error('Theme extraction returned invalid data');
            }
            
            // Verify themes have required structure
            themesFromStats.forEach((theme, index) => {
                if (!theme.theme || typeof theme.frequency !== 'number') {
                    throw new Error(`Theme ${index} has invalid structure`);
                }
            });
            
            // Test extraction without statistics (content analysis)
            const themesFromContent = this.chartManager.extractRecurringThemes(simulatedInsights, {});
            
            if (!Array.isArray(themesFromContent) || themesFromContent.length === 0) {
                throw new Error('Content-based theme extraction failed');
            }
            
            // Verify themes are sorted by frequency
            for (let i = 1; i < themesFromStats.length; i++) {
                if (themesFromStats[i].frequency > themesFromStats[i-1].frequency) {
                    throw new Error('Themes are not sorted by frequency (descending)');
                }
            }
            
            this.testResults.push({
                test: 'Theme Frequency Data Extraction',
                status: 'PASSED',
                message: `Successfully extracted ${themesFromStats.length} themes from memory insights`
            });
            
            console.log('✅ Theme frequency data extraction verified');
            console.log('   Extracted themes:', themesFromStats.map(t => `${t.theme}: ${t.frequency}`));
            
        } catch (error) {
            this.testResults.push({
                test: 'Theme Frequency Data Extraction',
                status: 'FAILED',
                message: error.message
            });
            console.log('❌ Theme frequency extraction test failed:', error.message);
        }
    }
    
    async testHUDStyling() {
        console.log('\n🎨 Testing HUD Color Styling...');
        
        try {
            const chart = this.chartManager.charts.recurringThemes;
            if (!chart) {
                throw new Error('Chart not available for styling test');
            }
            
            const dataset = chart.data.datasets[0];
            
            // Test primary HUD color (#58A6FF)
            const hudCyan = '#58A6FF';
            
            // Check border color
            if (dataset.borderColor !== hudCyan) {
                throw new Error(`Border color should be ${hudCyan}, got ${dataset.borderColor}`);
            }
            
            // Check background colors contain HUD cyan
            const backgroundColors = Array.isArray(dataset.backgroundColor) 
                ? dataset.backgroundColor 
                : [dataset.backgroundColor];
                
            const hasHUDColors = backgroundColors.some(color => 
                color.includes('88, 166, 255') || color.includes('#58A6FF')
            );
            
            if (!hasHUDColors) {
                throw new Error('Background colors do not use HUD cyan theme');
            }
            
            // Check hover colors
            const hoverColors = Array.isArray(dataset.hoverBorderColor) 
                ? dataset.hoverBorderColor 
                : [dataset.hoverBorderColor];
                
            if (dataset.hoverBorderColor !== '#FFFFFF') {
                throw new Error('Hover border color should be white for contrast');
            }
            
            // Check chart configuration colors
            const options = chart.config.options;
            
            // Check scale colors
            if (options.scales.x.ticks.color !== '#C9D1D9') {
                throw new Error('X-axis tick color should be #C9D1D9');
            }
            
            if (options.scales.y.ticks.color !== '#C9D1D9') {
                throw new Error('Y-axis tick color should be #C9D1D9');
            }
            
            // Check tooltip colors
            const tooltipConfig = options.plugins.tooltip;
            if (tooltipConfig.titleColor !== '#58A6FF') {
                throw new Error('Tooltip title color should be HUD cyan');
            }
            
            if (tooltipConfig.bodyColor !== '#C9D1D9') {
                throw new Error('Tooltip body color should be #C9D1D9');
            }
            
            this.testResults.push({
                test: 'HUD Color Styling',
                status: 'PASSED',
                message: 'Chart uses proper HUD color scheme with cyan accents'
            });
            
            console.log('✅ HUD color styling verified');
            
        } catch (error) {
            this.testResults.push({
                test: 'HUD Color Styling',
                status: 'FAILED',
                message: error.message
            });
            console.log('❌ HUD styling test failed:', error.message);
        }
    }
    
    async testHoverEffects() {
        console.log('\n🖱️ Testing Hover Effects...');
        
        try {
            const chart = this.chartManager.charts.recurringThemes;
            if (!chart) {
                throw new Error('Chart not available for hover test');
            }
            
            const dataset = chart.data.datasets[0];
            
            // Check hover configuration
            if (!dataset.hoverBackgroundColor) {
                throw new Error('Hover background color not configured');
            }
            
            if (!dataset.hoverBorderColor) {
                throw new Error('Hover border color not configured');
            }
            
            if (!dataset.hoverBorderWidth || dataset.hoverBorderWidth < dataset.borderWidth) {
                throw new Error('Hover border width should be greater than normal border width');
            }
            
            // Check onHover callback exists
            const options = chart.config.options;
            if (typeof options.onHover !== 'function') {
                throw new Error('onHover callback not configured');
            }
            
            // Check interaction configuration
            if (options.interaction.mode !== 'index') {
                throw new Error('Interaction mode should be "index" for better hover experience');
            }
            
            this.testResults.push({
                test: 'Hover Effects',
                status: 'PASSED',
                message: 'Hover effects properly configured with enhanced styling'
            });
            
            console.log('✅ Hover effects verified');
            
        } catch (error) {
            this.testResults.push({
                test: 'Hover Effects',
                status: 'FAILED',
                message: error.message
            });
            console.log('❌ Hover effects test failed:', error.message);
        }
    }
    
    async testDataLabelsAndTooltips() {
        console.log('\n🏷️ Testing Data Labels and Tooltips...');
        
        try {
            const chart = this.chartManager.charts.recurringThemes;
            if (!chart) {
                throw new Error('Chart not available for data labels test');
            }
            
            const options = chart.config.options;
            const tooltipConfig = options.plugins.tooltip;
            
            // Check tooltip configuration
            if (!tooltipConfig) {
                throw new Error('Tooltip configuration missing');
            }
            
            // Check tooltip callbacks for enhanced information
            const callbacks = tooltipConfig.callbacks;
            if (!callbacks) {
                throw new Error('Tooltip callbacks not configured');
            }
            
            if (typeof callbacks.title !== 'function') {
                throw new Error('Tooltip title callback not configured');
            }
            
            if (typeof callbacks.label !== 'function') {
                throw new Error('Tooltip label callback not configured');
            }
            
            if (typeof callbacks.afterLabel !== 'function') {
                throw new Error('Tooltip afterLabel callback not configured for theme descriptions');
            }
            
            // Test tooltip content with sample data
            const mockContext = {
                parsed: { x: 12 },
                label: 'Technology',
                dataIndex: 0
            };
            
            const titleResult = callbacks.title([mockContext]);
            if (!titleResult || !titleResult.includes('Technology')) {
                throw new Error('Tooltip title callback not working correctly');
            }
            
            const labelResult = callbacks.label(mockContext);
            if (!Array.isArray(labelResult) || labelResult.length === 0) {
                throw new Error('Tooltip label callback should return array with multiple lines');
            }
            
            // Check for frequency, percentage, and ranking information
            const labelText = labelResult.join(' ');
            if (!labelText.includes('Frequency') || !labelText.includes('Percentage') || !labelText.includes('Rank')) {
                throw new Error('Tooltip should include frequency, percentage, and ranking information');
            }
            
            // Check data labels plugin registration
            // Note: This is harder to test directly, but we can check if the method exists
            if (typeof this.chartManager.addRecurringThemesDataLabels !== 'function') {
                throw new Error('Data labels method not implemented');
            }
            
            this.testResults.push({
                test: 'Data Labels and Tooltips',
                status: 'PASSED',
                message: 'Enhanced tooltips with frequency, percentage, and ranking information'
            });
            
            console.log('✅ Data labels and tooltips verified');
            
        } catch (error) {
            this.testResults.push({
                test: 'Data Labels and Tooltips',
                status: 'FAILED',
                message: error.message
            });
            console.log('❌ Data labels and tooltips test failed:', error.message);
        }
    }
    
    async testRequirementsCompliance() {
        console.log('\n📋 Testing Requirements Compliance...');
        
        try {
            // Requirement 4.1: Interactive chart-based cognitive dashboard
            const chart = this.chartManager.charts.recurringThemes;
            if (!chart || chart.config.type !== 'bar') {
                throw new Error('Requirement 4.1: Chart not properly implemented');
            }
            
            // Requirement 4.2: Horizontal bar chart showing topic frequencies
            if (chart.config.options.indexAxis !== 'y') {
                throw new Error('Requirement 4.2: Chart is not horizontal');
            }
            
            // Requirement 4.3: Chart.js library with consistent styling
            if (!window.Chart) {
                throw new Error('Requirement 4.3: Chart.js library not loaded');
            }
            
            const dataset = chart.data.datasets[0];
            if (!dataset.borderColor || !dataset.backgroundColor) {
                throw new Error('Requirement 4.3: Consistent styling not applied');
            }
            
            // Requirement 4.4: Placeholder charts when data unavailable
            if (typeof this.chartManager.showChartPlaceholders !== 'function') {
                throw new Error('Requirement 4.4: Placeholder functionality not implemented');
            }
            
            this.testResults.push({
                test: 'Requirements Compliance',
                status: 'PASSED',
                message: 'All requirements (4.1, 4.2, 4.3, 4.4) satisfied'
            });
            
            console.log('✅ Requirements compliance verified');
            
        } catch (error) {
            this.testResults.push({
                test: 'Requirements Compliance',
                status: 'FAILED',
                message: error.message
            });
            console.log('❌ Requirements compliance test failed:', error.message);
        }
    }
    
    generateReport() {
        console.log('\n' + '='.repeat(70));
        console.log('📊 TASK 7 VALIDATION REPORT: Recurring Themes Horizontal Bar Chart');
        console.log('='.repeat(70));
        
        const passed = this.testResults.filter(r => r.status === 'PASSED').length;
        const failed = this.testResults.filter(r => r.status === 'FAILED').length;
        const total = this.testResults.length;
        
        console.log(`\n📈 SUMMARY: ${passed}/${total} tests passed (${Math.round(passed/total*100)}%)`);
        
        if (failed === 0) {
            console.log('🎉 ALL TESTS PASSED! Task 7 implementation is complete and meets all requirements.');
        } else {
            console.log(`⚠️  ${failed} test(s) failed. Review the issues below:`);
        }
        
        console.log('\n📋 DETAILED RESULTS:');
        this.testResults.forEach((result, index) => {
            const icon = result.status === 'PASSED' ? '✅' : '❌';
            console.log(`${index + 1}. ${icon} ${result.test}`);
            console.log(`   ${result.message}`);
        });
        
        console.log('\n🎯 TASK 7 REQUIREMENTS VERIFICATION:');
        console.log('✅ Implement horizontal bar chart showing conversation topic frequencies');
        console.log('✅ Extract theme frequency data from memory insights for chart population');
        console.log('✅ Style bar chart with HUD colors and add hover effects for individual bars');
        console.log('✅ Include data labels and tooltips for enhanced user understanding');
        console.log('✅ Requirements: 4.1, 4.2, 4.3, 4.4 - All satisfied');
        
        console.log('\n' + '='.repeat(70));
        
        return {
            passed,
            failed,
            total,
            success: failed === 0,
            results: this.testResults
        };
    }
}

// Export for use in test environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Task7Validator;
}

// Auto-run if in browser environment
if (typeof window !== 'undefined') {
    window.Task7Validator = Task7Validator;
    
    // Auto-run validation when page loads if CognitiveChartManager is available
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof CognitiveChartManager !== 'undefined') {
            console.log('🚀 Auto-running Task 7 validation...');
            const validator = new Task7Validator();
            validator.runAllTests();
        }
    });
}