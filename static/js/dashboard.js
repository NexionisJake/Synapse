/**
 * Dashboard JavaScript for Synapse AI Web Application
 * 
 * Handles interactive insight browsing, filtering, and visualization
 */

// Custom Error Classes for better error handling
class NetworkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NetworkError';
    }
}

class ServiceUnavailableError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ServiceUnavailableError';
    }
}

class InsufficientDataError extends Error {
    constructor(message) {
        super(message);
        this.name = 'InsufficientDataError';
    }
}

class ServerError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ServerError';
    }
}

class APIError extends Error {
    constructor(message) {
        super(message);
        this.name = 'APIError';
    }
}

class TimeoutError extends Error {
    constructor(message) {
        super(message);
        this.name = 'TimeoutError';
    }
}

// Markdown rendering utilities (shared with chat.js)
const MarkdownRenderer = {
    /**
     * Configure marked.js with secure settings
     */
    configure() {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true, // Convert line breaks to <br>
                gfm: true, // GitHub Flavored Markdown
                sanitize: false, // We'll use DOMPurify for sanitization
                smartLists: true,
                smartypants: false
            });
        }
    },

    /**
     * Convert Markdown text to safe HTML
     * @param {string} markdownText - Raw markdown text from AI
     * @returns {string} Safe HTML string
     */
    render(markdownText) {
        if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') {
            console.warn('Markdown libraries not loaded, falling back to plain text');
            return this.escapeHtml(markdownText);
        }

        try {
            // Parse markdown to HTML
            const rawHtml = marked.parse(markdownText);
            
            // Sanitize HTML to prevent XSS attacks
            const cleanHtml = DOMPurify.sanitize(rawHtml, {
                ALLOWED_TAGS: [
                    'p', 'br', 'strong', 'em', 'u', 'strike', 'del',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'ul', 'ol', 'li',
                    'blockquote', 'pre', 'code',
                    'a', 'span', 'div'
                ],
                ALLOWED_ATTR: ['href', 'target', 'class'],
                ALLOW_DATA_ATTR: false
            });

            return cleanHtml;
        } catch (error) {
            console.error('Markdown rendering error:', error);
            return this.escapeHtml(markdownText);
        }
    },

    /**
     * Escape HTML characters for safe display
     * @param {string} text - Raw text to escape
     * @returns {string} HTML-escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Set content with markdown rendering
     * @param {HTMLElement} element - Target element
     * @param {string} content - Markdown content
     */
    setContent(element, content) {
        const renderedHtml = this.render(content);
        element.innerHTML = renderedHtml;
    }
};

// Initialize markdown renderer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    MarkdownRenderer.configure();
});

class Dashboard {
    static chartManagerInstance = null; // Singleton instance of CognitiveChartManager
    static chartManagerRefCount = 0; // Reference count for proper cleanup
    
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
        this.ensureSerendipityVisibility();
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
    }

    initializeChartManager() {
        // Initialize chart manager if CognitiveChartManager is available
        if (typeof CognitiveChartManager !== 'undefined') {
            // Use static property for cleaner singleton pattern with reference counting
            if (Dashboard.chartManagerInstance) {
                this.chartManager = Dashboard.chartManagerInstance;
                Dashboard.chartManagerRefCount++;
                console.log('Using existing chart manager instance (refs:', Dashboard.chartManagerRefCount, ')');
            } else {
                this.chartManager = new CognitiveChartManager();
                this.chartManager.init();
                Dashboard.chartManagerInstance = this.chartManager;
                Dashboard.chartManagerRefCount = 1;
                console.log('Chart manager initialized (new singleton instance)');
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

        // Serendipity analysis button
        const discoverConnectionsBtn = document.getElementById('discover-connections-btn');
        if (discoverConnectionsBtn) {
            discoverConnectionsBtn.addEventListener('click', () => this.discoverConnections());
        }

        // Keyboard navigation for serendipity button
        if (discoverConnectionsBtn) {
            discoverConnectionsBtn.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.discoverConnections();
                }
            });
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
        const dashboardContent = document.getElementById('dashboard-content-inner');

        if (loadingState) loadingState.style.display = 'flex';
        if (errorState) errorState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'none';
        if (dashboardContent) dashboardContent.style.display = 'none';
    }

    showErrorState(message) {
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const emptyState = document.getElementById('empty-state');
        const dashboardContent = document.getElementById('dashboard-content-inner');

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
        const dashboardContent = document.getElementById('dashboard-content-inner');

        if (loadingState) loadingState.style.display = 'none';
        if (errorState) errorState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'flex';
        if (dashboardContent) dashboardContent.style.display = 'none';
        
        // Enhance empty state with comprehensive onboarding
        this.enhanceEmptyStateWithOnboarding(emptyState);
    }

    /**
     * Enhance empty state with comprehensive onboarding guidance
     */
    enhanceEmptyStateWithOnboarding(emptyStateElement) {
        if (!emptyStateElement) return;
        
        // Check if we've already enhanced this empty state
        if (emptyStateElement.querySelector('.onboarding-enhanced')) return;
        
        const enhancedContent = `
            <div class="onboarding-enhanced">
                <div class="empty-icon">🧠</div>
                <h3 class="hud-text-primary">Welcome to Your Cognitive Dashboard</h3>
                <p class="hud-text-secondary">This is where you'll discover insights and patterns from your conversations.</p>
                
                <div class="onboarding-steps" style="margin: var(--spacing-lg) 0; text-align: left; max-width: 600px;">
                    <h4 class="hud-text-primary" style="margin-bottom: var(--spacing-md); text-align: center;">
                        <span aria-hidden="true">🚀</span> Getting Started
                    </h4>
                    
                    <div class="onboarding-step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <h5>Start Conversations</h5>
                            <p>Chat with the AI about topics you're interested in. Share your thoughts, ask questions, and explore ideas.</p>
                        </div>
                    </div>
                    
                    <div class="onboarding-step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <h5>Build Your Memory</h5>
                            <p>As you chat, the system automatically extracts insights and builds your cognitive memory.</p>
                        </div>
                    </div>
                    
                    <div class="onboarding-step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <h5>Discover Connections</h5>
                            <p>Use the serendipity analysis to find hidden patterns and unexpected connections in your thoughts.</p>
                        </div>
                    </div>
                </div>
                
                <div class="onboarding-features" style="margin: var(--spacing-lg) 0; padding: var(--spacing-md); background: rgba(0, 229, 255, 0.05); border-radius: var(--border-radius);">
                    <h4 class="hud-text-primary" style="margin-bottom: var(--spacing-md);">
                        <span aria-hidden="true">✨</span> What You'll Get
                    </h4>
                    <div class="features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-md);">
                        <div class="feature-item">
                            <div class="feature-icon" aria-hidden="true">📊</div>
                            <h6>Insight Analytics</h6>
                            <p>Track your thinking patterns and interests over time</p>
                        </div>
                        <div class="feature-item">
                            <div class="feature-icon" aria-hidden="true">🔗</div>
                            <h6>Hidden Connections</h6>
                            <p>Discover unexpected relationships between your ideas</p>
                        </div>
                        <div class="feature-item">
                            <div class="feature-icon" aria-hidden="true">🎯</div>
                            <h6>Personal Growth</h6>
                            <p>Gain deeper understanding of your cognitive patterns</p>
                        </div>
                    </div>
                </div>
                
                <div class="onboarding-actions" style="margin-top: var(--spacing-lg);">
                    <a href="/" class="hud-button primary" style="margin-right: var(--spacing-md);">
                        <span class="button-icon">💬</span>
                        Start Your First Conversation
                    </a>
                    <button class="hud-button secondary" onclick="dashboard.showOnboardingTips()">
                        <span class="button-icon">💡</span>
                        Get Tips
                    </button>
                </div>
                
                <div class="onboarding-progress" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); background: rgba(108, 117, 125, 0.05); border-radius: var(--border-radius);">
                    <h5 style="margin-bottom: var(--spacing-sm);">
                        <span aria-hidden="true">📈</span> Your Progress
                    </h5>
                    <div class="progress-item">
                        <span class="progress-icon incomplete" aria-hidden="true">○</span>
                        <span>Have your first conversation</span>
                    </div>
                    <div class="progress-item">
                        <span class="progress-icon incomplete" aria-hidden="true">○</span>
                        <span>Generate your first insights (need 1+ conversations)</span>
                    </div>
                    <div class="progress-item">
                        <span class="progress-icon incomplete" aria-hidden="true">○</span>
                        <span>Try serendipity analysis (need 3+ conversations)</span>
                    </div>
                </div>
            </div>
        `;
        
        emptyStateElement.innerHTML = enhancedContent;
    }

    /**
     * Show onboarding tips modal
     */
    showOnboardingTips() {
        const tipsContent = `
            <div class="onboarding-tips-modal" role="dialog" aria-labelledby="tips-title" aria-modal="true">
                <div class="tips-modal-backdrop" onclick="dashboard.closeOnboardingTips()"></div>
                <div class="tips-modal-content">
                    <div class="tips-modal-header">
                        <h3 id="tips-title">💡 Tips for Better Insights</h3>
                        <button class="tips-modal-close" onclick="dashboard.closeOnboardingTips()" aria-label="Close tips">×</button>
                    </div>
                    <div class="tips-modal-body">
                        <div class="tip-category">
                            <h4>🗣️ Conversation Tips</h4>
                            <ul>
                                <li><strong>Be authentic:</strong> Share your genuine thoughts and feelings</li>
                                <li><strong>Explore diverse topics:</strong> Discuss work, hobbies, philosophy, goals, etc.</li>
                                <li><strong>Ask follow-up questions:</strong> Dive deeper into interesting topics</li>
                                <li><strong>Share context:</strong> Explain why something matters to you</li>
                            </ul>
                        </div>
                        
                        <div class="tip-category">
                            <h4>📊 Building Rich Data</h4>
                            <ul>
                                <li><strong>Regular conversations:</strong> Chat consistently over time</li>
                                <li><strong>Vary your topics:</strong> Mix personal and professional discussions</li>
                                <li><strong>Express opinions:</strong> Share what you agree/disagree with</li>
                                <li><strong>Discuss challenges:</strong> Talk about problems you're solving</li>
                            </ul>
                        </div>
                        
                        <div class="tip-category">
                            <h4>🔍 Maximizing Analysis</h4>
                            <ul>
                                <li><strong>Wait for data:</strong> Have 3-5 conversations before trying serendipity analysis</li>
                                <li><strong>Review insights:</strong> Check your dashboard regularly</li>
                                <li><strong>Act on connections:</strong> Use discovered patterns to guide decisions</li>
                                <li><strong>Keep chatting:</strong> More data = better insights</li>
                            </ul>
                        </div>
                        
                        <div class="tip-category">
                            <h4>🎯 Example Topics to Explore</h4>
                            <div class="example-topics">
                                <span class="topic-tag">Career goals</span>
                                <span class="topic-tag">Learning interests</span>
                                <span class="topic-tag">Creative projects</span>
                                <span class="topic-tag">Problem-solving approaches</span>
                                <span class="topic-tag">Values and beliefs</span>
                                <span class="topic-tag">Future plans</span>
                                <span class="topic-tag">Daily challenges</span>
                                <span class="topic-tag">Inspiration sources</span>
                            </div>
                        </div>
                    </div>
                    <div class="tips-modal-footer">
                        <button class="hud-button primary" onclick="dashboard.closeOnboardingTips()">Start Chatting!</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', tipsContent);
        
        // Focus management
        const modal = document.querySelector('.onboarding-tips-modal');
        const closeButton = modal.querySelector('.tips-modal-close');
        closeButton.focus();
        
        this.trapFocusInModal(modal);
    }

    /**
     * Close onboarding tips modal
     */
    closeOnboardingTips() {
        const modal = document.querySelector('.onboarding-tips-modal');
        if (modal) {
            modal.remove();
        }
    }

    showDashboardContent() {
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const emptyState = document.getElementById('empty-state');
        const dashboardContent = document.getElementById('dashboard-content-inner');

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
     * Validate that existing API endpoints are working
     */
    async validateAPIEndpoints() {
        const endpoints = ['/api/insights'];
        
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
     * Get timeout value from server configuration or use fallback
     */
    async getSerendipityTimeout() {
        try {
            const response = await fetch('/api/serendipity', { method: 'GET' });
            if (response.ok) {
                const status = await response.json();
                // Use server timeout * 3 (for retries) + 120s buffer for network overhead
                // This accounts for backend retry logic (3 attempts with potential timeouts)
                const serverTimeout = status.service_info?.timeout || 120;
                const frontendTimeout = (serverTimeout * 3) + 120; // 3 retries + buffer
                console.log(`Frontend timeout set to ${frontendTimeout}s based on server timeout ${serverTimeout}s`);
                return frontendTimeout * 1000; // Convert to milliseconds
            }
        } catch (e) {
            console.warn('Could not get server timeout, using fallback:', e);
        }
        // Fallback to 6 minutes (360s) to handle backend retries
        console.log('Using fallback timeout of 360s');
        return 360000;
    }

    /**
     * Initiate serendipity analysis with comprehensive error handling
     */
    async discoverConnections() {
        const button = document.getElementById('discover-connections-btn');
        const resultsContainer = document.getElementById('serendipity-results');
        const statusElement = document.getElementById('serendipity-status');
        
        if (!button || !resultsContainer || !statusElement) {
            console.error('Serendipity UI elements not found');
            this.showSerendipityError('UI components not available. Please refresh the page.', resultsContainer);
            return;
        }

        // Initialize retry mechanism
        const maxRetries = 3;
        const retryDelay = 2000; // 2 seconds
        let currentAttempt = 1;

        const attemptAnalysis = async (attemptNumber) => {
            try {
                // Update UI to loading state with attempt info
                this.setSerendipityLoadingState(button, statusElement, resultsContainer, attemptNumber, maxRetries);
                
                // Check network connectivity first
                if (!navigator.onLine) {
                    throw new NetworkError('No internet connection. Please check your network and try again.');
                }

                // Get dynamic timeout from server configuration
                const dynamicTimeout = await this.getSerendipityTimeout();
                console.log(`Using frontend timeout of ${dynamicTimeout/1000}s for serendipity analysis`);

                // Add progress tracking for long requests
                let progressInterval;
                const startTime = Date.now();
                
                // Update progress every 10 seconds for long requests
                if (dynamicTimeout > 120000) { // If timeout > 2 minutes
                    progressInterval = setInterval(() => {
                        const elapsed = (Date.now() - startTime) / 1000;
                        if (elapsed > 30) { // Start showing progress after 30s
                            const progressElement = resultsContainer.querySelector('.progress-text');
                            if (progressElement) {
                                const minutes = Math.floor(elapsed / 60);
                                const seconds = Math.floor(elapsed % 60);
                                progressElement.textContent = `Analysis in progress: ${minutes}m ${seconds}s elapsed. Complex analysis may take up to 6 minutes...`;
                            }
                        }
                    }, 10000);
                }

                // Make API request with dynamic timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => {
                    clearInterval(progressInterval);
                    controller.abort();
                }, dynamicTimeout);
                
                const response = await fetch('/api/serendipity', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({}),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);
                clearInterval(progressInterval);

                // Handle different response scenarios
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    
                    // Categorize errors for better handling
                    if (response.status === 503) {
                        throw new ServiceUnavailableError(errorData.message || 'Serendipity analysis is currently disabled.');
                    } else if (response.status === 400) {
                        throw new InsufficientDataError(errorData.message || 'Not enough data for analysis.');
                    } else if (response.status >= 500) {
                        throw new ServerError(errorData.message || 'Server error occurred.');
                    } else {
                        throw new APIError(errorData.message || `Request failed with status ${response.status}`);
                    }
                }

                const data = await response.json();

                if (data.error) {
                    throw new APIError(data.message || 'Analysis failed');
                }

                // Check for partial results and handle gracefully
                if (this.hasPartialResults(data)) {
                    this.renderPartialResults(data, resultsContainer);
                    this.setSerendipityPartialState(button, statusElement);
                } else {
                    // Render successful results
                    this.renderSerendipityResults(data, resultsContainer);
                    this.setSerendipitySuccessState(button, statusElement);
                }

                // Track successful analysis
                this.trackSerendipitySuccess(data);

            } catch (error) {
                clearInterval(progressInterval); // Clean up progress tracking
                console.error(`Serendipity analysis error (attempt ${attemptNumber}):`, error);
                
                // Handle specific error types
                if (error.name === 'AbortError') {
                    error = new TimeoutError('Analysis timeout - the request took longer than expected. This usually happens with very large datasets or system load. The backend may still be processing - please wait a moment before trying again.');
                }

                // Determine if we should retry
                const shouldRetry = this.shouldRetrySerendipityAnalysis(error, attemptNumber, maxRetries);
                
                if (shouldRetry) {
                    // Show retry countdown
                    this.showRetryCountdown(resultsContainer, retryDelay, attemptNumber + 1, maxRetries);
                    
                    // Wait and retry
                    await new Promise(resolve => setTimeout(resolve, retryDelay));
                    return attemptAnalysis(attemptNumber + 1);
                } else {
                    // Final failure - show comprehensive error
                    this.renderSerendipityError(error, resultsContainer, attemptNumber, maxRetries);
                    this.setSerendipityErrorState(button, statusElement);
                    
                    // Track failure for analytics
                    this.trackSerendipityFailure(error, attemptNumber);
                }
            }
        };

        // Start the analysis attempt
        await attemptAnalysis(currentAttempt);
    }

    /**
     * Set serendipity UI to loading state with enhanced feedback
     */
    setSerendipityLoadingState(button, statusElement, resultsContainer, attemptNumber = 1, maxAttempts = 1) {
        // Update button
        button.disabled = true;
        button.classList.add('loading');
        button.setAttribute('aria-busy', 'true');
        
        const buttonText = button.querySelector('.button-text');
        if (buttonText) {
            buttonText.textContent = attemptNumber > 1 ? `Retrying (${attemptNumber}/${maxAttempts})` : 'Analyzing';
        }

        // Update status
        statusElement.className = 'serendipity-status analyzing';
        const statusText = statusElement.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = attemptNumber > 1 ? `Retry ${attemptNumber}` : 'Analyzing';
        }
        
        // Show enhanced loading in results
        const loadingMessages = [
            'Discovering hidden connections in your thoughts...',
            'Analyzing patterns across your conversations...',
            'Finding unexpected relationships in your ideas...',
            'Exploring cross-domain connections...',
            'Identifying recurring themes and insights...',
            'Processing large dataset - this may take up to 6 minutes...',
            'Performing deep semantic analysis...',
            'Cross-referencing insights and patterns...',
            'Complex analysis in progress - please be patient...',
            'AI model processing your unique thought patterns...'
        ];
        
        const randomMessage = loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
        
        resultsContainer.innerHTML = `
            <div class="serendipity-loading" role="status" aria-label="Analyzing your thoughts">
                <div class="loading-spinner" aria-hidden="true"></div>
                <p class="hud-text-secondary">${randomMessage}</p>
                ${attemptNumber > 1 ? `
                    <div class="retry-info" style="margin-top: var(--spacing-md); padding: var(--spacing-sm); background: rgba(255, 193, 7, 0.1); border-radius: var(--border-radius); font-size: 0.9em;">
                        <span class="retry-icon" aria-hidden="true">🔄</span>
                        Retry attempt ${attemptNumber} of ${maxAttempts}
                    </div>
                ` : ''}
                <div class="loading-progress" style="margin-top: var(--spacing-md);">
                    <div class="progress-bar">
                        <div class="progress-fill" style="animation: progress-pulse 2s infinite;"></div>
                    </div>
                    <p class="progress-text" style="font-size: 0.8em; color: var(--hud-text-tertiary); margin-top: var(--spacing-xs);">
                        Complex analysis may take up to 6 minutes depending on data size and system load...
                    </p>
                </div>
            </div>
        `;
    }

    /**
     * Set serendipity UI to success state
     */
    setSerendipitySuccessState(button, statusElement) {
        // Update button
        button.disabled = false;
        button.classList.remove('loading');
        button.setAttribute('aria-busy', 'false');
        
        const buttonText = button.querySelector('.button-text');
        if (buttonText) {
            buttonText.textContent = 'Discover Connections';
        }

        // Update status
        statusElement.className = 'serendipity-status ready';
        statusElement.querySelector('.status-text').textContent = 'Complete';
    }

    /**
     * Set serendipity UI to error state
     */
    setSerendipityErrorState(button, statusElement) {
        // Update button
        button.disabled = false;
        button.classList.remove('loading');
        button.setAttribute('aria-busy', 'false');
        
        const buttonText = button.querySelector('.button-text');
        if (buttonText) {
            buttonText.textContent = 'Discover Connections';
        }

        // Update status
        statusElement.className = 'serendipity-status error';
        const statusText = statusElement.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = 'Error';
        }
    }

    /**
     * Set serendipity UI to partial results state
     */
    setSerendipityPartialState(button, statusElement) {
        // Update button
        button.disabled = false;
        button.classList.remove('loading');
        button.setAttribute('aria-busy', 'false');
        
        const buttonText = button.querySelector('.button-text');
        if (buttonText) {
            buttonText.textContent = 'Discover Connections';
        }

        // Update status
        statusElement.className = 'serendipity-status partial';
        const statusText = statusElement.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = 'Partial';
        }
    }

    /**
     * Check if results are partial (some data missing or incomplete)
     */
    hasPartialResults(data) {
        const { connections = [], meta_patterns = [], serendipity_summary = '' } = data;
        
        // Consider results partial if we have very few connections or no summary
        return (connections.length > 0 && connections.length < 3) || 
               (connections.length > 0 && !serendipity_summary.trim()) ||
               (meta_patterns.length === 0 && connections.length > 0);
    }

    /**
     * Determine if we should retry the serendipity analysis
     */
    shouldRetrySerendipityAnalysis(error, attemptNumber, maxRetries) {
        // Don't retry if we've reached max attempts
        if (attemptNumber >= maxRetries) {
            return false;
        }

        // Don't retry for certain error types
        if (error.name === 'InsufficientDataError' || 
            error.name === 'ServiceUnavailableError') {
            return false;
        }

        // For timeout errors, only retry once since we have a long timeout
        if (error.name === 'TimeoutError' && attemptNumber >= 2) {
            return false;
        }

        // Retry for network, timeout, and server errors
        return error.name === 'NetworkError' || 
               error.name === 'TimeoutError' || 
               error.name === 'ServerError' ||
               error.name === 'APIError';
    }

    /**
     * Show retry countdown to user
     */
    showRetryCountdown(container, delay, nextAttempt, maxAttempts) {
        const seconds = Math.ceil(delay / 1000);
        let countdown = seconds;
        
        const updateCountdown = () => {
            container.innerHTML = `
                <div class="serendipity-retry-countdown" role="status" aria-label="Retrying analysis">
                    <div class="retry-icon" aria-hidden="true">🔄</div>
                    <h4 class="retry-title">Retrying Analysis</h4>
                    <p class="retry-message">Attempting again in ${countdown} second${countdown !== 1 ? 's' : ''}...</p>
                    <div class="retry-progress">
                        <div class="retry-progress-bar">
                            <div class="retry-progress-fill" style="width: ${((seconds - countdown) / seconds) * 100}%;"></div>
                        </div>
                        <p class="retry-info">Attempt ${nextAttempt} of ${maxAttempts}</p>
                    </div>
                </div>
            `;
            
            countdown--;
            if (countdown >= 0) {
                setTimeout(updateCountdown, 1000);
            }
        };
        
        updateCountdown();
    }

    /**
     * Track successful serendipity analysis for analytics
     */
    trackSerendipitySuccess(data) {
        try {
            const analytics = {
                event: 'serendipity_success',
                timestamp: new Date().toISOString(),
                connections_count: data.connections?.length || 0,
                patterns_count: data.meta_patterns?.length || 0,
                has_summary: !!data.serendipity_summary,
                analysis_duration: data.metadata?.analysis_duration || 0
            };
            
            // Store in localStorage for analytics
            const existingAnalytics = JSON.parse(localStorage.getItem('serendipity_analytics') || '[]');
            existingAnalytics.push(analytics);
            
            // Keep only last 50 entries
            if (existingAnalytics.length > 50) {
                existingAnalytics.splice(0, existingAnalytics.length - 50);
            }
            
            localStorage.setItem('serendipity_analytics', JSON.stringify(existingAnalytics));
        } catch (error) {
            console.warn('Failed to track serendipity success:', error);
        }
    }

    /**
     * Track failed serendipity analysis for analytics
     */
    trackSerendipityFailure(error, attemptNumber) {
        try {
            const analytics = {
                event: 'serendipity_failure',
                timestamp: new Date().toISOString(),
                error_type: error.name || 'Unknown',
                error_message: error.message || 'Unknown error',
                attempt_number: attemptNumber,
                user_agent: navigator.userAgent
            };
            
            // Store in localStorage for analytics
            const existingAnalytics = JSON.parse(localStorage.getItem('serendipity_analytics') || '[]');
            existingAnalytics.push(analytics);
            
            // Keep only last 50 entries
            if (existingAnalytics.length > 50) {
                existingAnalytics.splice(0, existingAnalytics.length - 50);
            }
            
            localStorage.setItem('serendipity_analytics', JSON.stringify(existingAnalytics));
        } catch (error) {
            console.warn('Failed to track serendipity failure:', error);
        }
    }

    /**
     * Render serendipity analysis results with pagination support
     */
    renderSerendipityResults(data, container) {
        const { connections = [], meta_patterns = [], serendipity_summary = '', recommendations = [], metadata = {} } = data;
        
        // Store data for pagination
        this.serendipityData = {
            connections,
            meta_patterns,
            serendipity_summary,
            recommendations,
            metadata
        };
        
        // Initialize pagination state
        this.connectionsPagination = {
            currentPage: 1,
            itemsPerPage: 6, // Show 6 connections per page
            totalItems: connections.length
        };
        
        this.metaPatternsPagination = {
            currentPage: 1,
            itemsPerPage: 4, // Show 4 meta patterns per page
            totalItems: meta_patterns.length
        };
        
        let html = '';

        // Render connections with pagination
        if (connections.length > 0) {
            html += this.renderConnectionsWithPagination(connections);
        }

        // Render meta patterns with pagination
        if (meta_patterns.length > 0) {
            html += this.renderMetaPatternsWithPagination(meta_patterns);
        }

        // Render summary
        if (serendipity_summary) {
            html += this.renderSerendipitySummary(serendipity_summary);
        }

        // Render recommendations
        if (recommendations.length > 0) {
            html += this.renderRecommendations(recommendations);
        }

        // Render metadata
        if (metadata) {
            html += this.renderSerendipityMetadata(metadata);
        }

        container.innerHTML = html;

        // Setup pagination event listeners
        this.setupSerendipityPagination();

        // Animate progress bars after rendering
        setTimeout(() => this.animateProgressBars(), 100);
        
        // Setup interactive elements
        setTimeout(() => this.setupInteractiveElements(), 150);
    }

    /**
     * Render connection cards with enhanced visual indicators
     */
    renderConnections(connections) {
        const connectionsHtml = connections.map((connection, index) => {
            const surpriseFactor = Math.round((connection.surprise_factor || 0) * 100);
            const relevance = Math.round((connection.relevance || 0) * 100);
            const connectedInsights = connection.connected_insights || [];
            
            // Determine visual intensity based on scores
            const surpriseIntensity = this.getIntensityClass(surpriseFactor);
            const relevanceIntensity = this.getIntensityClass(relevance);
            const overallScore = (surpriseFactor + relevance) / 2;
            const cardPriority = this.getPriorityClass(overallScore);
            
            return `
                <div class="connection-card ${cardPriority}" role="article" tabindex="0" data-connection-index="${index}">
                    <div class="connection-header">
                        <h4 class="connection-title">${this.escapeHtml(connection.title || 'Untitled Connection')}</h4>
                        <div class="connection-score-badge" aria-label="Overall connection strength ${Math.round(overallScore)}%">
                            ${Math.round(overallScore)}%
                        </div>
                    </div>
                    
                    <div class="connection-indicators">
                        <div class="connection-indicator surprise-indicator">
                            <div class="indicator-header">
                                <span class="indicator-label">
                                    <span class="indicator-icon" aria-hidden="true">✨</span>
                                    Surprise
                                </span>
                                <span class="indicator-value">${surpriseFactor}%</span>
                            </div>
                            <div class="indicator-bar" role="progressbar" aria-valuenow="${surpriseFactor}" aria-valuemin="0" aria-valuemax="100" aria-label="Surprise factor ${surpriseFactor}%">
                                <div class="indicator-fill surprise ${surpriseIntensity}" style="width: 0%" data-target-width="${surpriseFactor}%"></div>
                                <div class="indicator-glow surprise" style="width: 0%" data-target-width="${surpriseFactor}%"></div>
                            </div>
                        </div>
                        
                        <div class="connection-indicator relevance-indicator">
                            <div class="indicator-header">
                                <span class="indicator-label">
                                    <span class="indicator-icon" aria-hidden="true">🎯</span>
                                    Relevance
                                </span>
                                <span class="indicator-value">${relevance}%</span>
                            </div>
                            <div class="indicator-bar" role="progressbar" aria-valuenow="${relevance}" aria-valuemin="0" aria-valuemax="100" aria-label="Relevance ${relevance}%">
                                <div class="indicator-fill relevance ${relevanceIntensity}" style="width: 0%" data-target-width="${relevance}%"></div>
                                <div class="indicator-glow relevance" style="width: 0%" data-target-width="${relevance}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    ${connection.connection_type ? `
                        <div class="connection-type-badge">
                            <span class="connection-type-icon" aria-hidden="true">${this.getConnectionTypeIcon(connection.connection_type)}</span>
                            ${this.escapeHtml(connection.connection_type)}
                        </div>
                    ` : ''}
                    
                    <div class="connection-description">
                        ${this.escapeHtml(connection.description || 'No description available.')}
                    </div>
                    
                    ${connectedInsights.length > 0 ? `
                        <div class="connection-insights">
                            <button class="insights-toggle" aria-expanded="false" aria-controls="insights-${index}">
                                <span class="insights-toggle-icon" aria-hidden="true">🔗</span>
                                <span class="insights-toggle-text">Connected Insights (${connectedInsights.length})</span>
                                <span class="insights-toggle-arrow" aria-hidden="true">▼</span>
                            </button>
                            <div class="connected-insights" id="insights-${index}" aria-hidden="true">
                                ${connectedInsights.map(insight => `
                                    <span class="insight-tag" tabindex="0" role="button" aria-label="Insight: ${this.escapeHtml(insight)}">
                                        ${this.escapeHtml(insight)}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${connection.actionable_insight ? `
                        <div class="connection-actionable">
                            <div class="actionable-header">
                                <span class="actionable-icon" aria-hidden="true">💡</span>
                                <span class="actionable-label">Actionable Insight</span>
                            </div>
                            <div class="actionable-content">
                                ${this.escapeHtml(connection.actionable_insight)}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="connection-actions">
                        <button class="connection-action-btn expand-btn" aria-label="Expand connection details" data-connection-index="${index}">
                            <span aria-hidden="true">🔍</span>
                            Details
                        </button>
                        <button class="connection-action-btn bookmark-btn" aria-label="Bookmark this connection" data-connection-index="${index}">
                            <span aria-hidden="true">🔖</span>
                            Save
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="serendipity-connections" role="region" aria-label="Discovered connections">
                <div class="connections-header">
                    <h4 class="connections-title">
                        <span class="connections-icon" aria-hidden="true">🌟</span>
                        Discovered Connections
                        <span class="connections-count">(${connections.length})</span>
                    </h4>
                </div>
                <div class="connections-grid">
                    ${connectionsHtml}
                </div>
            </div>
        `;
    }
    
    /**
     * Render connections with pagination support
     */
    renderConnectionsWithPagination(connections) {
        const { currentPage, itemsPerPage } = this.connectionsPagination;
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pageConnections = connections.slice(startIndex, endIndex);
        const totalPages = Math.ceil(connections.length / itemsPerPage);
        
        const connectionsHtml = this.renderConnections(pageConnections);
        
        if (totalPages <= 1) {
            return connectionsHtml;
        }
        
        const paginationHtml = `
            <div class="serendipity-pagination connections-pagination" role="navigation" aria-label="Connections pagination">
                <button class="pagination-btn prev-btn" ${currentPage === 1 ? 'disabled' : ''} 
                        data-action="prev-connections" aria-label="Previous page of connections">
                    <span aria-hidden="true">‹</span>
                    Previous
                </button>
                <div class="pagination-info">
                    <span class="page-indicator">
                        Page ${currentPage} of ${totalPages}
                    </span>
                    <span class="items-indicator">
                        Showing ${startIndex + 1}-${Math.min(endIndex, connections.length)} of ${connections.length} connections
                    </span>
                </div>
                <button class="pagination-btn next-btn" ${currentPage === totalPages ? 'disabled' : ''} 
                        data-action="next-connections" aria-label="Next page of connections">
                    Next
                    <span aria-hidden="true">›</span>
                </button>
            </div>
        `;
        
        return connectionsHtml.replace('</div>', paginationHtml + '</div>');
    }

    /**
     * Render meta patterns with enhanced visualization and interactivity
     */
    renderMetaPatterns(metaPatterns) {
        const patternsHtml = metaPatterns.map((pattern, index) => {
            const confidence = Math.round((pattern.confidence || 0) * 100);
            const confidenceLevel = this.getConfidenceLevel(confidence);
            const evidenceCount = pattern.evidence_count || 0;
            
            return `
                <div class="meta-pattern-card ${confidenceLevel}" role="article" tabindex="0" data-pattern-index="${index}">
                    <div class="pattern-header">
                        <div class="pattern-icon" aria-hidden="true">${this.getPatternIcon(pattern.pattern_name)}</div>
                        <h5 class="meta-pattern-name">${this.escapeHtml(pattern.pattern_name || 'Unnamed Pattern')}</h5>
                        <div class="pattern-confidence-badge" aria-label="Confidence level ${confidence}%">
                            ${confidence}%
                        </div>
                    </div>
                    
                    <div class="pattern-description">
                        ${this.escapeHtml(pattern.description || 'No description available.')}
                    </div>
                    
                    <div class="pattern-metrics">
                        <div class="metric-item">
                            <div class="metric-header">
                                <span class="metric-label">
                                    <span class="metric-icon" aria-hidden="true">🎯</span>
                                    Confidence
                                </span>
                                <span class="metric-value">${confidence}%</span>
                            </div>
                            <div class="confidence-bar" role="progressbar" aria-valuenow="${confidence}" aria-valuemin="0" aria-valuemax="100" aria-label="Confidence ${confidence}%">
                                <div class="confidence-fill ${confidenceLevel}" style="width: 0%" data-target-width="${confidence}%"></div>
                                <div class="confidence-glow ${confidenceLevel}" style="width: 0%" data-target-width="${confidence}%"></div>
                            </div>
                        </div>
                        
                        ${evidenceCount > 0 ? `
                            <div class="metric-item evidence-metric">
                                <div class="metric-header">
                                    <span class="metric-label">
                                        <span class="metric-icon" aria-hidden="true">📊</span>
                                        Evidence
                                    </span>
                                    <span class="metric-value">${evidenceCount}</span>
                                </div>
                                <div class="evidence-visualization">
                                    ${this.renderEvidenceVisualization(evidenceCount)}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="pattern-actions">
                        <button class="pattern-action-btn explore-btn" aria-label="Explore pattern details" data-pattern-index="${index}">
                            <span aria-hidden="true">🔍</span>
                            Explore
                        </button>
                        <button class="pattern-action-btn related-btn" aria-label="Find related patterns" data-pattern-index="${index}">
                            <span aria-hidden="true">🔗</span>
                            Related
                        </button>
                    </div>
                    
                    <div class="pattern-details" id="pattern-details-${index}" aria-hidden="true">
                        <div class="details-content">
                            <div class="detail-section">
                                <h6 class="detail-title">Pattern Strength</h6>
                                <div class="strength-indicator ${confidenceLevel}">
                                    ${this.getStrengthDescription(confidence)}
                                </div>
                            </div>
                            ${evidenceCount > 0 ? `
                                <div class="detail-section">
                                    <h6 class="detail-title">Evidence Sources</h6>
                                    <div class="evidence-breakdown">
                                        Based on ${evidenceCount} piece${evidenceCount !== 1 ? 's' : ''} of evidence from your conversations and insights.
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="serendipity-meta-patterns" role="region" aria-label="Meta patterns">
                <div class="meta-patterns-header">
                    <h4 class="meta-patterns-title">
                        <span class="patterns-icon" aria-hidden="true">🧩</span>
                        Overarching Patterns
                        <span class="patterns-count">(${metaPatterns.length})</span>
                    </h4>
                    <div class="patterns-controls">
                        <button class="patterns-sort-btn" aria-label="Sort patterns by confidence">
                            <span aria-hidden="true">📊</span>
                            Sort by Confidence
                        </button>
                    </div>
                </div>
                <div class="meta-patterns-grid">
                    ${patternsHtml}
                </div>
            </div>
        `;
    }
    
    /**
     * Render meta patterns with pagination support
     */
    renderMetaPatternsWithPagination(metaPatterns) {
        const { currentPage, itemsPerPage } = this.metaPatternsPagination;
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pagePatterns = metaPatterns.slice(startIndex, endIndex);
        const totalPages = Math.ceil(metaPatterns.length / itemsPerPage);
        
        const patternsHtml = this.renderMetaPatterns(pagePatterns);
        
        if (totalPages <= 1) {
            return patternsHtml;
        }
        
        const paginationHtml = `
            <div class="serendipity-pagination patterns-pagination" role="navigation" aria-label="Patterns pagination">
                <button class="pagination-btn prev-btn" ${currentPage === 1 ? 'disabled' : ''} 
                        data-action="prev-patterns" aria-label="Previous page of patterns">
                    <span aria-hidden="true">‹</span>
                    Previous
                </button>
                <div class="pagination-info">
                    <span class="page-indicator">
                        Page ${currentPage} of ${totalPages}
                    </span>
                    <span class="items-indicator">
                        Showing ${startIndex + 1}-${Math.min(endIndex, metaPatterns.length)} of ${metaPatterns.length} patterns
                    </span>
                </div>
                <button class="pagination-btn next-btn" ${currentPage === totalPages ? 'disabled' : ''} 
                        data-action="next-patterns" aria-label="Next page of patterns">
                    Next
                    <span aria-hidden="true">›</span>
                </button>
            </div>
        `;
        
        return patternsHtml.replace('</div>', paginationHtml + '</div>');
    }

    /**
     * Render serendipity summary
     */
    renderSerendipitySummary(summary) {
        return `
            <div class="serendipity-summary" role="region" aria-label="Analysis summary">
                <h4 class="serendipity-summary-title">Analysis Summary</h4>
                <div class="serendipity-summary-content">${MarkdownRenderer.render(summary)}</div>
            </div>
        `;
    }

    /**
     * Render recommendations
     */
    renderRecommendations(recommendations) {
        const recommendationsHtml = recommendations.map(recommendation => `
            <li class="recommendation-item" role="listitem" tabindex="0">
                <span class="recommendation-icon" aria-hidden="true">💡</span>
                <span class="recommendation-text">${this.escapeHtml(recommendation)}</span>
            </li>
        `).join('');

        return `
            <div class="serendipity-recommendations" role="region" aria-label="Recommendations">
                <h4 class="serendipity-recommendations-title">Recommendations</h4>
                <ul class="recommendations-list" role="list">
                    ${recommendationsHtml}
                </ul>
            </div>
        `;
    }

    /**
     * Render serendipity metadata
     */
    renderSerendipityMetadata(metadata) {
        const timestamp = metadata.timestamp ? new Date(metadata.timestamp).toLocaleString() : 'Unknown';
        const model = metadata.model || 'Unknown';
        
        return `
            <div class="serendipity-metadata" role="contentinfo" aria-label="Analysis metadata">
                <div class="metadata-item">
                    <span class="metadata-icon" aria-hidden="true">🕒</span>
                    <span>Analyzed: ${timestamp}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-icon" aria-hidden="true">🤖</span>
                    <span>Model: ${model}</span>
                </div>
            </div>
        `;
    }

    /**
     * Render comprehensive serendipity error state with actionable guidance
     */
    renderSerendipityError(error, container, attemptNumber = 1, maxAttempts = 1) {
        const errorMessage = error.message || 'Unknown error occurred';
        const errorType = error.name || 'Error';
        
        // Categorize error types for specific guidance
        const isInsufficientData = errorType === 'InsufficientDataError' || 
                                  errorMessage.toLowerCase().includes('insufficient') || 
                                  errorMessage.toLowerCase().includes('not enough');
        
        const isNetworkError = errorType === 'NetworkError' || 
                              errorMessage.toLowerCase().includes('network') ||
                              errorMessage.toLowerCase().includes('connection');
        
        const isServiceUnavailable = errorType === 'ServiceUnavailableError' ||
                                   errorMessage.toLowerCase().includes('disabled') ||
                                   errorMessage.toLowerCase().includes('unavailable');
        
        const isTimeout = errorType === 'TimeoutError' ||
                         errorMessage.toLowerCase().includes('timeout') ||
                         errorMessage.toLowerCase().includes('taking longer');
        
        const isServerError = errorType === 'ServerError' ||
                             errorMessage.toLowerCase().includes('server error') ||
                             errorMessage.toLowerCase().includes('internal error');

        // Get appropriate icon and title
        let errorIcon = '⚠️';
        let errorTitle = 'Analysis Unavailable';
        
        if (isInsufficientData) {
            errorIcon = '📊';
            errorTitle = 'More Data Needed';
        } else if (isNetworkError) {
            errorIcon = '🌐';
            errorTitle = 'Connection Issue';
        } else if (isServiceUnavailable) {
            errorIcon = '🔧';
            errorTitle = 'Service Disabled';
        } else if (isTimeout) {
            errorIcon = '⏱️';
            errorTitle = 'Analysis Timeout';
        } else if (isServerError) {
            errorIcon = '🔧';
            errorTitle = 'Server Issue';
        }

        const errorHtml = `
            <div class="serendipity-error" role="alert">
                <div class="error-icon" aria-hidden="true">${errorIcon}</div>
                <h4 class="error-title">${errorTitle}</h4>
                <p class="error-message">${this.escapeHtml(errorMessage)}</p>
                
                ${attemptNumber > 1 ? `
                    <div class="error-attempts" style="margin-top: var(--spacing-sm); padding: var(--spacing-sm); background: rgba(255, 193, 7, 0.1); border-radius: var(--border-radius); font-size: 0.9em;">
                        <span class="attempts-icon" aria-hidden="true">🔄</span>
                        Failed after ${attemptNumber} attempt${attemptNumber !== 1 ? 's' : ''}
                    </div>
                ` : ''}
                
                ${this.getErrorSpecificGuidance(errorType, isInsufficientData, isNetworkError, isServiceUnavailable, isTimeout, isServerError)}
                
                <div class="error-actions" style="margin-top: var(--spacing-md); display: flex; gap: var(--spacing-sm); flex-wrap: wrap;">
                    ${!isServiceUnavailable ? `
                        <button class="hud-button secondary retry-button" onclick="dashboard.discoverConnections()" style="flex: 1; min-width: 120px;">
                            <span class="button-icon" aria-hidden="true">↻</span>
                            Try Again
                        </button>
                    ` : ''}
                    
                    <button class="hud-button tertiary help-button" onclick="dashboard.showSerendipityHelp()" style="flex: 1; min-width: 120px;">
                        <span class="button-icon" aria-hidden="true">❓</span>
                        Get Help
                    </button>
                </div>
                
                ${this.getErrorTroubleshootingSteps(errorType)}
            </div>
        `;
        
        container.innerHTML = errorHtml;
    }

    /**
     * Get error-specific guidance based on error type
     */
    getErrorSpecificGuidance(errorType, isInsufficientData, isNetworkError, isServiceUnavailable, isTimeout, isServerError) {
        if (isInsufficientData) {
            return `
                <div class="error-suggestions" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(0, 229, 255, 0.05); border-radius: var(--border-radius); text-align: left;">
                    <strong>💡 To enable serendipity analysis:</strong>
                    <ul style="margin: var(--spacing-sm) 0 0 var(--spacing-md); color: var(--hud-text-secondary);">
                        <li>Have at least 3-5 conversations with the AI</li>
                        <li>Share diverse topics and thoughts</li>
                        <li>Allow insights to accumulate over time</li>
                        <li>Discuss different subjects to create cross-connections</li>
                    </ul>
                    <p style="margin-top: var(--spacing-sm); font-size: 0.9em; color: var(--hud-text-tertiary);">
                        The more you interact, the better the analysis becomes!
                    </p>
                </div>
            `;
        } else if (isNetworkError) {
            return `
                <div class="error-suggestions" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(255, 193, 7, 0.05); border-radius: var(--border-radius); text-align: left;">
                    <strong>🌐 Network troubleshooting:</strong>
                    <ul style="margin: var(--spacing-sm) 0 0 var(--spacing-md); color: var(--hud-text-secondary);">
                        <li>Check your internet connection</li>
                        <li>Try refreshing the page</li>
                        <li>Disable VPN if using one</li>
                        <li>Check if other websites are working</li>
                    </ul>
                </div>
            `;
        } else if (isServiceUnavailable) {
            return `
                <div class="error-suggestions" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(108, 117, 125, 0.05); border-radius: var(--border-radius); text-align: left;">
                    <strong>🔧 Service information:</strong>
                    <p style="margin: var(--spacing-sm) 0 0 0; color: var(--hud-text-secondary);">
                        The serendipity analysis feature is currently disabled. This may be intentional for system maintenance or configuration reasons.
                    </p>
                    <p style="margin: var(--spacing-sm) 0 0 0; color: var(--hud-text-tertiary); font-size: 0.9em;">
                        Contact your system administrator if you believe this is an error.
                    </p>
                </div>
            `;
        } else if (isTimeout) {
            return `
                <div class="error-suggestions" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(255, 193, 7, 0.05); border-radius: var(--border-radius); text-align: left;">
                    <strong>⏱️ Performance tips:</strong>
                    <ul style="margin: var(--spacing-sm) 0 0 var(--spacing-md); color: var(--hud-text-secondary);">
                        <li>Analysis may take longer with large amounts of data</li>
                        <li>Try again during off-peak hours</li>
                        <li>Ensure your system has adequate resources</li>
                        <li>Close other resource-intensive applications</li>
                    </ul>
                </div>
            `;
        } else if (isServerError) {
            return `
                <div class="error-suggestions" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(220, 53, 69, 0.05); border-radius: var(--border-radius); text-align: left;">
                    <strong>🔧 Server issue detected:</strong>
                    <p style="margin: var(--spacing-sm) 0 0 0; color: var(--hud-text-secondary);">
                        There's a temporary issue with the analysis service. This is usually resolved quickly.
                    </p>
                    <ul style="margin: var(--spacing-sm) 0 0 var(--spacing-md); color: var(--hud-text-secondary);">
                        <li>Wait a few minutes and try again</li>
                        <li>Check if the AI service is running</li>
                        <li>Refresh the page if the issue persists</li>
                    </ul>
                </div>
            `;
        }
        
        return `
            <div class="error-suggestions" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(108, 117, 125, 0.05); border-radius: var(--border-radius); text-align: left;">
                <strong>🔍 General troubleshooting:</strong>
                <ul style="margin: var(--spacing-sm) 0 0 var(--spacing-md); color: var(--hud-text-secondary);">
                    <li>Refresh the page and try again</li>
                    <li>Check your internet connection</li>
                    <li>Ensure the AI service is running</li>
                    <li>Try again in a few minutes</li>
                </ul>
            </div>
        `;
    }

    /**
     * Get troubleshooting steps for specific error types
     */
    getErrorTroubleshootingSteps(errorType) {
        return `
            <details class="error-troubleshooting" style="margin-top: var(--spacing-md); padding: var(--spacing-md); background: rgba(108, 117, 125, 0.02); border-radius: var(--border-radius);">
                <summary style="cursor: pointer; font-weight: 500; color: var(--hud-text-secondary);">
                    🔧 Advanced Troubleshooting
                </summary>
                <div style="margin-top: var(--spacing-sm); font-size: 0.9em; color: var(--hud-text-tertiary);">
                    <p><strong>Error Type:</strong> ${errorType}</p>
                    <p><strong>Timestamp:</strong> ${new Date().toLocaleString()}</p>
                    <p><strong>Browser:</strong> ${navigator.userAgent.split(' ').slice(-2).join(' ')}</p>
                    <p><strong>Online Status:</strong> ${navigator.onLine ? 'Connected' : 'Offline'}</p>
                    <p style="margin-top: var(--spacing-sm);">
                        If this issue persists, you can check the browser console (F12) for more technical details.
                    </p>
                </div>
            </details>
        `;
    }

    /**
     * Render partial results with graceful degradation
     */
    renderPartialResults(data, container) {
        const { connections = [], meta_patterns = [], serendipity_summary = '', recommendations = [], metadata = {} } = data;
        
        let html = `
            <div class="serendipity-partial-notice" role="alert" style="margin-bottom: var(--spacing-md); padding: var(--spacing-md); background: rgba(255, 193, 7, 0.1); border-radius: var(--border-radius); border-left: 4px solid var(--warning-color);">
                <div class="partial-icon" aria-hidden="true" style="display: inline-block; margin-right: var(--spacing-sm);">⚠️</div>
                <strong>Partial Results Available</strong>
                <p style="margin: var(--spacing-xs) 0 0 0; color: var(--hud-text-secondary); font-size: 0.9em;">
                    Some analysis data is incomplete, but we found ${connections.length} connection${connections.length !== 1 ? 's' : ''} to show you.
                </p>
            </div>
        `;

        // Render available connections
        if (connections.length > 0) {
            html += this.renderConnectionsWithPagination(connections);
        }

        // Render available meta patterns
        if (meta_patterns.length > 0) {
            html += this.renderMetaPatternsWithPagination(meta_patterns);
        }

        // Show what's missing
        const missingElements = [];
        if (connections.length < 3) missingElements.push('more connections');
        if (!serendipity_summary.trim()) missingElements.push('analysis summary');
        if (meta_patterns.length === 0) missingElements.push('meta patterns');
        if (recommendations.length === 0) missingElements.push('recommendations');

        if (missingElements.length > 0) {
            html += `
                <div class="serendipity-missing-data" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); background: rgba(108, 117, 125, 0.05); border-radius: var(--border-radius);">
                    <h4 style="margin: 0 0 var(--spacing-sm) 0; color: var(--hud-text-secondary);">
                        <span aria-hidden="true">📊</span> To get complete analysis:
                    </h4>
                    <p style="margin: 0 0 var(--spacing-sm) 0; color: var(--hud-text-tertiary); font-size: 0.9em;">
                        Missing: ${missingElements.join(', ')}
                    </p>
                    <ul style="margin: 0 0 var(--spacing-sm) var(--spacing-md); color: var(--hud-text-secondary); font-size: 0.9em;">
                        <li>Have more conversations to build richer data</li>
                        <li>Discuss diverse topics for better cross-connections</li>
                        <li>Try the analysis again later</li>
                    </ul>
                    <button class="hud-button secondary" onclick="dashboard.discoverConnections()" style="margin-top: var(--spacing-sm);">
                        <span class="button-icon" aria-hidden="true">🔄</span>
                        Try Full Analysis Again
                    </button>
                </div>
            `;
        }

        // Add metadata if available
        if (metadata.analysis_timestamp) {
            html += this.renderSerendipityMetadata(metadata);
        }

        container.innerHTML = html;
        
        // Setup interactive elements
        this.setupSerendipityPagination();
        this.setupInteractiveElements();
        this.animateProgressBars();
    }

    /**
     * Show serendipity help modal or section
     */
    showSerendipityHelp() {
        const helpContent = `
            <div class="serendipity-help-modal" role="dialog" aria-labelledby="help-title" aria-modal="true">
                <div class="help-modal-backdrop" onclick="dashboard.closeSerendipityHelp()"></div>
                <div class="help-modal-content">
                    <div class="help-modal-header">
                        <h3 id="help-title">Serendipity Analysis Help</h3>
                        <button class="help-modal-close" onclick="dashboard.closeSerendipityHelp()" aria-label="Close help">×</button>
                    </div>
                    <div class="help-modal-body">
                        <section class="help-section">
                            <h4>🔍 What is Serendipity Analysis?</h4>
                            <p>Serendipity analysis discovers hidden connections, patterns, and insights within your conversations and thoughts. It finds non-obvious relationships that you might not have noticed.</p>
                        </section>
                        
                        <section class="help-section">
                            <h4>📊 How to Get Better Results</h4>
                            <ul>
                                <li><strong>Have diverse conversations:</strong> Discuss different topics to create cross-domain connections</li>
                                <li><strong>Share personal thoughts:</strong> The more authentic your conversations, the better the insights</li>
                                <li><strong>Build up data over time:</strong> Analysis improves with more conversation history</li>
                                <li><strong>Be patient:</strong> Complex analysis may take a few moments</li>
                            </ul>
                        </section>
                        
                        <section class="help-section">
                            <h4>🔧 Troubleshooting Common Issues</h4>
                            <dl>
                                <dt><strong>Not enough data:</strong></dt>
                                <dd>Have at least 3-5 conversations before trying analysis</dd>
                                
                                <dt><strong>Analysis taking too long:</strong></dt>
                                <dd>Large datasets may require more processing time. Try during off-peak hours.</dd>
                                
                                <dt><strong>Connection issues:</strong></dt>
                                <dd>Check your internet connection and try refreshing the page</dd>
                                
                                <dt><strong>Service unavailable:</strong></dt>
                                <dd>The feature may be temporarily disabled for maintenance</dd>
                            </dl>
                        </section>
                        
                        <section class="help-section">
                            <h4>🎯 Understanding Results</h4>
                            <ul>
                                <li><strong>Connections:</strong> Relationships between different ideas or topics</li>
                                <li><strong>Surprise Factor:</strong> How unexpected the connection is (higher = more serendipitous)</li>
                                <li><strong>Relevance:</strong> How meaningful the connection is to you</li>
                                <li><strong>Meta Patterns:</strong> Overarching themes across multiple connections</li>
                            </ul>
                        </section>
                        
                        <section class="help-section">
                            <h4>🚀 Tips for Success</h4>
                            <ul>
                                <li>Use the analysis results to explore new directions in your thinking</li>
                                <li>Look for patterns that reveal your core interests and values</li>
                                <li>Consider the actionable insights provided with each connection</li>
                                <li>Run analysis periodically as your conversation history grows</li>
                            </ul>
                        </section>
                    </div>
                    <div class="help-modal-footer">
                        <button class="hud-button primary" onclick="dashboard.closeSerendipityHelp()">Got it!</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.insertAdjacentHTML('beforeend', helpContent);
        
        // Focus management for accessibility
        const modal = document.querySelector('.serendipity-help-modal');
        const closeButton = modal.querySelector('.help-modal-close');
        closeButton.focus();
        
        // Trap focus within modal
        this.trapFocusInModal(modal);
    }

    /**
     * Close serendipity help modal
     */
    closeSerendipityHelp() {
        const modal = document.querySelector('.serendipity-help-modal');
        if (modal) {
            modal.remove();
        }
        
        // Return focus to help button
        const helpButton = document.querySelector('.help-button');
        if (helpButton) {
            helpButton.focus();
        }
    }

    /**
     * Trap focus within modal for accessibility
     */
    trapFocusInModal(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSerendipityHelp();
            } else if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }

    /**
     * Show general error message with fallback
     */
    showSerendipityError(message, container) {
        if (container) {
            container.innerHTML = `
                <div class="serendipity-error" role="alert">
                    <div class="error-icon" aria-hidden="true">⚠️</div>
                    <h4 class="error-title">Error</h4>
                    <p class="error-message">${this.escapeHtml(message)}</p>
                    <button class="hud-button secondary" onclick="location.reload()" style="margin-top: var(--spacing-md);">
                        <span class="button-icon" aria-hidden="true">🔄</span>
                        Refresh Page
                    </button>
                </div>
            `;
        } else {
            console.error('Serendipity error:', message);
            alert('Error: ' + message);
        }
    }

    /**
     * Animate progress bars for visual feedback
     */
    animateProgressBars() {
        const progressBars = document.querySelectorAll('.indicator-fill, .confidence-fill');
        progressBars.forEach((bar, index) => {
            const targetWidth = bar.getAttribute('data-target-width') || bar.style.width;
            bar.style.width = '0%';
            bar.style.transition = `width 0.8s ease-out ${index * 0.1}s`;
            
            // Trigger reflow and animate
            bar.offsetHeight;
            bar.style.width = targetWidth;
            
            // Animate glow effect
            const glow = bar.nextElementSibling;
            if (glow && glow.classList.contains('indicator-glow')) {
                glow.style.width = '0%';
                glow.style.transition = `width 0.8s ease-out ${index * 0.1 + 0.2}s`;
                setTimeout(() => {
                    glow.style.width = targetWidth;
                }, (index * 100) + 200);
            }
        });
    }
    
    /**
     * Setup pagination event listeners
     */
    setupSerendipityPagination() {
        // Connections pagination
        const connectionsPagination = document.querySelector('.connections-pagination');
        if (connectionsPagination) {
            connectionsPagination.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]')?.getAttribute('data-action');
                if (action === 'prev-connections') {
                    this.previousConnectionsPage();
                } else if (action === 'next-connections') {
                    this.nextConnectionsPage();
                }
            });
        }
        
        // Patterns pagination
        const patternsPagination = document.querySelector('.patterns-pagination');
        if (patternsPagination) {
            patternsPagination.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]')?.getAttribute('data-action');
                if (action === 'prev-patterns') {
                    this.previousPatternsPage();
                } else if (action === 'next-patterns') {
                    this.nextPatternsPage();
                }
            });
        }
    }
    
    /**
     * Setup interactive elements
     */
    setupInteractiveElements() {
        // Connection card interactions
        this.setupConnectionInteractions();
        
        // Pattern card interactions
        this.setupPatternInteractions();
        
        // Insights toggle interactions
        this.setupInsightsToggle();
        
        // Keyboard navigation
        this.setupKeyboardNavigation();
    }
    
    /**
     * Setup connection card interactions
     */
    setupConnectionInteractions() {
        const connectionCards = document.querySelectorAll('.connection-card');
        connectionCards.forEach(card => {
            // Expand/collapse details
            const expandBtn = card.querySelector('.expand-btn');
            if (expandBtn) {
                expandBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleConnectionDetails(card);
                });
            }
            
            // Bookmark functionality
            const bookmarkBtn = card.querySelector('.bookmark-btn');
            if (bookmarkBtn) {
                bookmarkBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleConnectionBookmark(card);
                });
            }
            
            // Card hover effects
            card.addEventListener('mouseenter', () => {
                this.highlightRelatedElements(card);
            });
            
            card.addEventListener('mouseleave', () => {
                this.clearHighlights();
            });
        });
    }
    
    /**
     * Setup pattern card interactions
     */
    setupPatternInteractions() {
        const patternCards = document.querySelectorAll('.meta-pattern-card');
        patternCards.forEach(card => {
            // Explore pattern details
            const exploreBtn = card.querySelector('.explore-btn');
            if (exploreBtn) {
                exploreBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.togglePatternDetails(card);
                });
            }
            
            // Find related patterns
            const relatedBtn = card.querySelector('.related-btn');
            if (relatedBtn) {
                relatedBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showRelatedPatterns(card);
                });
            }
        });
        
        // Sort patterns functionality
        const sortBtn = document.querySelector('.patterns-sort-btn');
        if (sortBtn) {
            sortBtn.addEventListener('click', () => {
                this.sortPatternsByConfidence();
            });
        }
    }
    
    /**
     * Setup insights toggle functionality
     */
    setupInsightsToggle() {
        const insightsToggles = document.querySelectorAll('.insights-toggle');
        insightsToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleInsightsVisibility(toggle);
            });
        });
    }
    
    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        const focusableElements = document.querySelectorAll('.connection-card, .meta-pattern-card, .insight-tag');
        focusableElements.forEach(element => {
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (element.classList.contains('connection-card')) {
                        this.toggleConnectionDetails(element);
                    } else if (element.classList.contains('meta-pattern-card')) {
                        this.togglePatternDetails(element);
                    }
                }
            });
        });
    }
    
    /**
     * Pagination methods
     */
    previousConnectionsPage() {
        if (this.connectionsPagination.currentPage > 1) {
            this.connectionsPagination.currentPage--;
            this.updateConnectionsDisplay();
        }
    }
    
    nextConnectionsPage() {
        const totalPages = Math.ceil(this.connectionsPagination.totalItems / this.connectionsPagination.itemsPerPage);
        if (this.connectionsPagination.currentPage < totalPages) {
            this.connectionsPagination.currentPage++;
            this.updateConnectionsDisplay();
        }
    }
    
    previousPatternsPage() {
        if (this.metaPatternsPagination.currentPage > 1) {
            this.metaPatternsPagination.currentPage--;
            this.updatePatternsDisplay();
        }
    }
    
    nextPatternsPage() {
        const totalPages = Math.ceil(this.metaPatternsPagination.totalItems / this.metaPatternsPagination.itemsPerPage);
        if (this.metaPatternsPagination.currentPage < totalPages) {
            this.metaPatternsPagination.currentPage++;
            this.updatePatternsDisplay();
        }
    }
    
    /**
     * Update displays after pagination
     */
    updateConnectionsDisplay() {
        const connectionsContainer = document.querySelector('.serendipity-connections');
        if (connectionsContainer && this.serendipityData) {
            const newHtml = this.renderConnectionsWithPagination(this.serendipityData.connections);
            connectionsContainer.outerHTML = newHtml;
            this.setupSerendipityPagination();
            setTimeout(() => {
                this.animateProgressBars();
                this.setupInteractiveElements();
            }, 100);
        }
    }
    
    updatePatternsDisplay() {
        const patternsContainer = document.querySelector('.serendipity-meta-patterns');
        if (patternsContainer && this.serendipityData) {
            const newHtml = this.renderMetaPatternsWithPagination(this.serendipityData.meta_patterns);
            patternsContainer.outerHTML = newHtml;
            this.setupSerendipityPagination();
            setTimeout(() => {
                this.animateProgressBars();
                this.setupInteractiveElements();
            }, 100);
        }
    }
    
    /**
     * Interactive functionality methods
     */
    toggleConnectionDetails(card) {
        const isExpanded = card.classList.contains('expanded');
        
        // Close all other expanded cards
        document.querySelectorAll('.connection-card.expanded').forEach(otherCard => {
            if (otherCard !== card) {
                otherCard.classList.remove('expanded');
            }
        });
        
        card.classList.toggle('expanded', !isExpanded);
        
        // Update ARIA attributes
        const expandBtn = card.querySelector('.expand-btn');
        if (expandBtn) {
            expandBtn.setAttribute('aria-expanded', !isExpanded);
            expandBtn.innerHTML = !isExpanded ? 
                '<span aria-hidden="true">🔍</span> Collapse' : 
                '<span aria-hidden="true">🔍</span> Details';
        }
    }
    
    togglePatternDetails(card) {
        const detailsElement = card.querySelector('.pattern-details');
        const exploreBtn = card.querySelector('.explore-btn');
        
        if (detailsElement && exploreBtn) {
            const isHidden = detailsElement.getAttribute('aria-hidden') === 'true';
            detailsElement.setAttribute('aria-hidden', !isHidden);
            exploreBtn.setAttribute('aria-expanded', isHidden);
            
            card.classList.toggle('details-expanded', isHidden);
            
            exploreBtn.innerHTML = isHidden ? 
                '<span aria-hidden="true">🔍</span> Hide' : 
                '<span aria-hidden="true">🔍</span> Explore';
        }
    }
    
    toggleInsightsVisibility(toggle) {
        const insightsContainer = toggle.nextElementSibling;
        const arrow = toggle.querySelector('.insights-toggle-arrow');
        
        if (insightsContainer && arrow) {
            const isHidden = insightsContainer.getAttribute('aria-hidden') === 'true';
            insightsContainer.setAttribute('aria-hidden', !isHidden);
            toggle.setAttribute('aria-expanded', isHidden);
            
            arrow.textContent = isHidden ? '▲' : '▼';
            insightsContainer.style.display = isHidden ? 'flex' : 'none';
        }
    }
    
    toggleConnectionBookmark(card) {
        const bookmarkBtn = card.querySelector('.bookmark-btn');
        const isBookmarked = card.classList.contains('bookmarked');
        
        card.classList.toggle('bookmarked', !isBookmarked);
        
        if (bookmarkBtn) {
            bookmarkBtn.innerHTML = !isBookmarked ? 
                '<span aria-hidden="true">🔖</span> Saved' : 
                '<span aria-hidden="true">🔖</span> Save';
            bookmarkBtn.setAttribute('aria-label', !isBookmarked ? 
                'Remove bookmark from this connection' : 
                'Bookmark this connection');
        }
        
        // Store bookmark state (could be enhanced with localStorage)
        console.log(`Connection ${!isBookmarked ? 'bookmarked' : 'unbookmarked'}`);
    }
    
    highlightRelatedElements(card) {
        // Add visual highlighting for related elements
        card.classList.add('highlighted');
    }
    
    clearHighlights() {
        document.querySelectorAll('.highlighted').forEach(element => {
            element.classList.remove('highlighted');
        });
    }
    
    showRelatedPatterns(card) {
        // This could be enhanced to show actual related patterns
        const patternIndex = card.getAttribute('data-pattern-index');
        console.log(`Showing related patterns for pattern ${patternIndex}`);
        
        // For now, just highlight other patterns
        document.querySelectorAll('.meta-pattern-card').forEach(otherCard => {
            if (otherCard !== card) {
                otherCard.classList.add('related-highlight');
                setTimeout(() => {
                    otherCard.classList.remove('related-highlight');
                }, 2000);
            }
        });
    }
    
    sortPatternsByConfidence() {
        if (!this.serendipityData || !this.serendipityData.meta_patterns) return;
        
        // Sort patterns by confidence
        const sortedPatterns = [...this.serendipityData.meta_patterns].sort((a, b) => {
            return (b.confidence || 0) - (a.confidence || 0);
        });
        
        this.serendipityData.meta_patterns = sortedPatterns;
        this.metaPatternsPagination.currentPage = 1;
        this.updatePatternsDisplay();
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Get intensity class based on score
     */
    getIntensityClass(score) {
        if (score >= 80) return 'high-intensity';
        if (score >= 60) return 'medium-intensity';
        if (score >= 40) return 'low-intensity';
        return 'minimal-intensity';
    }
    
    /**
     * Get priority class based on overall score
     */
    getPriorityClass(score) {
        if (score >= 80) return 'high-priority';
        if (score >= 60) return 'medium-priority';
        return 'standard-priority';
    }
    
    /**
     * Get confidence level class
     */
    getConfidenceLevel(confidence) {
        if (confidence >= 80) return 'high-confidence';
        if (confidence >= 60) return 'medium-confidence';
        if (confidence >= 40) return 'low-confidence';
        return 'minimal-confidence';
    }
    
    /**
     * Get connection type icon
     */
    getConnectionTypeIcon(type) {
        const icons = {
            'thematic': '🎭',
            'temporal': '⏰',
            'causal': '🔗',
            'conceptual': '💭',
            'emotional': '❤️',
            'behavioral': '🎯',
            'cross-domain': '🌐',
            'contradiction': '⚡',
            'evolution': '📈',
            'pattern': '🔄'
        };
        return icons[type.toLowerCase()] || '🔗';
    }
    
    /**
     * Get pattern icon based on pattern name
     */
    getPatternIcon(patternName) {
        const name = (patternName || '').toLowerCase();
        if (name.includes('growth') || name.includes('learning')) return '📈';
        if (name.includes('creative') || name.includes('innovation')) return '💡';
        if (name.includes('social') || name.includes('relationship')) return '👥';
        if (name.includes('emotional') || name.includes('feeling')) return '❤️';
        if (name.includes('decision') || name.includes('choice')) return '🎯';
        if (name.includes('time') || name.includes('temporal')) return '⏰';
        if (name.includes('conflict') || name.includes('tension')) return '⚡';
        if (name.includes('value') || name.includes('belief')) return '⭐';
        return '🧩';
    }
    
    /**
     * Get strength description based on confidence
     */
    getStrengthDescription(confidence) {
        if (confidence >= 90) return 'Very Strong - Highly consistent pattern';
        if (confidence >= 80) return 'Strong - Clear and consistent pattern';
        if (confidence >= 70) return 'Moderate - Generally consistent pattern';
        if (confidence >= 60) return 'Emerging - Pattern becoming apparent';
        if (confidence >= 50) return 'Weak - Some evidence of pattern';
        return 'Minimal - Limited evidence of pattern';
    }
    
    /**
     * Render evidence visualization
     */
    renderEvidenceVisualization(evidenceCount) {
        const maxDots = 10;
        const dots = Math.min(evidenceCount, maxDots);
        const extraCount = evidenceCount > maxDots ? evidenceCount - maxDots : 0;
        
        let visualization = '';
        for (let i = 0; i < dots; i++) {
            visualization += '<span class="evidence-dot" aria-hidden="true">●</span>';
        }
        
        if (extraCount > 0) {
            visualization += `<span class="evidence-extra" aria-hidden="true">+${extraCount}</span>`;
        }
        
        return visualization;
    }

    /**
     * Clean up automatic updates and chart manager references
     */
    cleanup() {
        if (this.chartUpdateInterval) {
            clearInterval(this.chartUpdateInterval);
            this.chartUpdateInterval = null;
        }

        // Clean up chart manager reference with proper reference counting
        if (this.chartManager && Dashboard.chartManagerInstance) {
            Dashboard.chartManagerRefCount--;
            console.log('Dashboard cleanup: Chart manager refs remaining:', Dashboard.chartManagerRefCount);
            
            // Only destroy the singleton if no more references exist
            if (Dashboard.chartManagerRefCount <= 0) {
                if (this.chartManager.destroy && typeof this.chartManager.destroy === 'function') {
                    this.chartManager.destroy();
                }
                Dashboard.chartManagerInstance = null;
                Dashboard.chartManagerRefCount = 0;
                console.log('Chart manager singleton destroyed');
            }
        }
        
        this.chartManager = null;
    }

    /**
     * Ensure serendipity section is visible and accessible
     */
    ensureSerendipityVisibility() {
        const serendipitySection = document.querySelector('.serendipity-section');
        if (serendipitySection) {
            // Add a subtle scroll indicator if the section is not in view
            setTimeout(() => {
                const rect = serendipitySection.getBoundingClientRect();
                const container = document.querySelector('.dashboard-content');
                
                if (container && rect.top > window.innerHeight) {
                    // Add a visual hint that there's more content below
                    this.addScrollIndicator(container);
                }
            }, 2000); // Wait 2 seconds for page to settle
        }
    }

    /**
     * Add a scroll indicator to show more content is available
     */
    addScrollIndicator(container) {
        if (document.querySelector('.scroll-indicator')) return; // Already exists
        
        const indicator = document.createElement('div');
        indicator.className = 'scroll-indicator';
        indicator.innerHTML = `
            <div class="scroll-indicator-content">
                <span class="scroll-indicator-text">Scroll for Serendipity Analysis</span>
                <span class="scroll-indicator-arrow">↓</span>
            </div>
        `;
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(0, 229, 255, 0.7));
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 1000;
            animation: pulse 2s infinite;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
            font-family: var(--hud-font-family);
        `;
        
        indicator.addEventListener('click', () => {
            const serendipitySection = document.querySelector('.serendipity-section');
            if (serendipitySection) {
                serendipitySection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                setTimeout(() => indicator.remove(), 1000);
            }
        });
        
        document.body.appendChild(indicator);
        
        // Remove indicator after 10 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.remove();
            }
        }, 10000);
    }

    /**
     * Enhanced markdown content rendering with safety checks
     */
    renderMarkdownContent(content) {
        if (!content || typeof content !== 'string') {
            return '<em>No content available</em>';
        }
        
        // Use the existing MarkdownRenderer if available
        if (typeof MarkdownRenderer !== 'undefined' && MarkdownRenderer.render) {
            return MarkdownRenderer.render(content);
        }
        
        // Fallback to basic HTML escaping
        return this.escapeHtml(content);
    }

    /**
     * Safely escape HTML content
     */
    escapeHtml(text) {
        if (!text || typeof text !== 'string') return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Animate connection metrics with staggered progress bars
     */
    animateConnectionMetrics(connections) {
        connections.forEach((connection, index) => {
            const surpriseFactor = Math.round((connection.surprise_factor || 0) * 100);
            const relevance = Math.round((connection.relevance || 0) * 100);
            
            const surpriseBar = document.getElementById(`surprise-${index}`);
            const relevanceBar = document.getElementById(`relevance-${index}`);
            
            if (surpriseBar) {
                const surpriseFill = surpriseBar.querySelector('.progress-fill');
                if (surpriseFill) {
                    setTimeout(() => {
                        surpriseFill.style.width = `${surpriseFactor}%`;
                        surpriseFill.style.transition = 'width 1.2s ease-out';
                    }, index * 100);
                }
            }
            
            if (relevanceBar) {
                const relevanceFill = relevanceBar.querySelector('.progress-fill');
                if (relevanceFill) {
                    setTimeout(() => {
                        relevanceFill.style.width = `${relevance}%`;
                        relevanceFill.style.transition = 'width 1.2s ease-out';
                    }, (index * 100) + 200);
                }
            }
        });
    }

    /**
     * Animate pattern confidence visualizations
     */
    animatePatternConfidence(patterns) {
        patterns.forEach((pattern, index) => {
            const confidence = Math.round((pattern.confidence || 0) * 100);
            const confidenceBar = document.getElementById(`pattern-confidence-${index}`);
            
            if (confidenceBar) {
                const confidenceFill = confidenceBar.querySelector('.confidence-fill');
                if (confidenceFill) {
                    setTimeout(() => {
                        confidenceFill.style.width = `${confidence}%`;
                        confidenceFill.style.transition = 'width 1.5s ease-out';
                        
                        // Add pulse effect for high confidence
                        if (confidence >= 80) {
                            confidenceBar.classList.add('high-confidence-pulse');
                        }
                    }, index * 150);
                }
            }
        });
    }

    /**
     * Animate recommendations with staggered appearance
     */
    animateRecommendations() {
        const recommendations = document.querySelectorAll('.recommendation-item');
        recommendations.forEach((rec, index) => {
            rec.style.opacity = '0';
            rec.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                rec.style.opacity = '1';
                rec.style.transform = 'translateY(0)';
                rec.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            }, index * 100);
        });
    }

    /**
     * Determine recommendation type based on content
     */
    getRecommendationType(recommendation) {
        const lowerRec = recommendation.toLowerCase();
        
        if (lowerRec.includes('conversation') || lowerRec.includes('discuss')) {
            return 'conversation';
        } else if (lowerRec.includes('explore') || lowerRec.includes('investigate')) {
            return 'exploration';
        } else if (lowerRec.includes('connect') || lowerRec.includes('bridge')) {
            return 'connection';
        } else if (lowerRec.includes('reflect') || lowerRec.includes('consider')) {
            return 'reflection';
        } else {
            return 'general';
        }
    }

    /**
     * Get appropriate icon for recommendation type
     */
    getRecommendationIcon(type) {
        const icons = {
            conversation: '💬',
            exploration: '🔍',
            connection: '🌉',
            reflection: '🤔',
            general: '💡'
        };
        return icons[type] || '💡';
    }

    /**
     * Determine recommendation priority based on content
     */
    getRecommendationPriority(recommendation) {
        const lowerRec = recommendation.toLowerCase();
        
        if (lowerRec.includes('important') || lowerRec.includes('critical') || lowerRec.includes('urgent')) {
            return 'high';
        } else if (lowerRec.includes('consider') || lowerRec.includes('might')) {
            return 'medium';
        } else {
            return 'normal';
        }
    }

    /**
     * Static method to reset the chart manager singleton (useful for testing)
     */
    static resetChartManager() {
        if (Dashboard.chartManagerInstance) {
            if (Dashboard.chartManagerInstance.destroy && typeof Dashboard.chartManagerInstance.destroy === 'function') {
                Dashboard.chartManagerInstance.destroy();
            }
            Dashboard.chartManagerInstance = null;
            Dashboard.chartManagerRefCount = 0;
            console.log('Chart manager singleton forcefully reset');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize dashboard if we have the required elements
    const hasLoadingState = document.getElementById('loading-state');
    const hasDashboardContent = document.getElementById('dashboard-content-inner');

    if (hasLoadingState || hasDashboardContent) {
        // Ensure only one instance is created and attach it to the window object.
        // This prevents duplicate initializations from other scripts like chat.js.
        if (!window.dashboard) {
            window.dashboard = new Dashboard();
        }
    } else {
        console.log('Dashboard elements not found, skipping dashboard initialization');
    }
});