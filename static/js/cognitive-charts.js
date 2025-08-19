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
        
        this.createChartContainers();
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
     * Create chart container elements in the dashboard
     */
    createChartContainers() {
        const chartsSection = document.querySelector('.charts-section');
        if (!chartsSection) {
            console.warn('Charts section not found in dashboard');
            return;
        }
        
        // Replace placeholder with actual chart containers
        const chartPlaceholder = chartsSection.querySelector('.chart-placeholder');
        if (chartPlaceholder) {
            chartPlaceholder.remove();
        }
        
        const chartContainersHTML = `
            <div class="charts-grid">
                <!-- Core Values Radar Chart -->
                <div class="chart-container glass-panel" id="core-values-container">
                    <div class="chart-header">
                        <h4 class="chart-title">Core Values</h4>
                        <div class="chart-status" id="core-values-status">Loading...</div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="core-values-chart" width="300" height="200"></canvas>
                    </div>
                </div>
                
                <!-- Recurring Themes Bar Chart -->
                <div class="chart-container glass-panel" id="recurring-themes-container">
                    <div class="chart-header">
                        <h4 class="chart-title">Recurring Themes</h4>
                        <div class="chart-status" id="recurring-themes-status">Loading...</div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="recurring-themes-chart" width="300" height="200"></canvas>
                    </div>
                </div>
                
                <!-- Emotional Landscape Doughnut Chart -->
                <div class="chart-container glass-panel" id="emotional-landscape-container">
                    <div class="chart-header">
                        <h4 class="chart-title">Emotional Landscape</h4>
                        <div class="chart-status" id="emotional-landscape-status">Loading...</div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="emotional-landscape-chart" width="300" height="200"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        chartsSection.insertAdjacentHTML('beforeend', chartContainersHTML);
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
        
        const chartData = {
            labels: data.labels || ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
            datasets: [{
                label: 'Core Values',
                data: data.values || [3, 4, 5, 4, 3, 4],
                backgroundColor: 'rgba(88, 166, 255, 0.15)',
                borderColor: '#58A6FF',
                borderWidth: 3,
                pointBackgroundColor: '#58A6FF',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 3,
                pointRadius: 8,
                pointHoverBackgroundColor: '#FFFFFF',
                pointHoverBorderColor: '#58A6FF',
                pointHoverBorderWidth: 4,
                pointHoverRadius: 12,
                tension: 0.1
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
                            color: 'rgba(88, 166, 255, 0.3)',
                            lineWidth: 1
                        },
                        grid: { 
                            color: 'rgba(88, 166, 255, 0.2)',
                            lineWidth: 1
                        },
                        pointLabels: { 
                            color: '#C9D1D9',
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 12,
                                weight: '600'
                            },
                            padding: 8
                        },
                        ticks: { 
                            color: 'rgba(201, 209, 217, 0.6)',
                            backdropColor: 'transparent',
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
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
        
        // Create gradient colors for bars based on frequency
        const gradientColors = frequencies.map((freq, index) => {
            const intensity = freq / Math.max(...frequencies);
            const alpha = 0.6 + (intensity * 0.4); // Range from 0.6 to 1.0
            return `rgba(88, 166, 255, ${alpha})`;
        });
        
        const hoverColors = frequencies.map((freq, index) => {
            const intensity = freq / Math.max(...frequencies);
            const alpha = 0.8 + (intensity * 0.2); // Range from 0.8 to 1.0
            return `rgba(88, 166, 255, ${alpha})`;
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
                        borderColor: '#58A6FF',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                        hoverBackgroundColor: hoverColors,
                        hoverBorderColor: '#FFFFFF',
                        hoverBorderWidth: 3,
                        hoverBorderRadius: 8,
                        // Enhanced bar styling
                        barThickness: 'flex',
                        maxBarThickness: 40,
                        minBarLength: 2
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
                                color: 'rgba(88, 166, 255, 0.1)',
                                borderColor: 'rgba(88, 166, 255, 0.3)',
                                lineWidth: 1
                            },
                            ticks: {
                                color: '#C9D1D9',
                                font: {
                                    family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
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
                                    family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
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
                                    family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
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
                                    family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
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
        
        // Enhanced color palette with HUD theme variations
        const emotionalColors = [
            '#58A6FF',  // Primary Cyan - Curious
            '#7C3AED',  // Purple - Analytical  
            '#10B981',  // Emerald - Optimistic
            '#F59E0B',  // Amber - Thoughtful
            '#EF4444',  // Red - Creative
            '#8B5CF6',  // Violet - Empathetic
            '#06B6D4',  // Cyan variant
            '#EC4899',  // Pink variant
            '#84CC16',  // Lime variant
            '#F97316'   // Orange variant
        ];
        
        // Create gradient colors based on intensity
        const backgroundColors = values.map((value, index) => {
            const baseColor = emotionalColors[index % emotionalColors.length];
            const intensity = value / Math.max(...values);
            const alpha = 0.7 + (intensity * 0.3); // Range from 0.7 to 1.0
            return this.hexToRgba(baseColor, alpha);
        });
        
        const hoverColors = values.map((value, index) => {
            const baseColor = emotionalColors[index % emotionalColors.length];
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
                        borderColor: emotionalColors.slice(0, values.length),
                        borderWidth: 3,
                        hoverBackgroundColor: hoverColors,
                        hoverBorderColor: '#FFFFFF',
                        hoverBorderWidth: 4,
                        hoverOffset: 12,
                        // Enhanced segment styling
                        borderRadius: 4,
                        borderJoinStyle: 'round'
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
     * Process memory data into chart-ready formats
     */
    processMemoryDataForCharts(memoryData) {
        const insights = memoryData.insights || [];
        const statistics = memoryData.statistics || {};
        
        // Core Values processing
        const coreValues = this.extractCoreValues(insights, statistics);
        
        // Recurring Themes processing
        const themes = this.extractRecurringThemes(insights, statistics);
        
        // Emotional Landscape processing
        const emotions = this.extractEmotionalData(insights, statistics);
        
        return {
            coreValues: {
                labels: ['Creativity', 'Stability', 'Learning', 'Curiosity', 'Analysis', 'Empathy'],
                values: coreValues
            },
            recurringThemes: {
                labels: themes.map(t => t.theme),
                frequencies: themes.map(t => t.frequency)
            },
            emotionalLandscape: {
                labels: emotions.map(e => e.emotion),
                values: emotions.map(e => e.intensity)
            }
        };
    }
    
    /**
     * Extract core values from insights data with enhanced analysis
     */
    extractCoreValues(insights, statistics) {
        // Default values if no data available
        const defaultValues = [3, 4, 5, 4, 3, 4];
        
        if (!insights || insights.length === 0) {
            return defaultValues;
        }
        
        // Enhanced keyword analysis with weighted terms and context
        const valueKeywords = {
            creativity: {
                primary: ['creative', 'innovation', 'artistic', 'imagination', 'original', 'design', 'invent'],
                secondary: ['unique', 'novel', 'brainstorm', 'inspire', 'vision', 'aesthetic', 'craft'],
                context: ['art', 'music', 'writing', 'problem-solving', 'ideas']
            },
            stability: {
                primary: ['stable', 'consistent', 'reliable', 'steady', 'secure', 'predictable'],
                secondary: ['routine', 'structure', 'organized', 'methodical', 'systematic', 'planned'],
                context: ['schedule', 'habit', 'process', 'framework', 'foundation']
            },
            learning: {
                primary: ['learn', 'study', 'knowledge', 'education', 'growth', 'understand'],
                secondary: ['research', 'explore', 'discover', 'master', 'skill', 'develop'],
                context: ['course', 'book', 'tutorial', 'practice', 'improvement']
            },
            curiosity: {
                primary: ['curious', 'explore', 'discover', 'question', 'wonder', 'investigate'],
                secondary: ['why', 'how', 'what if', 'experiment', 'probe', 'inquire'],
                context: ['mystery', 'unknown', 'possibility', 'adventure', 'exploration']
            },
            analysis: {
                primary: ['analyze', 'logical', 'systematic', 'rational', 'critical', 'evaluate'],
                secondary: ['data', 'evidence', 'reason', 'logic', 'method', 'objective'],
                context: ['research', 'statistics', 'comparison', 'assessment', 'judgment']
            },
            empathy: {
                primary: ['empathy', 'understanding', 'compassion', 'caring', 'emotional', 'support'],
                secondary: ['help', 'listen', 'feel', 'connect', 'relate', 'comfort'],
                context: ['relationship', 'friendship', 'community', 'kindness', 'sensitivity']
            }
        };
        
        const values = [];
        const totalInsights = insights.length;
        
        Object.keys(valueKeywords).forEach(value => {
            const keywords = valueKeywords[value];
            let score = 0;
            let matchCount = 0;
            
            insights.forEach(insight => {
                const content = (insight.content || '').toLowerCase();
                const evidence = (insight.evidence || '').toLowerCase();
                const tags = (insight.tags || []).map(tag => tag.toLowerCase());
                const confidence = insight.confidence || 0.5;
                
                let insightScore = 0;
                
                // Primary keywords (higher weight)
                keywords.primary.forEach(keyword => {
                    if (content.includes(keyword) || evidence.includes(keyword)) {
                        insightScore += 1.0 * confidence;
                        matchCount++;
                    }
                    if (tags.some(tag => tag.includes(keyword))) {
                        insightScore += 0.8 * confidence;
                        matchCount++;
                    }
                });
                
                // Secondary keywords (medium weight)
                keywords.secondary.forEach(keyword => {
                    if (content.includes(keyword) || evidence.includes(keyword)) {
                        insightScore += 0.6 * confidence;
                        matchCount++;
                    }
                    if (tags.some(tag => tag.includes(keyword))) {
                        insightScore += 0.4 * confidence;
                        matchCount++;
                    }
                });
                
                // Context keywords (lower weight)
                keywords.context.forEach(keyword => {
                    if (content.includes(keyword) || evidence.includes(keyword)) {
                        insightScore += 0.3 * confidence;
                    }
                    if (tags.some(tag => tag.includes(keyword))) {
                        insightScore += 0.2 * confidence;
                    }
                });
                
                score += insightScore;
            });
            
            // Calculate normalized score with frequency consideration
            let normalizedScore;
            if (matchCount === 0) {
                // No matches found, use baseline
                normalizedScore = 2.5;
            } else {
                // Scale based on match frequency and total score
                const frequency = matchCount / totalInsights;
                const avgScore = score / Math.max(matchCount, 1);
                
                // Combine frequency and average score
                const combinedScore = (frequency * 2) + (avgScore * 3);
                
                // Normalize to 1-5 scale with some baseline
                normalizedScore = Math.min(5, Math.max(1, 1.5 + (combinedScore * 0.7)));
            }
            
            values.push(Math.round(normalizedScore * 10) / 10); // Round to 1 decimal place
        });
        
        // Ensure we have exactly 6 values
        if (values.length !== 6) {
            console.warn('Core values extraction returned unexpected number of values:', values.length);
            return defaultValues;
        }
        
        console.log('Extracted core values:', {
            creativity: values[0],
            stability: values[1],
            learning: values[2],
            curiosity: values[3],
            analysis: values[4],
            empathy: values[5]
        });
        
        return values;
    }
    
    /**
     * Extract recurring themes from insights data with enhanced analysis
     */
    extractRecurringThemes(insights, statistics) {
        const categories = statistics.categories || {};
        
        // If we have category statistics, use them as primary source
        if (Object.keys(categories).length > 0) {
            const categoryThemes = Object.entries(categories)
                .map(([category, count]) => ({
                    theme: category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    frequency: count
                }))
                .sort((a, b) => b.frequency - a.frequency)
                .slice(0, 8); // Get top 8 from categories
            
            if (categoryThemes.length >= 4) {
                return categoryThemes.slice(0, 6); // Return top 6
            }
        }
        
        // Enhanced theme extraction from insights content
        if (!insights || insights.length === 0) {
            return [
                { theme: 'Technology', frequency: 8 },
                { theme: 'Philosophy', frequency: 6 },
                { theme: 'Learning', frequency: 7 },
                { theme: 'Creativity', frequency: 5 }
            ];
        }
        
        // Define comprehensive theme keywords with weighted scoring
        const themeKeywords = {
            'Technology': {
                primary: ['technology', 'programming', 'software', 'computer', 'digital', 'ai', 'artificial intelligence', 'machine learning', 'algorithm', 'code', 'coding', 'development', 'tech'],
                secondary: ['app', 'website', 'internet', 'online', 'cyber', 'data', 'database', 'system', 'platform', 'framework', 'api', 'cloud'],
                context: ['innovation', 'automation', 'efficiency', 'optimization', 'integration', 'scalability']
            },
            'Philosophy': {
                primary: ['philosophy', 'ethics', 'moral', 'meaning', 'existence', 'consciousness', 'reality', 'truth', 'wisdom', 'belief', 'value', 'principle'],
                secondary: ['think', 'thought', 'idea', 'concept', 'theory', 'perspective', 'viewpoint', 'opinion', 'debate', 'argument'],
                context: ['life', 'purpose', 'society', 'human nature', 'free will', 'determinism', 'metaphysics']
            },
            'Learning': {
                primary: ['learn', 'learning', 'education', 'study', 'knowledge', 'skill', 'training', 'course', 'lesson', 'teach', 'instruction'],
                secondary: ['understand', 'comprehend', 'grasp', 'master', 'practice', 'exercise', 'tutorial', 'guide', 'method', 'technique'],
                context: ['improvement', 'development', 'growth', 'progress', 'achievement', 'competency']
            },
            'Creativity': {
                primary: ['creative', 'creativity', 'art', 'artistic', 'design', 'imagination', 'innovative', 'original', 'inspiration', 'aesthetic'],
                secondary: ['draw', 'paint', 'write', 'compose', 'create', 'craft', 'build', 'make', 'express', 'style'],
                context: ['beauty', 'visual', 'music', 'literature', 'poetry', 'storytelling', 'performance']
            },
            'Science': {
                primary: ['science', 'scientific', 'research', 'experiment', 'hypothesis', 'theory', 'discovery', 'analysis', 'method', 'evidence'],
                secondary: ['biology', 'chemistry', 'physics', 'mathematics', 'psychology', 'sociology', 'medicine', 'health'],
                context: ['observation', 'measurement', 'data', 'statistics', 'correlation', 'causation']
            },
            'Personal': {
                primary: ['personal', 'self', 'identity', 'personality', 'character', 'emotion', 'feeling', 'relationship', 'family', 'friend'],
                secondary: ['growth', 'development', 'improvement', 'goal', 'dream', 'aspiration', 'challenge', 'struggle'],
                context: ['happiness', 'success', 'fulfillment', 'satisfaction', 'well-being', 'mental health']
            },
            'Business': {
                primary: ['business', 'work', 'job', 'career', 'professional', 'company', 'organization', 'management', 'leadership', 'strategy'],
                secondary: ['market', 'customer', 'client', 'service', 'product', 'sales', 'marketing', 'finance', 'profit'],
                context: ['entrepreneurship', 'startup', 'innovation', 'competition', 'growth', 'success']
            },
            'Entertainment': {
                primary: ['movie', 'film', 'book', 'game', 'music', 'show', 'entertainment', 'fun', 'hobby', 'leisure'],
                secondary: ['watch', 'read', 'play', 'listen', 'enjoy', 'relax', 'recreation', 'activity'],
                context: ['story', 'character', 'plot', 'genre', 'comedy', 'drama', 'adventure']
            }
        };
        
        const themeScores = {};
        const totalInsights = insights.length;
        
        // Initialize theme scores
        Object.keys(themeKeywords).forEach(theme => {
            themeScores[theme] = 0;
        });
        
        // Analyze each insight for theme indicators
        insights.forEach(insight => {
            const content = (insight.content || '').toLowerCase();
            const evidence = (insight.evidence || '').toLowerCase();
            const tags = (insight.tags || []).map(tag => tag.toLowerCase());
            const confidence = insight.confidence || 0.5;
            
            Object.entries(themeKeywords).forEach(([theme, keywords]) => {
                let themeScore = 0;
                
                // Primary keywords (highest weight)
                keywords.primary.forEach(keyword => {
                    if (content.includes(keyword)) themeScore += 1.0 * confidence;
                    if (evidence.includes(keyword)) themeScore += 0.8 * confidence;
                    if (tags.some(tag => tag.includes(keyword))) themeScore += 0.9 * confidence;
                });
                
                // Secondary keywords (medium weight)
                keywords.secondary.forEach(keyword => {
                    if (content.includes(keyword)) themeScore += 0.6 * confidence;
                    if (evidence.includes(keyword)) themeScore += 0.5 * confidence;
                    if (tags.some(tag => tag.includes(keyword))) themeScore += 0.4 * confidence;
                });
                
                // Context keywords (lower weight)
                keywords.context.forEach(keyword => {
                    if (content.includes(keyword)) themeScore += 0.3 * confidence;
                    if (evidence.includes(keyword)) themeScore += 0.2 * confidence;
                    if (tags.some(tag => tag.includes(keyword))) themeScore += 0.2 * confidence;
                });
                
                themeScores[theme] += themeScore;
            });
        });
        
        // Convert scores to frequencies and filter meaningful themes
        const themes = Object.entries(themeScores)
            .map(([theme, score]) => {
                // Convert score to frequency (approximate number of discussions)
                const frequency = Math.max(1, Math.round(score * 2)); // Scale factor for readability
                return { theme, frequency, rawScore: score };
            })
            .filter(item => item.rawScore > 0.5) // Only include themes with meaningful presence
            .sort((a, b) => b.frequency - a.frequency)
            .slice(0, 6); // Limit to top 6 themes
        
        // Ensure we have at least 4 themes for a meaningful chart
        if (themes.length < 4) {
            const defaultThemes = [
                { theme: 'Technology', frequency: 8 },
                { theme: 'Philosophy', frequency: 6 },
                { theme: 'Learning', frequency: 7 },
                { theme: 'Creativity', frequency: 5 }
            ];
            
            // Merge with extracted themes, avoiding duplicates
            const existingThemes = themes.map(t => t.theme);
            const additionalThemes = defaultThemes.filter(t => !existingThemes.includes(t.theme));
            
            return [...themes, ...additionalThemes].slice(0, 6);
        }
        
        console.log('Extracted recurring themes:', themes.map(t => `${t.theme}: ${t.frequency}`));
        
        return themes;
    }
    
    /**
     * Extract emotional data from insights
     */
    extractEmotionalData(insights, statistics) {
        // Default emotional distribution if no data available
        const defaultEmotions = [
            { emotion: 'Curious', intensity: 30 },
            { emotion: 'Analytical', intensity: 25 },
            { emotion: 'Optimistic', intensity: 25 },
            { emotion: 'Thoughtful', intensity: 20 }
        ];
        
        if (!insights || insights.length === 0) {
            return defaultEmotions;
        }
        
        // Analyze insights for emotional indicators
        const emotionKeywords = {
            curious: ['curious', 'wonder', 'explore', 'discover'],
            analytical: ['analyze', 'logical', 'systematic', 'rational'],
            optimistic: ['positive', 'hopeful', 'optimistic', 'confident'],
            thoughtful: ['thoughtful', 'reflective', 'contemplative', 'mindful'],
            excited: ['excited', 'enthusiastic', 'passionate', 'energetic'],
            concerned: ['worried', 'concerned', 'anxious', 'uncertain']
        };
        
        const emotionScores = {};
        
        Object.keys(emotionKeywords).forEach(emotion => {
            const keywords = emotionKeywords[emotion];
            let score = 0;
            
            insights.forEach(insight => {
                const content = (insight.content || '').toLowerCase();
                keywords.forEach(keyword => {
                    if (content.includes(keyword)) {
                        score += insight.confidence || 0.5;
                    }
                });
            });
            
            emotionScores[emotion] = score;
        });
        
        // Convert to percentage distribution
        const totalScore = Object.values(emotionScores).reduce((sum, score) => sum + score, 0);
        
        if (totalScore === 0) {
            return defaultEmotions;
        }
        
        return Object.entries(emotionScores)
            .map(([emotion, score]) => ({
                emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
                intensity: Math.round((score / totalScore) * 100)
            }))
            .filter(item => item.intensity > 0)
            .sort((a, b) => b.intensity - a.intensity)
            .slice(0, 6); // Limit to top 6 emotions
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