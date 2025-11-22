/**
 * Cognitive Chart Manager for Synapse AI Web Application
 * 
 * Handles creation, configuration, and management of Chart.js visualizations
 * with HUD theme styling for cognitive insights display
 */

class CognitiveChartManager {
    constructor(dashboardElement) {
        this.dashboard = dashboardElement;
        this.charts = {};
        this.chartConfig = this.getHUDChartConfig();
        this.isInitialized = false;
    }
    
    /**
     * Get base Chart.js configuration with HUD theme styling
     */
    getHUDChartConfig() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#C9D1D9',
                        font: {
                            family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                            size: 12,
                            weight: '500'
                        },
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(13, 17, 23, 0.95)',
                    titleColor: '#C9D1D9',
                    bodyColor: '#C9D1D9',
                    borderColor: '#58A6FF',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    titleFont: {
                        family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                        size: 12
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: '#C9D1D9',
                        font: {
                            family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                            size: 11
                        }
                    },
                    grid: { 
                        color: 'rgba(201, 209, 217, 0.1)',
                        borderColor: 'rgba(201, 209, 217, 0.2)'
                    }
                },
                y: {
                    ticks: { 
                        color: '#C9D1D9',
                        font: {
                            family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                            size: 11
                        }
                    },
                    grid: { 
                        color: 'rgba(201, 209, 217, 0.1)',
                        borderColor: 'rgba(201, 209, 217, 0.2)'
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        };
    }
    
    /**
     * Initialize chart containers and setup
     */
    init() {
        if (this.isInitialized) return;
        
        // Clean up any existing charts first
        this.cleanupAllCharts();
        
        this.isInitialized = true;
        console.log('CognitiveChartManager initialized');
    }
    
    /**
     * Clean up all existing charts to prevent canvas reuse errors
     */
    cleanupAllCharts() {
        // Destroy all existing Chart.js instances
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                try {
                    chart.destroy();
                } catch (error) {
                    console.warn('Error destroying chart:', error);
                }
            }
        });
        
        // Clear the charts object
        this.charts = {};
        
        // Also clean up any orphaned Chart.js instances
        const canvasIds = ['core-values-chart', 'recurring-themes-chart', 'emotional-landscape-chart'];
        canvasIds.forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                const existingChart = Chart.getChart(canvas);
                if (existingChart) {
                    try {
                        existingChart.destroy();
                    } catch (error) {
                        console.warn(`Error destroying existing chart on ${canvasId}:`, error);
                    }
                }
            }
        });
    }
    
    /**
     * Update charts with real memory data from API
     */
    async updateChartsWithMemoryData() {
        const chartIds = ['core-values', 'recurring-themes', 'emotional-landscape'];
        const chartTypes = ['radar', 'bar', 'doughnut'];
        
        try {
            // Dispatch loading started events for all charts
            chartIds.forEach((chartId, index) => {
                document.dispatchEvent(new CustomEvent('chartLoadingStarted', {
                    detail: { 
                        chartId, 
                        chartType: chartTypes[index]
                    }
                }));
            });
            
            const response = await fetch('/api/insights');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.message || 'Failed to fetch insights data');
            }
            
            // Process memory data into chart-ready formats
            const chartData = this.processMemoryDataForCharts(data);
            
            // Update or create charts with real data
            await this.createCoreValuesChart(chartData.coreValues);
            await this.createRecurringThemesChart(chartData.recurringThemes);
            await this.createEmotionalLandscapeChart(chartData.emotionalLandscape);
            
            // Dispatch loading completed events for all charts
            chartIds.forEach(chartId => {
                document.dispatchEvent(new CustomEvent('chartLoadingCompleted', {
                    detail: { chartId }
                }));
            });
            
            console.log('Charts updated with real memory data');
            
        } catch (error) {
            console.error('Failed to update charts with memory data:', error);
            
            // Use the new chart error handling system
            if (window.chartErrorHandler) {
                chartIds.forEach((chartId, index) => {
                    window.chartErrorHandler.handleChartError(
                        chartId, 
                        chartTypes[index], 
                        error, 
                        { source: 'data_loading' }
                    );
                });
            } else {
                // Fallback to old error handling
                chartIds.forEach(chartId => {
                    document.dispatchEvent(new CustomEvent('chartError', {
                        detail: { 
                            chartId, 
                            error 
                        }
                    }));
                });
                
                this.showChartPlaceholders();
            }
        }
    }
    
    /**
     * Process memory.json data into chart-ready formats
     */
    processMemoryDataForCharts(memoryData) {
        const insights = memoryData.insights || [];
        const summaries = memoryData.conversation_summaries || [];
        
        // Core Values processing
        const coreValues = this.extractCoreValues(insights);
        
        // Recurring Themes processing
        const themes = this.extractRecurringThemes(insights, summaries);
        
        // Emotional Landscape processing
        const emotions = this.extractEmotionalData(insights);
        
        return {
            coreValues: {
                labels: ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
                values: coreValues,
                metadata: {
                    lastUpdated: new Date().toISOString(),
                    sampleSize: insights.length,
                    confidenceScore: this.calculateAverageConfidence(insights)
                }
            },
            recurringThemes: {
                labels: themes.map(t => t.theme),
                frequencies: themes.map(t => t.frequency),
                metadata: {
                    totalThemes: themes.length,
                    timeRange: this.getTimeRange(summaries),
                    trendDirection: this.calculateTrendDirection(themes)
                }
            },
            emotionalLandscape: {
                labels: emotions.map(e => e.emotion),
                values: emotions.map(e => e.intensity),
                colors: emotions.map(e => e.color),
                metadata: {
                    dominantEmotion: emotions.length > 0 ? emotions[0].emotion : 'Neutral',
                    emotionalBalance: this.calculateEmotionalBalance(emotions),
                    volatility: this.calculateEmotionalVolatility(emotions)
                }
            }
        };
    }
    
    /**
     * Extract core values from insights data
     */
    extractCoreValues(insights) {
        const valueCategories = {
            'Creativity': ['creativity', 'creative', 'innovation', 'artistic', 'imagination'],
            'Stability': ['stability', 'consistent', 'reliable', 'steady', 'structured'],
            'Learning': ['learning', 'education', 'knowledge', 'study', 'understanding'],
            'Curiosity': ['curious', 'curiosity', 'explore', 'discover', 'question'],
            'Analysis': ['analysis', 'analytical', 'logical', 'systematic', 'reasoning'],
            'Empathy': ['empathy', 'compassion', 'understanding', 'caring', 'emotional']
        };
        
        const values = [0, 0, 0, 0, 0, 0]; // Default values
        
        if (insights.length === 0) {
            return [3, 4, 5, 4, 3, 4]; // Placeholder values
        }
        
        // Analyze insights for value indicators
        Object.keys(valueCategories).forEach((value, index) => {
            const keywords = valueCategories[value];
            let score = 0;
            let count = 0;
            
            insights.forEach(insight => {
                const content = (insight.content || '').toLowerCase();
                const tags = (insight.tags || []).map(tag => tag.toLowerCase());
                const evidence = (insight.evidence || '').toLowerCase();
                
                const hasKeyword = keywords.some(keyword => 
                    content.includes(keyword) || 
                    tags.includes(keyword) || 
                    evidence.includes(keyword)
                );
                
                if (hasKeyword) {
                    score += (insight.confidence || 0.5) * 5; // Scale to 0-5
                    count++;
                }
            });
            
            values[index] = count > 0 ? Math.min(5, score / count) : 2.5;
        });
        
        return values;
    }
    
    /**
     * Extract recurring themes from insights and summaries
     */
    extractRecurringThemes(insights, summaries) {
        const themeFrequency = {};
        
        // Extract themes from insights
        insights.forEach(insight => {
            const category = insight.category || 'other';
            const tags = insight.tags || [];
            
            // Count category frequency
            themeFrequency[category] = (themeFrequency[category] || 0) + 1;
            
            // Count tag frequency
            tags.forEach(tag => {
                const normalizedTag = tag.toLowerCase().replace(/[_-]/g, ' ');
                themeFrequency[normalizedTag] = (themeFrequency[normalizedTag] || 0) + 1;
            });
        });
        
        // Extract themes from conversation summaries
        summaries.forEach(summary => {
            const themes = summary.key_themes || [];
            themes.forEach(theme => {
                const normalizedTheme = theme.toLowerCase().replace(/[_-]/g, ' ');
                themeFrequency[normalizedTheme] = (themeFrequency[normalizedTheme] || 0) + 1;
            });
        });
        
        // Convert to sorted array and take top themes
        const sortedThemes = Object.entries(themeFrequency)
            .map(([theme, frequency]) => ({ theme: this.capitalizeTheme(theme), frequency }))
            .sort((a, b) => b.frequency - a.frequency)
            .slice(0, 8); // Top 8 themes
        
        // Return placeholder data if no themes found
        if (sortedThemes.length === 0) {
            return [
                { theme: 'Technology', frequency: 8 },
                { theme: 'Philosophy', frequency: 6 },
                { theme: 'Learning', frequency: 7 },
                { theme: 'Creativity', frequency: 5 }
            ];
        }
        
        return sortedThemes;
    }
    
    /**
     * Extract emotional data from insights
     */
    extractEmotionalData(insights) {
        const emotionKeywords = {
            'Curious': ['curious', 'wonder', 'explore', 'discover', 'question'],
            'Analytical': ['analysis', 'logical', 'systematic', 'reasoning', 'examine'],
            'Optimistic': ['optimistic', 'positive', 'hopeful', 'confident', 'bright'],
            'Thoughtful': ['thoughtful', 'reflective', 'contemplative', 'considerate'],
            'Creative': ['creative', 'innovative', 'artistic', 'imaginative', 'original'],
            'Empathetic': ['empathetic', 'compassionate', 'understanding', 'caring', 'sensitive']
        };
        
        const emotionColors = {
            'Curious': '#58A6FF',
            'Analytical': '#7C3AED',
            'Optimistic': '#10B981',
            'Thoughtful': '#F59E0B',
            'Creative': '#EF4444',
            'Empathetic': '#8B5CF6'
        };
        
        const emotionScores = {};
        
        // Initialize emotion scores
        Object.keys(emotionKeywords).forEach(emotion => {
            emotionScores[emotion] = 0;
        });
        
        if (insights.length === 0) {
            // Return placeholder data
            return [
                { emotion: 'Curious', intensity: 25, color: emotionColors['Curious'] },
                { emotion: 'Analytical', intensity: 20, color: emotionColors['Analytical'] },
                { emotion: 'Optimistic', intensity: 20, color: emotionColors['Optimistic'] },
                { emotion: 'Thoughtful', intensity: 15, color: emotionColors['Thoughtful'] },
                { emotion: 'Creative', intensity: 12, color: emotionColors['Creative'] },
                { emotion: 'Empathetic', intensity: 8, color: emotionColors['Empathetic'] }
            ];
        }
        
        // Analyze insights for emotional indicators
        insights.forEach(insight => {
            const content = (insight.content || '').toLowerCase();
            const tags = (insight.tags || []).map(tag => tag.toLowerCase());
            const evidence = (insight.evidence || '').toLowerCase();
            const confidence = insight.confidence || 0.5;
            
            Object.entries(emotionKeywords).forEach(([emotion, keywords]) => {
                const hasKeyword = keywords.some(keyword => 
                    content.includes(keyword) || 
                    tags.includes(keyword) || 
                    evidence.includes(keyword)
                );
                
                if (hasKeyword) {
                    emotionScores[emotion] += confidence;
                }
            });
        });
        
        // Convert to percentages and sort by intensity
        const totalScore = Object.values(emotionScores).reduce((sum, score) => sum + score, 0);
        
        if (totalScore === 0) {
            // Return balanced placeholder if no emotional indicators found
            return Object.keys(emotionKeywords).map(emotion => ({
                emotion,
                intensity: Math.round(100 / Object.keys(emotionKeywords).length),
                color: emotionColors[emotion]
            }));
        }
        
        return Object.entries(emotionScores)
            .map(([emotion, score]) => ({
                emotion,
                intensity: Math.round((score / totalScore) * 100),
                color: emotionColors[emotion]
            }))
            .filter(item => item.intensity > 0)
            .sort((a, b) => b.intensity - a.intensity);
    }
    
    /**
     * Show loading states for all charts
     */
    showChartLoadingStates() {
        const chartIds = ['core-values-status', 'recurring-themes-status', 'emotional-landscape-status'];
        chartIds.forEach(statusId => {
            this.updateChartStatus(statusId, 'Loading data...', 'loading');
        });
    }
    
    /**
     * Handle chart data errors
     */
    handleChartDataError(error) {
        console.error('Chart data error:', error);
        const chartIds = ['core-values-status', 'recurring-themes-status', 'emotional-landscape-status'];
        chartIds.forEach(statusId => {
            this.updateChartStatus(statusId, 'Data unavailable', 'error');
        });
    }
    
    /**
     * Show placeholder charts with sample data when real data is unavailable
     */
    showChartPlaceholders() {
        console.log('Showing chart placeholders with sample data');
        
        // Show placeholder charts with sample data
        this.createCoreValuesChart({
            labels: ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
            values: [3, 4, 5, 4, 3, 4]
        });
        
        this.createRecurringThemesChart({
            labels: ['Technology', 'Philosophy', 'Learning', 'Creativity'],
            frequencies: [8, 6, 7, 5]
        });
        
        this.createEmotionalLandscapeChart({
            labels: ['Curious', 'Analytical', 'Optimistic', 'Thoughtful'],
            values: [30, 25, 25, 20],
            colors: ['#58A6FF', '#7C3AED', '#10B981', '#F59E0B']
        });
        
        // Show placeholder message
        this.showPlaceholderMessage();
    }
    
    /**
     * Show message about placeholder data
     */
    showPlaceholderMessage() {
        const chartsSection = document.querySelector('.charts-section');
        if (chartsSection) {
            let placeholderMessage = chartsSection.querySelector('.placeholder-message');
            if (!placeholderMessage) {
                placeholderMessage = document.createElement('div');
                placeholderMessage.className = 'placeholder-message glass-panel';
                placeholderMessage.innerHTML = `
                    <div class="placeholder-icon">📊</div>
                    <h4>Sample Data Displayed</h4>
                    <p>Charts are showing sample data. Have more conversations to see your personalized insights!</p>
                `;
                chartsSection.insertBefore(placeholderMessage, chartsSection.firstChild);
            }
        }
    }
    
    /**
     * Remove placeholder message
     */
    removePlaceholderMessage() {
        const placeholderMessage = document.querySelector('.placeholder-message');
        if (placeholderMessage) {
            placeholderMessage.remove();
        }
    }
    
    /**
     * Refresh charts by fetching latest data
     */
    async refreshCharts() {
        console.log('Refreshing charts with latest data...');
        await this.updateChartsWithMemoryData();
    }
    
    // Helper methods for data processing
    calculateAverageConfidence(insights) {
        if (insights.length === 0) return 0;
        const totalConfidence = insights.reduce((sum, insight) => sum + (insight.confidence || 0), 0);
        return totalConfidence / insights.length;
    }
    
    getTimeRange(summaries) {
        if (summaries.length === 0) return 'No data';
        const timestamps = summaries.map(s => new Date(s.timestamp)).sort();
        const earliest = timestamps[0];
        const latest = timestamps[timestamps.length - 1];
        const daysDiff = Math.ceil((latest - earliest) / (1000 * 60 * 60 * 24));
        return daysDiff > 0 ? `${daysDiff} days` : 'Today';
    }
    
    calculateTrendDirection(themes) {
        // Simple trend calculation - could be enhanced with historical data
        return themes.length > 4 ? 'up' : themes.length > 2 ? 'stable' : 'down';
    }
    
    calculateEmotionalBalance(emotions) {
        if (emotions.length === 0) return 0;
        const variance = emotions.reduce((sum, emotion) => {
            const avgIntensity = 100 / emotions.length;
            return sum + Math.pow(emotion.intensity - avgIntensity, 2);
        }, 0) / emotions.length;
        return Math.max(0, 100 - Math.sqrt(variance));
    }
    
    calculateEmotionalVolatility(emotions) {
        if (emotions.length < 2) return 0;
        const intensities = emotions.map(e => e.intensity);
        const max = Math.max(...intensities);
        const min = Math.min(...intensities);
        return max - min;
    }
    
    capitalizeTheme(theme) {
        return theme.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    /**
     * Update chart status indicator
     */
    updateChartStatus(statusId, message, type = 'info') {
        const statusElement = document.getElementById(statusId);
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `chart-status ${type}`;
        }
    }
    
    /**
     * Create loading skeleton for charts
     */
    createChartLoadingSkeleton(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const container = canvas.parentElement;
        if (!container) return;
        
        // Create loading skeleton
        const skeleton = document.createElement('div');
        skeleton.className = 'chart-loading-skeleton';
        skeleton.innerHTML = `
            <div class="skeleton-chart">
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line short"></div>
            </div>
        `;
        
        // Hide canvas and show skeleton
        canvas.style.display = 'none';
        container.appendChild(skeleton);
        
        return skeleton;
    }
    
    /**
     * Remove loading skeleton and show chart
     */
    removeChartLoadingSkeleton(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const container = canvas.parentElement;
        if (!container) return;
        
        const skeleton = container.querySelector('.chart-loading-skeleton');
        if (skeleton) {
            skeleton.remove();
        }
        
        canvas.style.display = 'block';
    }
    
    /**
     * Show error state for a specific chart
     */
    showChartErrorState(canvasId, errorMessage) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const container = canvas.parentElement;
        if (!container) return;
        
        // Create error state
        const errorState = document.createElement('div');
        errorState.className = 'chart-error-state';
        errorState.innerHTML = `
            <div class="error-icon">⚠️</div>
            <h4>Chart Unavailable</h4>
            <p>${errorMessage}</p>
            <button class="retry-chart-button" onclick="window.globalChartManager?.refreshCharts()">
                Retry
            </button>
        `;
        
        // Hide canvas and show error state
        canvas.style.display = 'none';
        container.appendChild(errorState);
    }
    
    /**
     * Remove error state and show chart
     */
    removeChartErrorState(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const container = canvas.parentElement;
        if (!container) return;
        
        const errorState = container.querySelector('.chart-error-state');
        if (errorState) {
            errorState.remove();
        }
        
        canvas.style.display = 'block';
    }

    /**
     * Create Core Values radar chart with enhanced styling and interactivity
     */
    createCoreValuesChart(data) {
        const ctx = document.getElementById('core-values-chart');
        if (!ctx) {
            console.error('Core values chart canvas not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (this.charts.coreValues) {
            try {
                this.charts.coreValues.destroy();
                this.charts.coreValues = null;
            } catch (error) {
                console.warn('Error destroying existing chart:', error);
                this.charts.coreValues = null;
            }
        }
        
        // Clear any existing Chart.js instances on this canvas
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        // Create "Power Core" radial gradient for enhanced depth
        const canvas = ctx.canvas || ctx;
        const chartCtx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) * 0.8;
        
        const coreGradient = chartCtx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
        coreGradient.addColorStop(0, 'rgba(0, 229, 255, 0.4)'); // Bright center
        coreGradient.addColorStop(0.3, 'rgba(88, 166, 255, 0.3)'); // Mid transition
        coreGradient.addColorStop(0.7, 'rgba(0, 229, 255, 0.15)'); // Outer glow
        coreGradient.addColorStop(1, 'rgba(0, 229, 255, 0.05)'); // Transparent edge
        
        const chartData = {
            labels: data.labels || ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
            datasets: [{
                label: 'Core Values',
                data: data.values || [3, 4, 5, 4, 3, 4],
                backgroundColor: coreGradient,
                borderColor: '#00E5FF',
                borderWidth: 3,
                pointBackgroundColor: '#00E5FF',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 3,
                pointRadius: 8,
                pointHoverBackgroundColor: '#FFFFFF',
                pointHoverBorderColor: '#00E5FF',
                pointHoverBorderWidth: 5,
                pointHoverRadius: 16,
                tension: 0.2,
                // Enhanced styling for glow effect
                shadowColor: '#00E5FF',
                shadowBlur: 25,
                shadowOffsetX: 0,
                shadowOffsetY: 0
            }]
        };
        
        try {
            this.charts.coreValues = new Chart(ctx, {
                type: 'radar',
                data: chartData,
                options: {
                ...this.chartConfig,
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'point'
                },
                scales: {
                    r: {
                        angleLines: { 
                            color: 'rgba(0, 229, 255, 0.2)',
                            lineWidth: 0.8
                        },
                        grid: { 
                            color: 'rgba(0, 229, 255, 0.15)',
                            lineWidth: 0.8
                        },
                        pointLabels: { 
                            color: '#C9D1D9',
                            font: {
                                family: 'Roboto Mono, SF Mono, Monaco, monospace',
                                size: 12,
                                weight: '600'
                            },
                            padding: 12
                        },
                        ticks: { 
                            color: 'rgba(201, 209, 217, 0.5)',
                            backdropColor: 'transparent',
                            font: {
                                family: 'Roboto Mono, SF Mono, Monaco, monospace',
                                size: 10
                            },
                            stepSize: 1,
                            showLabelBackdrop: false
                        },
                        min: 0,
                        max: 5,
                        beginAtZero: true
                    }
                },
                plugins: {
                    ...this.chartConfig.plugins,
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(13, 17, 23, 0.95)',
                        titleColor: '#58A6FF',
                        bodyColor: '#C9D1D9',
                        borderColor: '#58A6FF',
                        borderWidth: 2,
                        cornerRadius: 8,
                        displayColors: false,
                        titleFont: {
                            family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                            size: 12
                        },
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                const value = context.parsed.r;
                                const percentage = Math.round((value / 5) * 100);
                                return `Strength: ${value}/5 (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                return this.getCoreValueDescription(context.label);
                            }.bind(this)
                        }
                    }
                },
                animation: {
                    duration: 1200,
                    easing: 'easeInOutQuart',
                    animateRotate: true,
                    animateScale: true
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
        
        this.updateChartStatus('core-values-status', 'Ready', 'success');
        
        // Register chart with performance optimizer
        this.registerChartWithOptimizer('coreValues', this.charts.coreValues);
        
        console.log('Enhanced Core Values chart created with interactive features');
        
        // Remove placeholder message if charts are successfully created with real data
        if (data.metadata && data.metadata.sampleSize > 0) {
            this.removePlaceholderMessage();
        }
        
        } catch (error) {
            console.error('Error creating Core Values chart:', error);
            
            // Use the new comprehensive error handling system
            if (window.chartErrorHandler) {
                window.chartErrorHandler.handleChartError(
                    'core-values', 
                    'radar', 
                    error, 
                    { source: 'chart_creation', data: data }
                );
            } else {
                // Fallback error handling
                this.updateChartStatus('core-values-status', 'Chart creation failed', 'error');
                
                // If it's a canvas reuse error, try to recover by clearing the canvas
                if (error.message.includes('Canvas is already in use')) {
                    console.log('Attempting to recover from canvas reuse error...');
                    // Clean up all charts and wait a bit before trying again
                    this.cleanupAllCharts();
                    setTimeout(() => {
                        try {
                            this.createCoreValuesChart(data);
                        } catch (retryError) {
                            console.error('Retry failed:', retryError);
                            this.updateChartStatus('core-values-status', 'Chart creation failed', 'error');
                        }
                    }, 200);
                }
            }
        }
    }
    
    /**
     * Get description for core value dimensions
     */
    getCoreValueDescription(label) {
        const descriptions = {
            'Creativity': 'Innovation and original thinking',
            'Stability': 'Consistency and reliability',
            'Learning': 'Knowledge acquisition and growth',
            'Curiosity': 'Exploration and questioning',
            'Analysis': 'Logical and systematic thinking',
            'Empathy': 'Understanding and compassion'
        };
        return descriptions[label] || 'Core personality dimension';
    }
    
    /**
     * Create Recurring Themes horizontal bar chart with enhanced styling and interactivity
     */
    createRecurringThemesChart(data) {
        const ctx = document.getElementById('recurring-themes-chart');
        if (!ctx) {
            console.error('Recurring themes chart canvas not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (this.charts.recurringThemes) {
            try {
                this.charts.recurringThemes.destroy();
                this.charts.recurringThemes = null;
            } catch (error) {
                console.warn('Error destroying existing recurring themes chart:', error);
                this.charts.recurringThemes = null;
            }
        }
        
        // Clear any existing Chart.js instances on this canvas
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        const labels = data.labels || ['Technology', 'Philosophy', 'Learning', 'Creativity'];
        const frequencies = data.frequencies || [8, 6, 7, 5];
        const totalFrequency = frequencies.reduce((sum, freq) => sum + freq, 0);
        
        // Create gradient bars with enhanced depth effect
        const gradientColors = frequencies.map((freq, index) => {
            const canvas = ctx.canvas || ctx;
            const chartCtx = canvas.getContext('2d');
            const gradient = chartCtx.createLinearGradient(0, 0, 300, 0);
            const intensity = freq / Math.max(...frequencies);
            const baseAlpha = 0.7 + (intensity * 0.3);
            
            gradient.addColorStop(0, `rgba(0, 229, 255, ${baseAlpha})`); // Bright cyan start
            gradient.addColorStop(0.5, `rgba(88, 166, 255, ${baseAlpha})`); // Mid cyan
            gradient.addColorStop(1, `rgba(58, 133, 210, ${baseAlpha * 0.8})`); // Darker cyan end
            
            return gradient;
        });
        
        const hoverColors = frequencies.map((freq, index) => {
            const canvas = ctx.canvas || ctx;
            const chartCtx = canvas.getContext('2d');
            const gradient = chartCtx.createLinearGradient(0, 0, 300, 0);
            const intensity = freq / Math.max(...frequencies);
            const baseAlpha = 0.9 + (intensity * 0.1);
            
            gradient.addColorStop(0, `rgba(0, 229, 255, ${baseAlpha})`);
            gradient.addColorStop(0.5, `rgba(88, 166, 255, ${baseAlpha})`);
            gradient.addColorStop(1, `rgba(58, 133, 210, ${baseAlpha})`);
            
            return gradient;
        });
        
        try {
            this.charts.recurringThemes = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Frequency',
                        data: frequencies,
                        backgroundColor: gradientColors,
                        borderColor: '#00E5FF',
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false,
                        hoverBackgroundColor: hoverColors,
                        hoverBorderColor: '#FFFFFF',
                        hoverBorderWidth: 3,
                        hoverBorderRadius: 10,
                        // Enhanced bar styling
                        barThickness: 'flex',
                        maxBarThickness: 45,
                        minBarLength: 2,
                        // Add subtle glow effect data
                        shadowColor: '#00E5FF',
                        shadowBlur: 15,
                        shadowOffsetX: 0,
                        shadowOffsetY: 0
                    }]
                },
                options: {
                    ...this.chartConfig,
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    layout: {
                        padding: {
                            left: 10,
                            right: 20,
                            top: 10,
                            bottom: 10
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart',
                        delay: function(context) {
                            // Staggered animation delay for each bar
                            return context.dataIndex * 150;
                        }
                    },
                    plugins: {
                        ...this.chartConfig.plugins,
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(13, 17, 23, 0.95)',
                            titleColor: '#58A6FF',
                            bodyColor: '#C9D1D9',
                            borderColor: '#58A6FF',
                            borderWidth: 2,
                            cornerRadius: 8,
                            displayColors: false,
                            titleFont: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 12
                            },
                            callbacks: {
                                title: function(context) {
                                    return `Theme: ${context[0].label}`;
                                },
                                label: function(context) {
                                    const frequency = context.parsed.x;
                                    const percentage = totalFrequency > 0 ? Math.round((frequency / totalFrequency) * 100) : 0;
                                    return [
                                        `Frequency: ${frequency} occurrences`,
                                        `Percentage: ${percentage}% of total themes`,
                                        `Rank: #${context.dataIndex + 1} most discussed`
                                    ];
                                },
                                afterLabel: function(context) {
                                    return this.getThemeDescription(context.label);
                                }.bind(this)
                            }
                        },
                        // Add data labels plugin
                        datalabels: false // Disable default datalabels, we'll use custom implementation
                    },
                    scales: {
                        x: {
                            ...this.chartConfig.scales.x,
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 229, 255, 0.08)',
                                borderColor: 'rgba(0, 229, 255, 0.2)',
                                lineWidth: 0.5
                            },
                            ticks: {
                                color: '#C9D1D9',
                                font: {
                                    family: 'Roboto Mono, SF Mono, Monaco, monospace',
                                    size: 11,
                                    weight: '500'
                                },
                                callback: function(value) {
                                    return Number.isInteger(value) ? value : '';
                                }
                            },
                            title: {
                                display: true,
                                text: 'Discussion Frequency',
                                color: '#C9D1D9',
                                font: {
                                    family: 'Roboto Mono, SF Mono, Monaco, monospace',
                                    size: 12,
                                    weight: '600'
                                },
                                padding: {
                                    top: 10
                                }
                            }
                        },
                        y: {
                            ...this.chartConfig.scales.y,
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#C9D1D9',
                                font: {
                                    family: 'Roboto Mono, SF Mono, Monaco, monospace',
                                    size: 11,
                                    weight: '600'
                                },
                                padding: 8
                            },
                            title: {
                                display: true,
                                text: 'Conversation Themes',
                                color: '#C9D1D9',
                                font: {
                                    family: 'Roboto Mono, SF Mono, Monaco, monospace',
                                    size: 12,
                                    weight: '600'
                                },
                                padding: {
                                    bottom: 10
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart',
                        delay: (context) => {
                            // Stagger animation for each bar
                            return context.dataIndex * 100;
                        }
                    },
                    onHover: (event, activeElements) => {
                        event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                        
                        // Add glow effect to hovered bars
                        if (activeElements.length > 0) {
                            const canvas = event.chart.canvas;
                            canvas.style.filter = 'drop-shadow(0 0 10px rgba(88, 166, 255, 0.5))';
                        } else {
                            const canvas = event.chart.canvas;
                            canvas.style.filter = 'none';
                        }
                    }
                }
            });
            
            // Add custom data labels after chart creation
            this.addRecurringThemesDataLabels();
            
            this.updateChartStatus('recurring-themes-status', 'Ready', 'success');
            
            // Register chart with performance optimizer
            this.registerChartWithOptimizer('recurringThemes', this.charts.recurringThemes);
            
            console.log('Enhanced Recurring Themes chart created with interactive features');
            
            // Remove placeholder message if charts are successfully created with real data
            if (data.metadata && data.metadata.totalThemes > 0) {
                this.removePlaceholderMessage();
            }
            
        } catch (error) {
            console.error('Error creating Recurring Themes chart:', error);
            this.updateChartStatus('recurring-themes-status', 'Chart creation failed', 'error');
            
            // Recovery attempt for canvas reuse errors
            if (error.message.includes('Canvas is already in use')) {
                console.log('Attempting to recover from canvas reuse error...');
                this.cleanupAllCharts();
                setTimeout(() => {
                    try {
                        this.createRecurringThemesChart(data);
                    } catch (retryError) {
                        console.error('Retry failed:', retryError);
                        this.updateChartStatus('recurring-themes-status', 'Chart creation failed', 'error');
                    }
                }, 200);
            }
        }
    }
    
    /**
     * Add custom data labels to recurring themes chart
     */
    addRecurringThemesDataLabels() {
        const chart = this.charts.recurringThemes;
        if (!chart) return;
        
        // Add custom plugin for data labels
        const dataLabelsPlugin = {
            id: 'recurringThemesDataLabels',
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                const dataset = chart.data.datasets[0];
                const meta = chart.getDatasetMeta(0);
                
                ctx.save();
                ctx.font = '600 11px SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif';
                ctx.fillStyle = '#C9D1D9';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                
                meta.data.forEach((bar, index) => {
                    const value = dataset.data[index];
                    if (value > 0) {
                        const x = bar.x + 8; // Offset from bar end
                        const y = bar.y;
                        
                        // Add glow effect to text
                        ctx.shadowColor = 'rgba(88, 166, 255, 0.5)';
                        ctx.shadowBlur = 4;
                        ctx.fillText(value.toString(), x, y);
                        ctx.shadowBlur = 0;
                    }
                });
                
                ctx.restore();
            }
        };
        
        // Register the plugin
        Chart.register(dataLabelsPlugin);
    }
    
    /**
     * Get description for theme categories
     */
    getThemeDescription(theme) {
        const descriptions = {
            'Technology': 'Discussions about tech, programming, and digital innovation',
            'Philosophy': 'Deep thoughts, ethics, and philosophical concepts',
            'Learning': 'Education, skill development, and knowledge acquisition',
            'Creativity': 'Art, design, creative processes, and imagination',
            'Science': 'Scientific concepts, research, and discoveries',
            'Personal': 'Personal development, relationships, and life experiences',
            'Business': 'Work, entrepreneurship, and professional topics',
            'Health': 'Wellness, fitness, and medical discussions',
            'Entertainment': 'Movies, games, books, and leisure activities',
            'Travel': 'Places, cultures, and travel experiences'
        };
        return descriptions[theme] || 'Conversation topic and related discussions';
    }
    
    /**
     * Create Emotional Landscape doughnut chart with enhanced styling and interactivity
     */
    createEmotionalLandscapeChart(data) {
        const ctx = document.getElementById('emotional-landscape-chart');
        if (!ctx) {
            console.error('Emotional landscape chart canvas not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (this.charts.emotionalLandscape) {
            try {
                this.charts.emotionalLandscape.destroy();
                this.charts.emotionalLandscape = null;
            } catch (error) {
                console.warn('Error destroying existing emotional landscape chart:', error);
                this.charts.emotionalLandscape = null;
            }
        }
        
        // Clear any existing Chart.js instances on this canvas
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        const labels = data.labels || ['Curious', 'Analytical', 'Optimistic', 'Thoughtful', 'Creative', 'Empathetic'];
        const values = data.values || [25, 20, 20, 15, 12, 8];
        const totalValue = values.reduce((sum, val) => sum + val, 0);
        
        // Find dominant emotion
        const maxIndex = values.indexOf(Math.max(...values));
        const dominantEmotion = labels[maxIndex];
        const dominantPercentage = Math.round((values[maxIndex] / totalValue) * 100);
        
        // Enhanced multi-color palette for different emotions
        const emotionalColors = {
            'Analytical': '#00E5FF',    // Electric Cyan - Analytical thinking
            'Creative': '#8B5CF6',      // Purple - Creative expression
            'Optimistic': '#10B981',    // Emerald - Positive outlook
            'Curious': '#58A6FF',       // Blue - Inquisitive nature
            'Thoughtful': '#F59E0B',    // Amber - Deep contemplation
            'Empathetic': '#EC4899',    // Pink - Emotional understanding
            'Focused': '#06B6D4',       // Cyan variant - Concentration
            'Innovative': '#EF4444',    // Red - Breakthrough thinking
            'Reflective': '#84CC16',    // Lime - Self-awareness
            'Collaborative': '#F97316'  // Orange - Team-oriented
        };
        
        // Create gradient colors with varying intensity
        const backgroundColors = values.map((value, index) => {
            const emotion = labels[index];
            const baseColor = emotionalColors[emotion] || emotionalColors['Curious'];
            const intensity = value / Math.max(...values);
            const alpha = 0.6 + (intensity * 0.4); // Range from 0.6 to 1.0
            return this.hexToRgba(baseColor, alpha);
        });
        
        const borderColors = labels.map((emotion, index) => {
            return emotionalColors[emotion] || emotionalColors['Curious'];
        });
        
        const hoverColors = values.map((value, index) => {
            const emotion = labels[index];
            const baseColor = emotionalColors[emotion] || emotionalColors['Curious'];
            return baseColor; // Full opacity on hover
        });
        
        try {
            this.charts.emotionalLandscape = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 4,
                        hoverBackgroundColor: hoverColors,
                        hoverBorderColor: '#FFFFFF',
                        hoverBorderWidth: 5,
                        hoverOffset: 16,
                        // Enhanced segment styling
                        borderRadius: 6,
                        borderJoinStyle: 'round',
                        // Add subtle shadow effect
                        shadowColor: 'rgba(0, 229, 255, 0.3)',
                        shadowBlur: 20,
                        shadowOffsetX: 0,
                        shadowOffsetY: 0
                    }]
                },
                options: {
                    ...this.chartConfig,
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    interaction: {
                        intersect: false,
                        mode: 'point'
                    },
                    layout: {
                        padding: {
                            top: 20,
                            bottom: 20,
                            left: 20,
                            right: 200  // Increased right padding for side text
                        }
                    },
                    plugins: {
                        ...this.chartConfig.plugins,
                        legend: {
                            display: true,
                            position: 'bottom',
                            align: 'center',
                            labels: {
                                color: '#C9D1D9',
                                padding: 16,
                                usePointStyle: true,
                                pointStyle: 'circle',
                                font: {
                                    family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                    size: 11,
                                    weight: '500'
                                },
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        return data.labels.map((label, i) => {
                                            const value = data.datasets[0].data[i];
                                            const percentage = Math.round((value / totalValue) * 100);
                                            return {
                                                text: `${label} (${percentage}%)`,
                                                fillStyle: data.datasets[0].backgroundColor[i],
                                                strokeStyle: data.datasets[0].borderColor[i],
                                                lineWidth: 2,
                                                pointStyle: 'circle',
                                                hidden: false,
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
                                }
                            },
                            onClick: (event, legendItem, legend) => {
                                // Enhanced legend interactivity
                                const chart = legend.chart;
                                const index = legendItem.index;
                                const meta = chart.getDatasetMeta(0);
                                
                                // Toggle segment visibility
                                meta.data[index].hidden = !meta.data[index].hidden;
                                chart.update();
                                
                                // Update center text if needed
                                this.updateEmotionalLandscapeCenterText(chart);
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(13, 17, 23, 0.95)',
                            titleColor: '#58A6FF',
                            bodyColor: '#C9D1D9',
                            borderColor: '#58A6FF',
                            borderWidth: 2,
                            cornerRadius: 8,
                            displayColors: true,
                            titleFont: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 12
                            },
                            callbacks: {
                                title: function(context) {
                                    return `Emotion: ${context[0].label}`;
                                },
                                label: function(context) {
                                    const value = context.parsed;
                                    const percentage = Math.round((value / totalValue) * 100);
                                    const rank = this.getEmotionRank(context.dataIndex, values);
                                    return [
                                        `Intensity: ${value}% of conversations`,
                                        `Relative: ${percentage}% of emotional spectrum`,
                                        `Ranking: #${rank} most expressed emotion`
                                    ];
                                }.bind(this),
                                afterLabel: function(context) {
                                    return this.getEmotionDescription(context.label);
                                }.bind(this)
                            }
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart',
                        animateRotate: true,
                        animateScale: true,
                        delay: (context) => {
                            // Stagger animation for each segment
                            return context.dataIndex * 150;
                        }
                    },
                    onHover: (event, activeElements) => {
                        event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                        
                        // Add glow effect to canvas on hover
                        if (activeElements.length > 0) {
                            const canvas = event.chart.canvas;
                            canvas.style.filter = 'drop-shadow(0 0 15px rgba(88, 166, 255, 0.4))';
                        } else {
                            const canvas = event.chart.canvas;
                            canvas.style.filter = 'none';
                        }
                    }
                },
                plugins: [{
                    id: 'emotionalLandscapeCenterText',
                    beforeDraw: (chart) => {
                        this.drawEmotionalLandscapeCenterText(chart, dominantEmotion, dominantPercentage);
                    }
                }]
            });
            
            this.updateChartStatus('emotional-landscape-status', 'Ready', 'success');
            
            // Register chart with performance optimizer
            this.registerChartWithOptimizer('emotionalLandscape', this.charts.emotionalLandscape);
            
            console.log('Enhanced Emotional Landscape chart created with center text and interactive features');
            
            // Remove placeholder message if charts are successfully created with real data
            if (data.metadata && data.metadata.dominantEmotion !== 'Neutral') {
                this.removePlaceholderMessage();
            }
            
        } catch (error) {
            console.error('Error creating Emotional Landscape chart:', error);
            this.updateChartStatus('emotional-landscape-status', 'Chart creation failed', 'error');
            
            // Recovery attempt for canvas reuse errors
            if (error.message.includes('Canvas is already in use')) {
                console.log('Attempting to recover from canvas reuse error...');
                this.cleanupAllCharts();
                setTimeout(() => {
                    try {
                        this.createEmotionalLandscapeChart(data);
                    } catch (retryError) {
                        console.error('Retry failed:', retryError);
                        this.updateChartStatus('emotional-landscape-status', 'Chart creation failed', 'error');
                    }
                }, 200);
            }
        }
    }
    
    /**
     * Draw side text for emotional landscape chart showing dominant emotion
     */
    drawEmotionalLandscapeCenterText(chart, dominantEmotion, dominantPercentage) {
        const ctx = chart.ctx;
        const chartCenterX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
        const chartCenterY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;
        
        // Position text to the right of the chart
        const textX = chart.chartArea.right + 40; // 40px padding from chart edge
        const textY = chartCenterY;
        
        ctx.save();
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        
        // Draw background panel for text
        const panelWidth = 160;
        const panelHeight = 100;
        const panelX = textX - 10;
        const panelY = textY - panelHeight / 2;
        
        // Draw glassmorphism background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.strokeStyle = 'rgba(88, 166, 255, 0.3)';
        ctx.lineWidth = 1;
        
        // Use roundRect if available, otherwise use regular rect
        if (ctx.roundRect) {
            ctx.roundRect(panelX, panelY, panelWidth, panelHeight, 8);
        } else {
            ctx.rect(panelX, panelY, panelWidth, panelHeight);
        }
        ctx.fill();
        ctx.stroke();
        
        // Draw dominant emotion label
        ctx.font = '600 14px SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillStyle = '#58A6FF';
        ctx.shadowColor = 'rgba(88, 166, 255, 0.5)';
        ctx.shadowBlur = 6;
        ctx.fillText('DOMINANT EMOTION', textX, textY - 25);
        
        // Draw emotion name
        ctx.font = '700 20px SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillStyle = '#C9D1D9';
        ctx.shadowColor = 'rgba(201, 209, 217, 0.3)';
        ctx.shadowBlur = 4;
        ctx.fillText(dominantEmotion.toUpperCase(), textX, textY);
        
        // Draw percentage
        ctx.font = '600 16px SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillStyle = '#58A6FF';
        ctx.shadowColor = 'rgba(88, 166, 255, 0.4)';
        ctx.shadowBlur = 4;
        ctx.fillText(`${dominantPercentage}%`, textX, textY + 25);
        
        ctx.restore();
    }
    
    /**
     * Update center text when chart data changes
     */
    updateEmotionalLandscapeCenterText(chart) {
        const data = chart.data;
        const visibleData = data.datasets[0].data.filter((value, index) => {
            const meta = chart.getDatasetMeta(0);
            return !meta.data[index].hidden;
        });
        
        if (visibleData.length > 0) {
            const maxValue = Math.max(...visibleData);
            const maxIndex = data.datasets[0].data.indexOf(maxValue);
            const dominantEmotion = data.labels[maxIndex];
            const totalVisible = visibleData.reduce((sum, val) => sum + val, 0);
            const dominantPercentage = Math.round((maxValue / totalVisible) * 100);
            
            // Redraw chart to update center text
            chart.update('none');
        }
    }
    
    /**
     * Get emotion rank based on intensity values
     */
    getEmotionRank(emotionIndex, values) {
        const sortedValues = [...values].sort((a, b) => b - a);
        const emotionValue = values[emotionIndex];
        return sortedValues.indexOf(emotionValue) + 1;
    }
    
    /**
     * Get description for emotion types
     */
    getEmotionDescription(emotion) {
        const descriptions = {
            'Curious': 'Inquisitive and eager to learn new things',
            'Analytical': 'Logical, systematic, and detail-oriented thinking',
            'Optimistic': 'Positive outlook and hopeful perspective',
            'Thoughtful': 'Reflective, considerate, and contemplative',
            'Creative': 'Imaginative, innovative, and artistic expression',
            'Empathetic': 'Understanding and sharing others\' feelings',
            'Confident': 'Self-assured and certain in abilities',
            'Playful': 'Light-hearted, fun-loving, and spontaneous',
            'Focused': 'Concentrated attention and determination',
            'Calm': 'Peaceful, relaxed, and composed demeanor'
        };
        return descriptions[emotion] || 'Emotional state reflected in conversations';
    }
    
    /**
     * Convert hex color to rgba with specified alpha
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    /**
     * Update chart status indicator
     */
    updateChartStatus(statusId, message, type = 'info') {
        const statusElement = document.getElementById(statusId);
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `chart-status ${type}`;
        }
    }
    
    /**
     * Update all charts with memory data
     */
    async updateChartsWithMemoryData() {
        try {
            // Update all chart statuses to loading
            this.updateChartStatus('core-values-status', 'Loading...', 'loading');
            this.updateChartStatus('recurring-themes-status', 'Loading...', 'loading');
            this.updateChartStatus('emotional-landscape-status', 'Loading...', 'loading');
            
            const response = await fetch('/api/insights');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.message || 'Unknown error occurred');
            }
            
            // Process data for charts
            const chartData = this.processMemoryDataForCharts(data);
            
            // Create or update charts
            this.createCoreValuesChart(chartData.coreValues);
            this.createRecurringThemesChart(chartData.recurringThemes);
            this.createEmotionalLandscapeChart(chartData.emotionalLandscape);
            
            console.log('Charts updated with memory data');
            
        } catch (error) {
            console.error('Failed to update charts:', error);
            
            // Only show placeholders if it's a data loading error, not a canvas error
            if (!error.message.includes('Canvas is already in use')) {
                this.showChartPlaceholders();
                
                // Update all statuses to error
                this.updateChartStatus('core-values-status', 'Error loading data', 'error');
                this.updateChartStatus('recurring-themes-status', 'Error loading data', 'error');
                this.updateChartStatus('emotional-landscape-status', 'Error loading data', 'error');
            } else {
                // For canvas errors, just update status without showing placeholders
                this.updateChartStatus('core-values-status', 'Chart initialization error', 'error');
                this.updateChartStatus('recurring-themes-status', 'Chart initialization error', 'error');
                this.updateChartStatus('emotional-landscape-status', 'Chart initialization error', 'error');
            }
        }
    }
    
    /**
     * Show placeholder charts with sample data when real data is unavailable
     */
    showChartPlaceholders() {
        console.log('Showing chart placeholders with sample data');
        
        // Show placeholder charts with sample data
        this.createCoreValuesChart({
            labels: ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
            values: [3, 4, 5, 4, 3, 4]
        });
        
        this.createRecurringThemesChart({
            labels: ['Technology', 'Philosophy', 'Learning', 'Creativity'],
            frequencies: [8, 6, 7, 5]
        });
        
        this.createEmotionalLandscapeChart({
            labels: ['Curious', 'Analytical', 'Optimistic', 'Thoughtful'],
            values: [30, 25, 25, 20]
        });
        
        // Update statuses to indicate placeholder data
        this.updateChartStatus('core-values-status', 'Sample data', 'placeholder');
        this.updateChartStatus('recurring-themes-status', 'Sample data', 'placeholder');
        this.updateChartStatus('emotional-landscape-status', 'Sample data', 'placeholder');
    }
    
    /**
     * Refresh all charts
     */
    refreshCharts() {
        console.log('Refreshing all charts');
        this.updateChartsWithMemoryData();
    }
    
    /**
     * Destroy all charts and cleanup
     */
    destroy() {
        // Unregister charts from performance optimizer
        if (window.performanceOptimizer) {
            Object.keys(this.charts).forEach(chartId => {
                window.performanceOptimizer.unregisterChart(chartId);
            });
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        this.charts = {};
        this.isInitialized = false;
        console.log('CognitiveChartManager destroyed');
    }
    
    /**
     * Optimize chart update using performance optimizer
     */
    optimizeChartUpdate(chartId, chart, newData) {
        if (window.performanceOptimizer) {
            window.performanceOptimizer.optimizeChartUpdate(chart, newData);
        } else {
            // Fallback to direct update
            if (chart && typeof chart.update === 'function') {
                chart.data = newData;
                chart.update('none');
            }
        }
    }
    
    /**
     * Register chart with performance optimizer
     */
    registerChartWithOptimizer(chartId, chart) {
        if (window.performanceOptimizer) {
            window.performanceOptimizer.registerChart(chartId, chart);
        }
    }
}

// Export for use in other modules
window.CognitiveChartManager = CognitiveChartManager;