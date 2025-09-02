/**
 * Enhanced Loading States and User Feedback System
 * 
 * Handles streaming indicators, chart loading states, visual confirmations,
 * connection status indicators, and error recovery options
 */

class LoadingFeedbackManager {
    constructor() {
        this.connectionStatus = 'connected';
        this.aiServiceStatus = 'ready';
        this.activeNotifications = new Set();
        this.performanceThresholds = {
            slow: 3000,      // 3 seconds
            verySlow: 8000   // 8 seconds
        };
        
        this.init();
    }
    
    init() {
        this.initializeStatusIndicators();
        this.setupPerformanceMonitoring();
        this.bindEvents();
        
        // Test connection status on initialization
        this.testConnectionStatus();
        
        console.log('LoadingFeedbackManager initialized');
    }
    
    /**
     * Initialize status indicators in the header
     */
    initializeStatusIndicators() {
        const connectionStatus = document.getElementById('connection-status');
        const aiServiceStatus = document.getElementById('ai-service-status');
        
        if (connectionStatus) {
            this.updateConnectionStatus('connected');
        }
        
        if (aiServiceStatus) {
            this.updateAIServiceStatus('ready');
        }
    }
    
    /**
     * Setup performance monitoring for responses
     */
    setupPerformanceMonitoring() {
        this.performanceMetrics = {
            responseTimeHistory: [],
            averageResponseTime: 0,
            slowResponseCount: 0
        };
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Listen for streaming events
        document.addEventListener('streamingStarted', (e) => {
            this.handleStreamingStarted(e.detail);
        });
        
        document.addEventListener('streamingCompleted', (e) => {
            this.handleStreamingCompleted(e.detail);
        });
        
        document.addEventListener('streamingError', (e) => {
            this.handleStreamingError(e.detail);
        });
        
        // Listen for chart events
        document.addEventListener('chartLoadingStarted', (e) => {
            this.handleChartLoadingStarted(e.detail);
        });
        
        document.addEventListener('chartLoadingCompleted', (e) => {
            this.handleChartLoadingCompleted(e.detail);
        });
        
        document.addEventListener('chartError', (e) => {
            this.handleChartError(e.detail);
        });
        
        // Close notifications on click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('performance-notification-close')) {
                this.closeNotification(e.target.closest('.performance-notification'));
            }
        });
    }
    
    /**
     * Update connection status indicator
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        this.connectionStatus = status;
        
        // Remove all status classes
        statusElement.classList.remove('connected', 'connecting', 'disconnected');
        statusElement.classList.add(status);
        
        const statusText = {
            'connected': 'ONLINE',
            'connecting': 'CONNECTING',
            'disconnected': 'OFFLINE'
        };
        
        statusElement.querySelector('span').textContent = statusText[status] || 'UNKNOWN';
        
        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('connectionStatusChanged', {
            detail: { status }
        }));
    }
    
    /**
     * Update AI service status indicator
     */
    updateAIServiceStatus(status) {
        const statusElement = document.getElementById('ai-service-status');
        if (!statusElement) return;
        
        this.aiServiceStatus = status;
        
        // Remove all status classes
        statusElement.classList.remove('ready', 'processing', 'error');
        statusElement.classList.add(status);
        
        const statusText = {
            'ready': 'AI READY',
            'processing': 'AI PROCESSING',
            'error': 'AI ERROR'
        };
        
        statusElement.querySelector('span').textContent = statusText[status] || 'AI UNKNOWN';
        
        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('aiServiceStatusChanged', {
            detail: { status }
        }));
    }
    
    /**
     * Test connection status by making a lightweight request
     */
    async testConnectionStatus() {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout

        try {
            this.updateConnectionStatus('connecting');
            
            const response = await fetch('/api/health', {
                method: 'GET',
                signal: controller.signal // Use AbortController for timeout
            });

            // Clear the timeout if the request completes in time
            clearTimeout(timeoutId);
            
            if (response.ok) {
                this.updateConnectionStatus('connected');
            } else {
                this.updateConnectionStatus('disconnected');
            }
        } catch (error) {
            clearTimeout(timeoutId); // Also clear timeout on error
            console.warn('Connection test failed:', error);
            this.updateConnectionStatus('disconnected');
        }
    }
    
    /**
     * Create streaming indicator with typing dots animation
     */
    createStreamingIndicator(container, message = 'Synapse is thinking...') {
        const indicator = document.createElement('div');
        indicator.classList.add('streaming-indicator');
        indicator.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span class="streaming-text">${message}</span>
        `;
        
        container.appendChild(indicator);
        return indicator;
    }
    
    /**
     * Create streaming progress bar
     */
    createStreamingProgress(container) {
        const progress = document.createElement('div');
        progress.classList.add('streaming-progress');
        progress.innerHTML = '<div class="streaming-progress-bar"></div>';
        
        container.appendChild(progress);
        return progress;
    }
    
    /**
     * Handle streaming started event
     */
    handleStreamingStarted(detail) {
        this.updateAIServiceStatus('processing');
        
        // Track start time for performance monitoring
        if (detail.requestId) {
            this.trackRequestStart(detail.requestId);
        }
        
        console.log('Streaming started:', detail);
    }
    
    /**
     * Handle streaming completed event
     */
    handleStreamingCompleted(detail) {
        this.updateAIServiceStatus('ready');
        
        // Track completion for performance monitoring
        if (detail.requestId) {
            this.trackRequestCompletion(detail.requestId, detail.responseTime);
        }
        
        // Show success indicator
        this.showSuccessIndicator(detail.container, 'Response completed');
        
        console.log('Streaming completed:', detail);
    }
    
    /**
     * Handle streaming error event
     */
    handleStreamingError(detail) {
        this.updateAIServiceStatus('error');
        
        // Show error recovery options
        // Handle different container property names from different sources
        const container = detail.container || detail.responseElement;
        this.showStreamingErrorRecovery(container, detail.error, detail.options);
        
        console.error('Streaming error:', detail);
    }
    
    /**
     * Show streaming error recovery options
     */
    showStreamingErrorRecovery(container, error, options = {}) {
        // Validate container exists and is a DOM element
        if (!container || typeof container.innerHTML === 'undefined') {
            console.warn('Invalid container provided to showStreamingErrorRecovery:', container);
            return;
        }
        
        const errorContent = document.createElement('div');
        errorContent.classList.add('streaming-error-content');
        
        const errorType = this.categorizeError(error);
        const errorConfig = this.getErrorConfig(errorType, error);
        
        errorContent.innerHTML = `
            <div class="streaming-error-header">
                <div class="streaming-error-icon">${errorConfig.icon}</div>
                <div class="streaming-error-title">${errorConfig.title}</div>
            </div>
            <div class="streaming-error-message">${errorConfig.message}</div>
            <div class="streaming-error-actions">
                ${errorConfig.actions.map(action => `
                    <button class="streaming-retry-button ${action.primary ? 'primary' : 'secondary'}" 
                            data-action="${action.action}">
                        ${action.text}
                    </button>
                `).join('')}
            </div>
        `;
        
        // Add event listeners for action buttons
        errorConfig.actions.forEach(action => {
            const button = errorContent.querySelector(`[data-action="${action.action}"]`);
            if (button) {
                button.addEventListener('click', () => {
                    this.handleErrorAction(action.action, container, options);
                });
            }
        });
        
        // Replace container content with error
        container.innerHTML = '';
        container.appendChild(errorContent);
    }
    
    /**
     * Categorize error type for appropriate handling
     */
    categorizeError(error) {
        if (error.name === 'AbortError' || error.message.includes('timeout')) {
            return 'timeout';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
            return 'network';
        } else if (error.message.includes('AI service') || error.message.includes('Ollama')) {
            return 'ai_service';
        } else if (error.message.includes('validation') || error.message.includes('Invalid')) {
            return 'validation';
        } else {
            return 'generic';
        }
    }
    
    /**
     * Get error configuration for different error types
     */
    getErrorConfig(errorType, error) {
        const configs = {
            timeout: {
                icon: '⏱️',
                title: 'Response Timeout',
                message: 'The AI is taking longer than expected. This might be a complex query.',
                actions: [
                    { text: 'Retry Streaming', action: 'retry_streaming', primary: true },
                    { text: 'Use Standard Mode', action: 'fallback_standard', primary: false }
                ]
            },
            network: {
                icon: '🌐',
                title: 'Connection Error',
                message: 'Unable to establish streaming connection. Check your network connection.',
                actions: [
                    { text: 'Retry Connection', action: 'retry_streaming', primary: true },
                    { text: 'Use Standard Mode', action: 'fallback_standard', primary: false }
                ]
            },
            ai_service: {
                icon: '🤖',
                title: 'AI Service Error',
                message: 'The AI service is currently unavailable. Please ensure Ollama is running.',
                actions: [
                    { text: 'Retry', action: 'retry_streaming', primary: true },
                    { text: 'Check Service', action: 'check_service', primary: false }
                ]
            },
            validation: {
                icon: '⚠️',
                title: 'Input Error',
                message: 'There was an issue with your message format. Please try rephrasing.',
                actions: [
                    { text: 'Edit Message', action: 'edit_message', primary: true }
                ]
            },
            generic: {
                icon: '❌',
                title: 'Unexpected Error',
                message: error.message || 'An unexpected error occurred during streaming.',
                actions: [
                    { text: 'Try Standard Mode', action: 'fallback_standard', primary: true }
                ]
            }
        };
        
        return configs[errorType] || configs.generic;
    }
    
    /**
     * Handle error action button clicks
     */
    handleErrorAction(action, container, options) {
        switch (action) {
            case 'retry_streaming':
                this.retryStreaming(container, options);
                break;
            case 'fallback_standard':
                this.fallbackToStandard(container, options);
                break;
            case 'check_service':
                this.checkAIService();
                break;
            case 'edit_message':
                this.focusMessageInput();
                break;
        }
    }
    
    /**
     * Retry streaming with the same parameters
     */
    async retryStreaming(container, options) {
        // Validate container exists
        if (!container || typeof container.innerHTML === 'undefined') {
            console.warn('Invalid container provided to retryStreaming:', container);
            return;
        }
        
        // Clear error content
        container.innerHTML = '';
        
        // Show loading indicator
        this.createStreamingIndicator(container, 'Retrying...');
        
        // Dispatch retry event
        document.dispatchEvent(new CustomEvent('retryStreaming', {
            detail: { container, options }
        }));
    }
    
    /**
     * Fallback to standard (non-streaming) mode
     */
    fallbackToStandard(container, options) {
        // Validate container exists
        if (!container || typeof container.innerHTML === 'undefined') {
            console.warn('Invalid container provided to fallbackToStandard:', container);
            return;
        }
        
        // Clear error content
        container.innerHTML = '';
        
        // Show loading indicator
        this.createStreamingIndicator(container, 'Switching to standard mode...');
        
        // Dispatch fallback event
        document.dispatchEvent(new CustomEvent('fallbackToStandard', {
            detail: { container, options }
        }));
    }
    
    /**
     * Check AI service status
     */
    async checkAIService() {
        this.updateAIServiceStatus('processing');
        
        try {
            const response = await fetch('/api/health');
            if (response.ok) {
                this.updateAIServiceStatus('ready');
                this.showSuccessNotification('AI service is running properly');
            } else {
                this.updateAIServiceStatus('error');
                this.showErrorNotification('AI service is not responding');
            }
        } catch (error) {
            this.updateAIServiceStatus('error');
            this.showErrorNotification('Unable to connect to AI service');
        }
    }
    
    /**
     * Focus message input for editing
     */
    focusMessageInput() {
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.focus();
            messageInput.select();
        }
    }
    
    /**
     * Create chart loading skeleton
     */
    createChartLoadingSkeleton(container, chartType = 'default') {
        const skeleton = document.createElement('div');
        skeleton.classList.add('chart-loading-skeleton');
        
        let skeletonContent = '';
        
        switch (chartType) {
            case 'radar':
                skeletonContent = '<div class="skeleton-radar"></div>';
                break;
            case 'bar':
                skeletonContent = `
                    <div class="skeleton-bars">
                        <div class="skeleton-bar"></div>
                        <div class="skeleton-bar"></div>
                        <div class="skeleton-bar"></div>
                        <div class="skeleton-bar"></div>
                    </div>
                `;
                break;
            case 'doughnut':
                skeletonContent = '<div class="skeleton-doughnut"></div>';
                break;
            default:
                skeletonContent = `
                    <div class="skeleton-chart">
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line short"></div>
                    </div>
                `;
        }
        
        skeleton.innerHTML = skeletonContent;
        container.appendChild(skeleton);
        
        return skeleton;
    }
    
    /**
     * Handle chart loading started event
     */
    handleChartLoadingStarted(detail) {
        const { chartId, chartType } = detail;
        const container = document.getElementById(`${chartId}-container`);
        const statusElement = document.getElementById(`${chartId}-status`);
        
        if (container) {
            // Hide canvas and show skeleton
            const canvas = container.querySelector('canvas');
            if (canvas) {
                canvas.style.display = 'none';
            }
            
            // Create loading skeleton
            this.createChartLoadingSkeleton(container.querySelector('.chart-wrapper'), chartType);
        }
        
        if (statusElement) {
            statusElement.textContent = 'Loading...';
            statusElement.className = 'chart-status loading';
        }
        
        console.log('Chart loading started:', detail);
    }
    
    /**
     * Handle chart loading completed event
     */
    handleChartLoadingCompleted(detail) {
        const { chartId } = detail;
        const container = document.getElementById(`${chartId}-container`);
        const statusElement = document.getElementById(`${chartId}-status`);
        
        if (container) {
            // Remove skeleton and show canvas
            const skeleton = container.querySelector('.chart-loading-skeleton');
            if (skeleton) {
                skeleton.remove();
            }
            
            const canvas = container.querySelector('canvas');
            if (canvas) {
                canvas.style.display = 'block';
            }
        }
        
        if (statusElement) {
            statusElement.textContent = 'Ready';
            statusElement.className = 'chart-status success';
        }
        
        console.log('Chart loading completed:', detail);
    }
    
    /**
     * Handle chart error event
     */
    handleChartError(detail) {
        const { chartId, error } = detail;
        const container = document.getElementById(`${chartId}-container`);
        const statusElement = document.getElementById(`${chartId}-status`);
        
        if (container) {
            this.showChartErrorState(container, error);
        }
        
        if (statusElement) {
            statusElement.textContent = 'Error';
            statusElement.className = 'chart-status error';
        }
        
        console.error('Chart error:', detail);
    }
    
    /**
     * Show chart error state
     */
    showChartErrorState(container, error) {
        const wrapper = container.querySelector('.chart-wrapper');
        if (!wrapper) return;
        
        // Hide canvas and skeleton
        const canvas = wrapper.querySelector('canvas');
        const skeleton = wrapper.querySelector('.chart-loading-skeleton');
        
        if (canvas) canvas.style.display = 'none';
        if (skeleton) skeleton.remove();
        
        // Create error state
        const errorState = document.createElement('div');
        errorState.classList.add('chart-error-state');
        errorState.innerHTML = `
            <div class="error-icon">⚠️</div>
            <h4>Chart Unavailable</h4>
            <p>${error.message || 'Unable to load chart data'}</p>
            <button class="retry-chart-button" onclick="window.loadingFeedbackManager?.retryChart('${container.id}')">
                Retry
            </button>
        `;
        
        wrapper.appendChild(errorState);
    }
    
    /**
     * Retry chart loading
     */
    retryChart(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Remove error state
        const errorState = container.querySelector('.chart-error-state');
        if (errorState) {
            errorState.remove();
        }
        
        // Show canvas
        const canvas = container.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'block';
        }
        
        // Dispatch retry event
        const chartId = containerId.replace('-container', '');
        document.dispatchEvent(new CustomEvent('retryChart', {
            detail: { chartId }
        }));
    }
    
    /**
     * Show success indicator
     */
    showSuccessIndicator(container, message) {
        const indicator = document.createElement('div');
        indicator.classList.add('success-indicator');
        indicator.textContent = message;
        
        container.appendChild(indicator);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.remove();
            }
        }, 3000);
    }
    
    /**
     * Track request start time for performance monitoring
     */
    trackRequestStart(requestId) {
        if (!this.requestTimes) {
            this.requestTimes = new Map();
        }
        
        this.requestTimes.set(requestId, Date.now());
    }
    
    /**
     * Track request completion and update performance metrics
     */
    trackRequestCompletion(requestId, responseTime) {
        if (!this.requestTimes) return;
        
        const startTime = this.requestTimes.get(requestId);
        if (startTime) {
            const actualResponseTime = responseTime || (Date.now() - startTime);
            
            // Update performance metrics
            this.performanceMetrics.responseTimeHistory.push(actualResponseTime);
            
            // Keep only last 10 response times
            if (this.performanceMetrics.responseTimeHistory.length > 10) {
                this.performanceMetrics.responseTimeHistory.shift();
            }
            
            // Calculate average
            this.performanceMetrics.averageResponseTime = 
                this.performanceMetrics.responseTimeHistory.reduce((a, b) => a + b, 0) / 
                this.performanceMetrics.responseTimeHistory.length;
            
            // Check if response was slow
            if (actualResponseTime > this.performanceThresholds.slow) {
                this.performanceMetrics.slowResponseCount++;
                this.showPerformanceNotification(actualResponseTime);
            }
            
            this.requestTimes.delete(requestId);
        }
    }
    
    /**
     * Show performance notification for slow responses
     */
    showPerformanceNotification(responseTime) {
        const isVerySlow = responseTime > this.performanceThresholds.verySlow;
        
        const notification = document.createElement('div');
        notification.classList.add('performance-notification');
        notification.innerHTML = `
            <button class="performance-notification-close">×</button>
            <div class="performance-notification-header">
                <div class="performance-notification-icon">${isVerySlow ? '🐌' : '⏱️'}</div>
                <div class="performance-notification-title">
                    ${isVerySlow ? 'Very Slow Response' : 'Slow Response'}
                </div>
            </div>
            <div class="performance-notification-message">
                Response took ${Math.round(responseTime / 1000)}s. 
                ${isVerySlow ? 
                    'Consider checking your AI service configuration.' : 
                    'This might be due to a complex query.'}
            </div>
        `;
        
        document.body.appendChild(notification);
        this.activeNotifications.add(notification);
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            this.closeNotification(notification);
        }, 8000);
    }
    
    /**
     * Show success notification
     */
    showSuccessNotification(message) {
        const notification = document.createElement('div');
        notification.classList.add('performance-notification');
        notification.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        notification.innerHTML = `
            <button class="performance-notification-close">×</button>
            <div class="performance-notification-header">
                <div class="performance-notification-icon" style="color: #10B981;">✓</div>
                <div class="performance-notification-title">Success</div>
            </div>
            <div class="performance-notification-message">${message}</div>
        `;
        
        document.body.appendChild(notification);
        this.activeNotifications.add(notification);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            this.closeNotification(notification);
        }, 4000);
    }
    
    /**
     * Show error notification
     */
    showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.classList.add('performance-notification');
        notification.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        notification.innerHTML = `
            <button class="performance-notification-close">×</button>
            <div class="performance-notification-header">
                <div class="performance-notification-icon" style="color: #EF4444;">⚠️</div>
                <div class="performance-notification-title">Error</div>
            </div>
            <div class="performance-notification-message">${message}</div>
        `;
        
        document.body.appendChild(notification);
        this.activeNotifications.add(notification);
        
        // Auto-remove after 6 seconds
        setTimeout(() => {
            this.closeNotification(notification);
        }, 6000);
    }
    
    /**
     * Close notification
     */
    closeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.style.animation = 'notification-slide-out 0.3s ease-in forwards';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
                this.activeNotifications.delete(notification);
            }, 300);
        }
    }
    
    /**
     * Get current performance metrics
     */
    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            connectionStatus: this.connectionStatus,
            aiServiceStatus: this.aiServiceStatus
        };
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        // Close all active notifications
        this.activeNotifications.forEach(notification => {
            this.closeNotification(notification);
        });
        
        // Clear request times
        if (this.requestTimes) {
            this.requestTimes.clear();
        }
    }
}

// Add slide-out animation to CSS
const slideOutStyle = document.createElement('style');
slideOutStyle.textContent = `
    @keyframes notification-slide-out {
        0% {
            opacity: 1;
            transform: translateX(0);
        }
        100% {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(slideOutStyle);

// Initialize loading feedback manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.loadingFeedbackManager = new LoadingFeedbackManager();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.loadingFeedbackManager) {
        window.loadingFeedbackManager.cleanup();
    }
});