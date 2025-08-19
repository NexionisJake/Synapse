/**
 * Task 6 Validation Test Script
 * 
 * This script validates that all requirements for Task 6 have been implemented:
 * - Core Values radar chart visualization
 * - Memory data processing for chart population
 * - Cyan colors and glassmorphism effects
 * - Interactive hover effects and smooth animations
 */

// Test data simulating memory.json insights
const testMemoryData = {
    insights: [
        {
            category: 'interests',
            content: 'User is interested in AI and machine learning',
            confidence: 0.9,
            tags: ['AI', 'machine_learning'],
            evidence: 'I love learning about artificial intelligence'
        },
        {
            category: 'interests',
            content: 'User enjoys programming in Python',
            confidence: 0.9,
            tags: ['Python', 'programming'],
            evidence: 'I love programming in Python'
        },
        {
            category: 'thinking_patterns',
            content: 'User prefers systematic approach to learning',
            confidence: 0.8,
            tags: ['systematic', 'learning'],
            evidence: 'Would you like to start with the basics?'
        },
        {
            category: 'interests',
            content: 'User shows curiosity about neural networks',
            confidence: 1.0,
            tags: ['neural_networks', 'curiosity'],
            evidence: 'I\'m particularly curious about machine learning and neural networks'
        },
        {
            category: 'thinking_patterns',
            content: 'User demonstrates analytical thinking',
            confidence: 0.85,
            tags: ['analytical', 'logical'],
            evidence: 'User asks detailed questions about technical concepts'
        },
        {
            category: 'interests',
            content: 'User values creative problem solving',
            confidence: 0.75,
            tags: ['creative', 'innovation'],
            evidence: 'User explores innovative approaches to challenges'
        }
    ]
};

// Validation functions
function validateChartCreation() {
    console.log('🧪 Testing Chart Creation...');
    
    if (typeof CognitiveChartManager === 'undefined') {
        console.error('❌ CognitiveChartManager not found');
        return false;
    }
    
    const chartManager = new CognitiveChartManager();
    
    if (typeof chartManager.createCoreValuesChart !== 'function') {
        console.error('❌ createCoreValuesChart method not found');
        return false;
    }
    
    console.log('✅ Chart creation methods available');
    return true;
}

function validateDataProcessing() {
    console.log('🧪 Testing Data Processing...');
    
    const chartManager = new CognitiveChartManager();
    
    if (typeof chartManager.extractCoreValues !== 'function') {
        console.error('❌ extractCoreValues method not found');
        return false;
    }
    
    if (typeof chartManager.processMemoryDataForCharts !== 'function') {
        console.error('❌ processMemoryDataForCharts method not found');
        return false;
    }
    
    // Test data processing
    const processedData = chartManager.processMemoryDataForCharts(testMemoryData);
    
    if (!processedData.coreValues) {
        console.error('❌ Core values data not processed');
        return false;
    }
    
    if (!processedData.coreValues.labels || processedData.coreValues.labels.length !== 6) {
        console.error('❌ Core values labels not properly structured');
        return false;
    }
    
    if (!processedData.coreValues.values || processedData.coreValues.values.length !== 6) {
        console.error('❌ Core values data not properly structured');
        return false;
    }
    
    console.log('✅ Data processing working correctly');
    console.log('📊 Processed values:', processedData.coreValues.values);
    return true;
}

function validateStyling() {
    console.log('🧪 Testing Styling and Theme Integration...');
    
    // Check if CSS custom properties are defined
    const rootStyles = getComputedStyle(document.documentElement);
    
    const hudAccentCyan = rootStyles.getPropertyValue('--hud-accent-cyan').trim();
    if (!hudAccentCyan || hudAccentCyan !== '#58A6FF') {
        console.error('❌ HUD accent cyan color not properly defined');
        return false;
    }
    
    const glassBlur = rootStyles.getPropertyValue('--glass-blur').trim();
    if (!glassBlur || !glassBlur.includes('blur')) {
        console.error('❌ Glassmorphism blur effect not properly defined');
        return false;
    }
    
    // Check if chart-specific styles exist
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) {
        const containerStyles = getComputedStyle(chartContainer);
        const backdropFilter = containerStyles.getPropertyValue('backdrop-filter');
        
        if (!backdropFilter || !backdropFilter.includes('blur')) {
            console.warn('⚠️ Glassmorphism effects may not be fully applied');
        }
    }
    
    console.log('✅ Styling and theme integration validated');
    return true;
}

function validateInteractivity() {
    console.log('🧪 Testing Interactive Features...');
    
    // Create a test chart to validate interactivity
    const canvas = document.createElement('canvas');
    canvas.id = 'test-core-values-chart';
    canvas.width = 300;
    canvas.height = 200;
    document.body.appendChild(canvas);
    
    const chartManager = new CognitiveChartManager();
    const testData = {
        labels: ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
        values: [4.2, 3.8, 4.7, 4.5, 3.9, 4.1]
    };
    
    try {
        // Temporarily override the chart canvas ID for testing
        const originalGetElementById = document.getElementById;
        document.getElementById = function(id) {
            if (id === 'core-values-chart') {
                return canvas;
            }
            return originalGetElementById.call(document, id);
        };
        
        chartManager.createCoreValuesChart(testData);
        
        // Restore original getElementById
        document.getElementById = originalGetElementById;
        
        // Check if chart was created
        if (!chartManager.charts.coreValues) {
            console.error('❌ Chart not created during interactivity test');
            return false;
        }
        
        // Validate chart configuration
        const chart = chartManager.charts.coreValues;
        const config = chart.config;
        
        // Check animation settings
        if (!config.options.animation || config.options.animation.duration < 1000) {
            console.error('❌ Smooth animations not properly configured');
            return false;
        }
        
        // Check hover effects
        if (!config.options.onHover) {
            console.error('❌ Hover effects not configured');
            return false;
        }
        
        // Check tooltip configuration
        if (!config.options.plugins.tooltip || !config.options.plugins.tooltip.callbacks) {
            console.error('❌ Interactive tooltips not properly configured');
            return false;
        }
        
        console.log('✅ Interactive features validated');
        
        // Cleanup
        chart.destroy();
        document.body.removeChild(canvas);
        
        return true;
        
    } catch (error) {
        console.error('❌ Error during interactivity test:', error);
        return false;
    }
}

function validateRequirements() {
    console.log('🎯 Validating Task 6 Requirements...');
    console.log('=====================================');
    
    const results = {
        chartCreation: validateChartCreation(),
        dataProcessing: validateDataProcessing(),
        styling: validateStyling(),
        interactivity: validateInteractivity()
    };
    
    console.log('=====================================');
    console.log('📋 Task 6 Validation Results:');
    console.log('=====================================');
    
    Object.entries(results).forEach(([test, passed]) => {
        console.log(`${passed ? '✅' : '❌'} ${test}: ${passed ? 'PASSED' : 'FAILED'}`);
    });
    
    const allPassed = Object.values(results).every(result => result);
    
    console.log('=====================================');
    console.log(`🎯 Overall Result: ${allPassed ? '✅ ALL REQUIREMENTS MET' : '❌ SOME REQUIREMENTS FAILED'}`);
    console.log('=====================================');
    
    if (allPassed) {
        console.log('🎉 Task 6 implementation is complete and meets all requirements!');
        console.log('');
        console.log('✅ Core Values radar chart displaying personality dimensions');
        console.log('✅ Memory.json data processing for chart population');
        console.log('✅ Cyan colors and glassmorphism effects matching HUD theme');
        console.log('✅ Interactive hover effects and smooth animations');
    }
    
    return allPassed;
}

// Export for use in browser console or test runner
if (typeof window !== 'undefined') {
    window.validateTask6 = validateRequirements;
    window.testMemoryData = testMemoryData;
}

// Auto-run validation if this script is loaded directly
if (typeof document !== 'undefined' && document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(validateRequirements, 1000); // Wait for other scripts to load
    });
} else if (typeof document !== 'undefined') {
    setTimeout(validateRequirements, 1000);
}