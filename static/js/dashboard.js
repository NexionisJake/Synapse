/**
 * Dashboard JavaScript for Synapse AI Web Application
 * 
 * Handles interactive insight browsing, filtering, and visualization
 */

class Dashboard {
    constructor() {
        this.insights = [];
        this.summaries = [];
        this.statistics = {};
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.filteredInsights = [];
        this.chartManager = null;

        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeChartManager();
        this.ensureBackwardCompatibility();
        this.loadDashboardData();
        this.setupAutomaticChartUpdates();
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
    }

    initializeChartManager() {
        // Initialize chart manager if CognitiveChartManager is available
        if (typeof CognitiveChartManager !== 'undefined') {
            // Check if chart manager already exists globally to avoid duplicates
            if (window.globalChartManager) {
                this.chartManager = window.globalChartManager;
                console.log('Using existing global chart manager');
            } else {
                this.chartManager = new CognitiveChartManager();
                this.chartManager.init();
                window.globalChartManager = this.chartManager;
                console.log('Chart manager initialized');
            }
        } else {
            console.warn('CognitiveChartManager not available');
        }
    }

    bindEvents() {
        // Retry button
        const retryButton = document.getElementById('retry-button');
        if (retryButton) {
            retryButton.addEventListener('click', () => this.loadDashboardData());
        }

        // Filter controls
        const categoryFilter = document.getElementById('category-filter');
        const confidenceFilter = document.getElementById('confidence-filter');

        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => this.applyFilters());
        }

        if (confidenceFilter) {
            confidenceFilter.addEventListener('change', () => this.applyFilters());
        }

        // Pagination controls
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');

        if (prevButton) {
            prevButton.addEventListener('click', () => this.previousPage());
        }

        if (nextButton) {
            nextButton.addEventListener('click', () => this.nextPage());
        }

        // Serendipity engine
        const discoverButton = document.getElementById('discover-connections');
        if (discoverButton) {
            discoverButton.addEventListener('click', () => this.discoverConnections());
        }

        // Dashboard refresh button
        const refreshButton = document.getElementById('refresh-dashboard');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.refreshDashboard());
        }

        // Charts refresh button
        const refreshChartsButton = document.getElementById('refresh-charts');
        if (refreshChartsButton) {
            refreshChartsButton.addEventListener('click', () => this.refreshCharts());
        }
    }

    async loadDashboardData() {
        try {
            this.showLoadingState();

            const response = await fetch('/api/insights');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.message || 'Unknown error occurred');
            }

            this.insights = data.insights || [];
            this.summaries = data.conversation_summaries || [];
            this.statistics = data.statistics || {};

            if (this.insights.length === 0 && this.summaries.length === 0) {
                this.showEmptyState();
            } else {
                this.showDashboardContent();
                this.renderDashboard();
                this.updateCharts();
            }

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showErrorState(error.message);
        }
    }

    showLoadingState() {
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const emptyState = document.getElementById('empty-state');
        const dashboardContent = document.getElementById('dashboard-content') || document.getElementById('dashboard-content-inner');

        if (loadingState) loadingState.style.display = 'flex';
        if (errorState) errorState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'none';
        if (dashboardContent) dashboardContent.style.display = 'none';
    }

    showErrorState(message) {
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const emptyState = document.getElementById('empty-state');
        const dashboardContent = document.getElementById('dashboard-content') || document.getElementById('dashboard-content-inner');

        if (loadingState) loadingState.style.display = 'none';
        if (errorState) errorState.style.display = 'flex';
        if (emptyState) emptyState.style.display = 'none';
        if (dashboardContent) dashboardContent.style.display = 'none';

        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = message;
        }
    }

    showEmptyState() {
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const emptyState = document.getElementById('empty-state');
        const dashboardContent = document.getElementById('dashboard-content') || document.getElementById('dashboard-content-inner');

        if (loadingState) loadingState.style.display = 'none';
        if (errorState) errorState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'flex';
        if (dashboardContent) dashboardContent.style.display = 'none';
    }

    showDashboardContent() {
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const emptyState = document.getElementById('empty-state');
        const dashboardContent = document.getElementById('dashboard-content-inner') || document.getElementById('dashboard-content');

        if (loadingState) loadingState.style.display = 'none';
        if (errorState) errorState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'none';
        if (dashboardContent) dashboardContent.style.display = 'block';
        
        // Ensure charts are properly initialized in the integrated layout
        this.ensureChartsInitialized();
    }

    /**
     * Ensure charts are properly initialized in the integrated dashboard layout
     */
    ensureChartsInitialized() {
        if (this.chartManager && !this.chartManager.isInitialized) {
            this.chartManager.init();
        }
        
        // Check if chart containers exist, if not create them
        const chartsSection = document.querySelector('.charts-section');
        if (chartsSection && !chartsSection.querySelector('.charts-grid')) {
            this.createIntegratedChartContainers();
        }
    }

    /**
     * Create chart containers for the integrated dashboard layout
     */
    createIntegratedChartContainers() {
        const chartsSection = document.querySelector('.charts-section');
        if (!chartsSection) return;

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

    renderDashboard() {
        this.renderStatistics();
        this.renderCategories();
        this.renderConfidenceDistribution();
        this.renderInsights();
        this.renderSummaries();
        this.setupFilters();
    }

    renderStatistics() {
        const stats = this.statistics;

        // Update stat cards
        this.updateElement('total-insights', stats.total_insights || 0);
        this.updateElement('total-conversations', stats.total_conversations || 0);
        this.updateElement('categories-count', Object.keys(stats.categories || {}).length);

        // Format last updated date
        const lastUpdated = stats.last_updated;
        if (lastUpdated) {
            const date = new Date(lastUpdated);
            const formatted = this.formatRelativeTime(date);
            this.updateElement('last-updated', formatted);
        } else {
            this.updateElement('last-updated', 'Never');
        }
    }

    renderCategories() {
        const container = document.getElementById('categories-container');
        if (!container) return;

        const categories = this.statistics.categories || {};

        if (Object.keys(categories).length === 0) {
            container.innerHTML = '<p class="no-data">No categories available yet.</p>';
            return;
        }

        const categoryCards = Object.entries(categories)
            .sort(([, a], [, b]) => b - a) // Sort by count descending
            .map(([category, count]) => {
                const description = this.getCategoryDescription(category);
                return `
                    <div class="category-card">
                        <div class="category-name">${category.replace(/_/g, ' ')}</div>
                        <div class="category-count">${count} insight${count !== 1 ? 's' : ''}</div>
                        <div class="category-description">${description}</div>
                    </div>
                `;
            }).join('');

        container.innerHTML = categoryCards;
    }

    renderConfidenceDistribution() {
        const confidence = this.statistics.confidence_distribution || {};
        const total = confidence.high + confidence.medium + confidence.low || 1;

        // Update counts
        this.updateElement('high-confidence-count', confidence.high || 0);
        this.updateElement('medium-confidence-count', confidence.medium || 0);
        this.updateElement('low-confidence-count', confidence.low || 0);

        // Update progress bars
        const highPercent = ((confidence.high || 0) / total) * 100;
        const mediumPercent = ((confidence.medium || 0) / total) * 100;
        const lowPercent = ((confidence.low || 0) / total) * 100;

        this.updateProgressBar('high-confidence-bar', highPercent);
        this.updateProgressBar('medium-confidence-bar', mediumPercent);
        this.updateProgressBar('low-confidence-bar', lowPercent);
    }

    renderInsights() {
        this.filteredInsights = [...this.insights];
        this.applyFilters();
    }

    renderSummaries() {
        const container = document.getElementById('summaries-container');
        if (!container) return;

        if (this.summaries.length === 0) {
            container.innerHTML = '<p class="no-data">No conversation summaries available yet.</p>';
            return;
        }

        const summaryCards = this.summaries
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 5) // Show only recent 5 summaries
            .map(summary => {
                const date = new Date(summary.timestamp);
                const themes = summary.key_themes || [];

                return `
                    <div class="summary-card">
                        <div class="summary-header">
                            <div class="summary-timestamp">${this.formatDate(date)}</div>
                            <div class="summary-insights-count">${summary.insights_count || 0} insights</div>
                        </div>
                        <div class="summary-content">${summary.summary}</div>
                        ${themes.length > 0 ? `
                            <div class="summary-themes">
                                ${themes.map(theme => `<span class="summary-theme">${theme}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');

        container.innerHTML = summaryCards;
    }

    setupFilters() {
        // Populate category filter
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            const categories = [...new Set(this.insights.map(insight => insight.category))].sort();
            const options = categories.map(category =>
                `<option value="${category}">${category.replace(/_/g, ' ')}</option>`
            ).join('');

            categoryFilter.innerHTML = '<option value="">All Categories</option>' + options;
        }
    }

    applyFilters() {
        const categoryFilter = document.getElementById('category-filter');
        const confidenceFilter = document.getElementById('confidence-filter');

        const selectedCategory = categoryFilter ? categoryFilter.value : '';
        const selectedConfidence = confidenceFilter ? confidenceFilter.value : '';

        this.filteredInsights = this.insights.filter(insight => {
            // Category filter
            if (selectedCategory && insight.category !== selectedCategory) {
                return false;
            }

            // Confidence filter
            if (selectedConfidence) {
                const confidence = insight.confidence || 0;
                if (selectedConfidence === 'high' && confidence < 0.8) return false;
                if (selectedConfidence === 'medium' && (confidence < 0.5 || confidence >= 0.8)) return false;
                if (selectedConfidence === 'low' && confidence >= 0.5) return false;
            }

            return true;
        });

        this.currentPage = 1;
        this.renderInsightsList();
        this.updatePagination();
    }

    renderInsightsList() {
        const container = document.getElementById('insights-container');
        if (!container) return;

        if (this.filteredInsights.length === 0) {
            container.innerHTML = '<p class="no-data">No insights match the current filters.</p>';
            return;
        }

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageInsights = this.filteredInsights.slice(startIndex, endIndex);

        const insightCards = pageInsights.map(insight => {
            const date = new Date(insight.timestamp);
            const confidence = Math.round((insight.confidence || 0) * 100);
            const tags = insight.tags || [];

            return `
                <div class="insight-card">
                    <div class="insight-header">
                        <span class="insight-category">${insight.category.replace(/_/g, ' ')}</span>
                        <span class="insight-confidence">${confidence}% confidence</span>
                    </div>
                    <div class="insight-content">${insight.content}</div>
                    ${tags.length > 0 ? `
                        <div class="insight-tags">
                            ${tags.map(tag => `<span class="insight-tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                    ${insight.evidence ? `
                        <div class="insight-evidence">"${insight.evidence}"</div>
                    ` : ''}
                    <div class="insight-timestamp">${this.formatDate(date)}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = insightCards;
    }

    updatePagination() {
        const totalPages = Math.ceil(this.filteredInsights.length / this.itemsPerPage);
        const pagination = document.getElementById('insights-pagination');

        if (!pagination) {
            console.log('Pagination element not found, skipping pagination update');
            return;
        }

        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';

        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');

        if (prevButton) {
            prevButton.disabled = this.currentPage === 1;
        }

        if (nextButton) {
            nextButton.disabled = this.currentPage === totalPages;
        }

        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        }
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderInsightsList();
            this.updatePagination();
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.filteredInsights.length / this.itemsPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderInsightsList();
            this.updatePagination();
        }
    }

    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateProgressBar(id, percentage) {
        const element = document.getElementById(id);
        if (element) {
            element.style.width = `${percentage}%`;
        }
    }

    formatDate(date) {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;

        return this.formatDate(date);
    }

    getCategoryDescription(category) {
        const descriptions = {
            'interests': 'Topics and subjects that capture your attention',
            'preferences': 'Your likes, dislikes, and personal choices',
            'thinking_patterns': 'How you approach problems and process information',
            'goals': 'Your aspirations and objectives',
            'concerns': 'Issues and challenges you\'re facing',
            'values': 'Principles and beliefs that guide your decisions',
            'learning_style': 'How you prefer to learn and understand new concepts',
            'communication': 'Your communication preferences and patterns',
            'personality': 'Traits and characteristics that define your personality',
            'skills': 'Abilities and competencies you possess or want to develop'
        };

        return descriptions[category] || 'Insights about your thoughts and behaviors';
    }

    // Serendipity Engine Methods
    async discoverConnections() {
        const button = document.getElementById('discover-connections');
        const status = document.getElementById('serendipity-status');
        const results = document.getElementById('serendipity-results');

        if (!button || !status) return;

        try {
            // Update UI to loading state
            button.disabled = true;
            button.classList.add('loading');
            status.textContent = 'Analyzing your memory for unexpected connections...';
            status.className = 'serendipity-status loading';

            if (results) {
                results.style.display = 'none';
            }

            // Make API call to serendipity endpoint
            const response = await fetch('/api/serendipity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.message || 'Unknown error occurred');
            }

            // Update UI with results
            this.renderSerendipityResults(data);
            status.textContent = 'Connections discovered! Explore the unexpected patterns below.';
            status.className = 'serendipity-status success';

        } catch (error) {
            console.error('Error discovering connections:', error);
            status.textContent = `Error: ${error.message}`;
            status.className = 'serendipity-status error';

            // Show empty results with error message
            this.renderSerendipityError(error.message);
        } finally {
            // Reset button state
            button.disabled = false;
            button.classList.remove('loading');
        }
    }

    renderSerendipityResults(data) {
        const results = document.getElementById('serendipity-results');
        if (!results) return;

        // Update summary
        const summaryText = document.getElementById('serendipity-summary-text');
        if (summaryText) {
            summaryText.textContent = data.serendipity_summary || 'No summary available.';
        }

        // Render connections
        this.renderConnections(data.connections || []);

        // Render meta patterns
        this.renderMetaPatterns(data.meta_patterns || []);

        // Render recommendations
        this.renderRecommendations(data.recommendations || []);

        // Show results
        results.style.display = 'block';
    }

    renderConnections(connections) {
        const container = document.getElementById('connections-list');
        if (!container) return;

        if (connections.length === 0) {
            container.innerHTML = `
                <div class="serendipity-empty">
                    <div class="serendipity-empty-icon">🔍</div>
                    <h4>No unexpected connections found</h4>
                    <p>Keep having diverse conversations to build more connections!</p>
                </div>
            `;
            return;
        }

        const connectionCards = connections.map(connection => {
            const surpriseFactor = (connection.surprise_factor || 0) * 100;
            const relevance = (connection.relevance || 0) * 100;
            const connectedInsights = connection.connected_insights || [];

            return `
                <div class="connection-card">
                    <div class="connection-header">
                        <h4 class="connection-title">${connection.title || 'Untitled Connection'}</h4>
                        <div class="connection-metrics">
                            <div class="connection-metric">
                                <span>Surprise:</span>
                                <div class="surprise-indicator">
                                    <div class="surprise-fill" style="width: ${surpriseFactor}%"></div>
                                </div>
                            </div>
                            <div class="connection-metric">
                                <span>Relevance:</span>
                                <div class="relevance-indicator">
                                    <div class="relevance-fill" style="width: ${relevance}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="connection-type">${connection.connection_type || 'pattern'}</div>
                    <div class="connection-description">${connection.description || 'No description available.'}</div>
                    ${connection.actionable_insight ? `
                        <div class="connection-insight">
                            <strong>Actionable Insight:</strong> ${connection.actionable_insight}
                        </div>
                    ` : ''}
                    ${connectedInsights.length > 0 ? `
                        <div class="connected-insights">
                            ${connectedInsights.map(insight => `<span class="connected-insight-tag">${insight}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

        container.innerHTML = connectionCards;
    }

    renderMetaPatterns(patterns) {
        const container = document.getElementById('meta-patterns-list');
        if (!container) return;

        if (patterns.length === 0) {
            container.innerHTML = `
                <div class="serendipity-empty">
                    <div class="serendipity-empty-icon">🧩</div>
                    <h4>No overarching patterns detected</h4>
                    <p>More conversations will help reveal deeper patterns in your thinking.</p>
                </div>
            `;
            return;
        }

        const patternCards = patterns.map(pattern => {
            const confidence = Math.round((pattern.confidence || 0) * 100);

            return `
                <div class="meta-pattern-card">
                    <div class="meta-pattern-header">
                        <h4 class="meta-pattern-name">${pattern.pattern_name || 'Unnamed Pattern'}</h4>
                        <div class="meta-pattern-stats">
                            <span class="evidence-count">${pattern.evidence_count || 0} evidence</span>
                            <span class="confidence-score">${confidence}% confidence</span>
                        </div>
                    </div>
                    <div class="meta-pattern-description">${pattern.description || 'No description available.'}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = patternCards;
    }

    renderRecommendations(recommendations) {
        const container = document.getElementById('recommendations-list');
        if (!container) return;

        if (recommendations.length === 0) {
            container.innerHTML = `
                <li>Continue having diverse conversations to discover more connections</li>
                <li>Explore topics that bridge your different interests</li>
                <li>Return to the serendipity engine as your memory grows</li>
            `;
            return;
        }

        const recommendationItems = recommendations.map(rec =>
            `<li>${rec}</li>`
        ).join('');

        container.innerHTML = recommendationItems;
    }

    renderSerendipityError(errorMessage) {
        const results = document.getElementById('serendipity-results');
        if (!results) return;

        // Show basic error state in results
        const summaryText = document.getElementById('serendipity-summary-text');
        if (summaryText) {
            summaryText.textContent = `Unable to analyze connections: ${errorMessage}`;
        }

        // Clear other sections
        this.renderConnections([]);
        this.renderMetaPatterns([]);
        this.renderRecommendations([
            'Please try again later',
            'Ensure you have sufficient conversation history',
            'Check that the AI service is running properly'
        ]);

        // Show results
        results.style.display = 'block';
    }

    // Chart management methods
    updateCharts() {
        if (this.chartManager) {
            this.chartManager.updateChartsWithMemoryData();
        }
    }

    refreshDashboard() {
        console.log('Refreshing dashboard...');
        this.loadDashboardData();
    }

    refreshCharts() {
        console.log('Refreshing charts...');
        if (this.chartManager) {
            this.chartManager.refreshCharts();
        } else {
            console.warn('Chart manager not available for refresh');
        }
    }

    /**
     * Set up automatic chart updates when new insights are generated
     */
    setupAutomaticChartUpdates() {
        // Check for new insights every 30 seconds
        this.chartUpdateInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/insights');
                if (response.ok) {
                    const data = await response.json();
                    const currentInsightCount = data.insights ? data.insights.length : 0;
                    
                    // Check if we have new insights
                    if (this.lastKnownInsightCount !== undefined && 
                        currentInsightCount > this.lastKnownInsightCount) {
                        console.log(`New insights detected: ${currentInsightCount - this.lastKnownInsightCount} new insights`);
                        this.updateCharts();
                        this.renderDashboard(); // Also update the dashboard content
                        
                        // Notify other components about new insights
                        this.notifyInsightUpdate(currentInsightCount - this.lastKnownInsightCount);
                    }
                    
                    this.lastKnownInsightCount = currentInsightCount;
                }
            } catch (error) {
                console.warn('Failed to check for new insights:', error);
            }
        }, 30000); // Check every 30 seconds
    }

    /**
     * Notify other components about insight updates
     */
    notifyInsightUpdate(newInsightCount) {
        // Dispatch custom event for other components to listen to
        document.dispatchEvent(new CustomEvent('insightsUpdated', {
            detail: {
                newInsightCount,
                timestamp: Date.now()
            }
        }));
        
        // Update serendipity engine if available
        if (window.serendipityEngine) {
            window.serendipityEngine.onInsightsUpdated(newInsightCount);
        }
    }

    /**
     * Handle integration with streaming chat responses
     */
    handleStreamingIntegration() {
        // Listen for streaming events from chat interface
        document.addEventListener('streamingCompleted', (event) => {
            const { fullResponse, streamingStats } = event.detail;
            
            // Trigger dashboard update after streaming completes
            setTimeout(() => {
                this.refreshDashboard();
            }, 2000); // Small delay to allow backend processing
        });

        // Listen for new conversation events
        document.addEventListener('conversationUpdated', (event) => {
            // Update dashboard when conversation changes
            this.refreshDashboard();
        });
    }

    /**
     * Ensure backward compatibility with existing API endpoints
     */
    ensureBackwardCompatibility() {
        // Check if we're in the integrated layout or standalone dashboard
        const isIntegratedLayout = document.querySelector('.hud-container') !== null;
        const isStandaloneDashboard = document.querySelector('.container.glass-panel-strong') !== null;
        
        if (isIntegratedLayout) {
            console.log('Dashboard running in integrated two-column layout');
            this.setupIntegratedLayoutFeatures();
        } else if (isStandaloneDashboard) {
            console.log('Dashboard running in standalone mode');
            this.setupStandaloneFeatures();
        }
        
        // Ensure all existing API endpoints continue to work
        this.validateAPIEndpoints();
    }

    /**
     * Setup features specific to integrated layout
     */
    setupIntegratedLayoutFeatures() {
        // Handle streaming integration
        this.handleStreamingIntegration();
        
        // Setup chart refresh when chat updates
        this.setupChatIntegration();
        
        // Ensure serendipity engine works in integrated mode
        this.setupSerendipityIntegration();
    }

    /**
     * Setup features for standalone dashboard
     */
    setupStandaloneFeatures() {
        // Keep existing standalone functionality
        console.log('Maintaining standalone dashboard functionality');
    }

    /**
     * Setup integration with chat interface
     */
    setupChatIntegration() {
        // Listen for chat events that might generate new insights
        document.addEventListener('messageProcessed', () => {
            // Refresh dashboard after message processing
            setTimeout(() => {
                this.loadDashboardData();
            }, 3000);
        });
    }

    /**
     * Setup serendipity engine integration
     */
    setupSerendipityIntegration() {
        // Ensure serendipity engine works with new layout
        const serendipitySection = document.querySelector('.serendipity-section');
        if (serendipitySection && !document.querySelector('.cognitive-dashboard .serendipity-section')) {
            // Move serendipity section to integrated dashboard if needed
            const dashboardContent = document.querySelector('.cognitive-dashboard .dashboard-content');
            if (dashboardContent) {
                // Create a compact version for the integrated layout
                this.createCompactSerendipitySection(dashboardContent);
            }
        }
    }

    /**
     * Create compact serendipity section for integrated layout
     */
    createCompactSerendipitySection(container) {
        const compactSerendipity = document.createElement('section');
        compactSerendipity.className = 'serendipity-section-compact hud-card';
        compactSerendipity.innerHTML = `
            <div class="section-header">
                <h3 class="section-title">Serendipity</h3>
                <button id="discover-connections-compact" class="hud-button secondary compact">
                    <span class="button-icon">🔮</span>
                </button>
            </div>
            <div id="serendipity-status-compact" class="serendipity-status-compact"></div>
            <div id="serendipity-results-compact" class="serendipity-results-compact" style="display: none;">
                <div class="connections-summary"></div>
            </div>
        `;
        
        container.appendChild(compactSerendipity);
        
        // Bind compact serendipity events
        const discoverButton = compactSerendipity.querySelector('#discover-connections-compact');
        if (discoverButton) {
            discoverButton.addEventListener('click', () => this.discoverConnectionsCompact());
        }
    }

    /**
     * Compact version of serendipity discovery for integrated layout
     */
    async discoverConnectionsCompact() {
        const button = document.getElementById('discover-connections-compact');
        const status = document.getElementById('serendipity-status-compact');
        const results = document.getElementById('serendipity-results-compact');

        if (!button || !status) return;

        try {
            button.disabled = true;
            status.textContent = 'Analyzing...';
            status.className = 'serendipity-status-compact loading';

            const response = await fetch('/api/serendipity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.message || 'Unknown error occurred');
            }

            // Show compact results
            this.renderCompactSerendipityResults(data);
            status.textContent = `Found ${data.connections?.length || 0} connections`;
            status.className = 'serendipity-status-compact success';

        } catch (error) {
            console.error('Error discovering connections:', error);
            status.textContent = 'Error occurred';
            status.className = 'serendipity-status-compact error';
        } finally {
            button.disabled = false;
        }
    }

    /**
     * Render compact serendipity results
     */
    renderCompactSerendipityResults(data) {
        const results = document.getElementById('serendipity-results-compact');
        if (!results) return;

        const connections = data.connections || [];
        const summary = document.querySelector('.connections-summary');
        
        if (summary && connections.length > 0) {
            const topConnection = connections[0];
            summary.innerHTML = `
                <div class="compact-connection">
                    <strong>${topConnection.title || 'Connection Found'}</strong>
                    <p>${topConnection.description?.substring(0, 100) || 'No description'}...</p>
                </div>
            `;
        }

        results.style.display = connections.length > 0 ? 'block' : 'none';
    }

    /**
     * Validate that existing API endpoints are working
     */
    async validateAPIEndpoints() {
        const endpoints = ['/api/insights', '/api/serendipity'];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint, { method: 'HEAD' });
                if (!response.ok && response.status !== 405) { // 405 is OK for HEAD on POST endpoints
                    console.warn(`API endpoint ${endpoint} may not be available`);
                }
            } catch (error) {
                console.warn(`Failed to validate endpoint ${endpoint}:`, error);
            }
        }
    }

    /**
     * Clean up automatic updates
     */
    cleanup() {
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
            this.chartUpdateInterval = null;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize dashboard if we have the required elements
    const hasLoadingState = document.getElementById('loading-state');
    const hasDashboardContent = document.getElementById('dashboard-content') || document.getElementById('dashboard-content-inner');

    if (hasLoadingState || hasDashboardContent) {
        new Dashboard();
    } else {
        console.log('Dashboard elements not found, skipping dashboard initialization');
    }
});