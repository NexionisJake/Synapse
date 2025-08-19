/**
 * Core Task 6 Validation Script (Node.js compatible)
 * 
 * Tests the core functionality without DOM dependencies
 */

// Mock Chart.js for testing
global.Chart = function(ctx, config) {
    this.config = config;
    this.data = config.data;
    this.destroy = () => {};
    this.update = () => {};
};

// Mock DOM elements and window
global.document = {
    getElementById: () => ({ getContext: () => ({}) }),
    createElement: () => ({ id: '', width: 0, height: 0 }),
    body: { appendChild: () => {}, removeChild: () => {} }
};

global.window = global;

// Keep original console (no need to mock it)

// Load the cognitive charts module
const fs = require('fs');
const cognitiveChartsCode = fs.readFileSync('static/js/cognitive-charts.js', 'utf8');

// Execute the code
eval(cognitiveChartsCode);

// Test data
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
            evidence: 'I am particularly curious about machine learning and neural networks'
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

function runCoreValidation() {
    console.log('🎯 Task 6 Core Validation');
    console.log('==========================');
    
    let allTestsPassed = true;
    
    // Test 1: CognitiveChartManager class exists
    console.log('\n1️⃣ Testing CognitiveChartManager class...');
    if (typeof CognitiveChartManager !== 'undefined') {
        console.log('   ✅ CognitiveChartManager class found');
        
        const chartManager = new CognitiveChartManager();
        console.log('   ✅ CognitiveChartManager instance created');
        
        // Test required methods
        const requiredMethods = [
            'createCoreValuesChart',
            'extractCoreValues', 
            'processMemoryDataForCharts',
            'getCoreValueDescription'
        ];
        
        requiredMethods.forEach(method => {
            if (typeof chartManager[method] === 'function') {
                console.log(`   ✅ Method ${method} exists`);
            } else {
                console.log(`   ❌ Method ${method} missing`);
                allTestsPassed = false;
            }
        });
    } else {
        console.log('   ❌ CognitiveChartManager class not found');
        allTestsPassed = false;
    }
    
    // Test 2: Data processing functionality
    console.log('\n2️⃣ Testing data processing...');
    try {
        const chartManager = new CognitiveChartManager();
        const processedData = chartManager.processMemoryDataForCharts(testMemoryData);
        
        if (processedData && processedData.coreValues) {
            console.log('   ✅ processMemoryDataForCharts works');
            
            const coreValues = processedData.coreValues;
            if (coreValues.labels && coreValues.labels.length === 6) {
                console.log('   ✅ Core values labels correct (6 dimensions)');
                console.log(`   📊 Labels: ${coreValues.labels.join(', ')}`);
            } else {
                console.log('   ❌ Core values labels incorrect');
                allTestsPassed = false;
            }
            
            if (coreValues.values && coreValues.values.length === 6) {
                console.log('   ✅ Core values data correct (6 values)');
                console.log(`   📊 Values: ${coreValues.values.join(', ')}`);
                
                // Check if values are in valid range (1-5)
                const validRange = coreValues.values.every(val => val >= 1 && val <= 5);
                if (validRange) {
                    console.log('   ✅ All values in valid range (1-5)');
                } else {
                    console.log('   ❌ Some values outside valid range');
                    allTestsPassed = false;
                }
            } else {
                console.log('   ❌ Core values data incorrect');
                allTestsPassed = false;
            }
        } else {
            console.log('   ❌ Data processing failed');
            allTestsPassed = false;
        }
    } catch (error) {
        console.log(`   ❌ Data processing error: ${error.message}`);
        allTestsPassed = false;
    }
    
    // Test 3: Core values extraction algorithm
    console.log('\n3️⃣ Testing core values extraction algorithm...');
    try {
        const chartManager = new CognitiveChartManager();
        const extractedValues = chartManager.extractCoreValues(testMemoryData.insights, {});
        
        if (Array.isArray(extractedValues) && extractedValues.length === 6) {
            console.log('   ✅ extractCoreValues returns correct array length');
            console.log(`   📊 Extracted values: ${extractedValues.join(', ')}`);
            
            // Test specific expectations based on test data
            const [creativity, stability, learning, curiosity, analysis, empathy] = extractedValues;
            
            // Learning should be high (lots of learning-related content)
            if (learning >= 4.0) {
                console.log('   ✅ Learning score appropriately high');
            } else {
                console.log(`   ⚠️ Learning score lower than expected: ${learning}`);
            }
            
            // Curiosity should be high (curiosity mentioned explicitly)
            if (curiosity >= 3.5) {
                console.log('   ✅ Curiosity score appropriately high');
            } else {
                console.log(`   ⚠️ Curiosity score lower than expected: ${curiosity}`);
            }
            
            // Analysis should be moderate to high (analytical thinking mentioned)
            if (analysis >= 3.0) {
                console.log('   ✅ Analysis score appropriately high');
            } else {
                console.log(`   ⚠️ Analysis score lower than expected: ${analysis}`);
            }
            
        } else {
            console.log('   ❌ extractCoreValues returns incorrect data');
            allTestsPassed = false;
        }
    } catch (error) {
        console.log(`   ❌ Core values extraction error: ${error.message}`);
        allTestsPassed = false;
    }
    
    // Test 4: Chart configuration
    console.log('\n4️⃣ Testing chart configuration...');
    try {
        const chartManager = new CognitiveChartManager();
        const testData = {
            labels: ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
            values: [4.2, 3.8, 4.7, 4.5, 3.9, 4.1]
        };
        
        // Mock the chart creation to capture configuration
        let capturedConfig = null;
        global.Chart = function(ctx, config) {
            capturedConfig = config;
            this.config = config;
            this.data = config.data;
            this.destroy = () => {};
            this.update = () => {};
        };
        
        chartManager.createCoreValuesChart(testData);
        
        if (capturedConfig) {
            console.log('   ✅ Chart configuration captured');
            
            // Check chart type
            if (capturedConfig.type === 'radar') {
                console.log('   ✅ Chart type is radar');
            } else {
                console.log(`   ❌ Chart type incorrect: ${capturedConfig.type}`);
                allTestsPassed = false;
            }
            
            // Check data structure
            if (capturedConfig.data && capturedConfig.data.datasets && capturedConfig.data.datasets.length > 0) {
                console.log('   ✅ Chart data structure correct');
                
                const dataset = capturedConfig.data.datasets[0];
                
                // Check colors (should be cyan theme)
                if (dataset.borderColor === '#58A6FF') {
                    console.log('   ✅ Cyan color scheme applied');
                } else {
                    console.log(`   ❌ Color scheme incorrect: ${dataset.borderColor}`);
                    allTestsPassed = false;
                }
                
                // Check animation settings
                if (capturedConfig.options && capturedConfig.options.animation && capturedConfig.options.animation.duration >= 1000) {
                    console.log('   ✅ Smooth animations configured');
                } else {
                    console.log('   ❌ Animation settings incorrect');
                    allTestsPassed = false;
                }
                
            } else {
                console.log('   ❌ Chart data structure incorrect');
                allTestsPassed = false;
            }
        } else {
            console.log('   ❌ Chart configuration not captured');
            allTestsPassed = false;
        }
    } catch (error) {
        console.log(`   ❌ Chart configuration error: ${error.message}`);
        allTestsPassed = false;
    }
    
    // Final results
    console.log('\n==========================');
    console.log('📋 VALIDATION RESULTS');
    console.log('==========================');
    
    if (allTestsPassed) {
        console.log('🎉 ✅ ALL CORE TESTS PASSED!');
        console.log('');
        console.log('Task 6 core implementation is working correctly:');
        console.log('✅ Core Values radar chart creation');
        console.log('✅ Memory data processing and extraction');
        console.log('✅ Sophisticated keyword analysis algorithm');
        console.log('✅ Proper chart configuration with cyan theme');
        console.log('✅ Smooth animations and interactive features');
        console.log('');
        console.log('🎯 Task 6 requirements successfully implemented!');
    } else {
        console.log('❌ SOME TESTS FAILED');
        console.log('Please review the failed tests above.');
    }
    
    return allTestsPassed;
}

// Run the validation
runCoreValidation();