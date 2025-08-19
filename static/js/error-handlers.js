/**
 * Comprehensive Error Handling System for Synapse AI Web Application
 * 
 * Provides StreamingErrorHandler and ChartErrorHandler classes with
 * user-friendly error messages, recovery suggestions, and retry options
 */

/**
 * StreamingErrorHandler - Handles streaming connection failures and timeouts
 */
class StreamingErrorHandler {
    constructor(chatInterface) {
        this.chatInterface = chatInterface;
        this.retryAttempts = 0;
        this.maxRetries = 3;
        this.retryDelay = 2000; // 2 seconds
        this.timeoutDuration = 120000; // 2 minutes base timeout, will be adaptive
        this.errorLog = [];
    }
    
    /**
     * Handle streaming errors with appropriate recovery strategies
     */
    handleStreamingError(error, responseElement, requestStartTime, requestId) {
        console.error('Streaming error:', error);
        
        // Log error for debugging
        this.logError('streaming', error, {
            requestId,
            responseTime: Date.now() - requestStartTime,
            retryAttempts: this.retryAttempts,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        });
        
        // Remove streaming indicators
        responseElement.classList.remove('streaming');
        responseElement.classList.add('streaming-error');
        
        // Determine error type and recovery strategy
        const errorType = this.categorizeError(error);
        this.showErrorUI(responseElement, errorType, error);
        
        // Dispatch error event for other components
        document.dispatchEvent(new CustomEvent('streamingError', {
            detail: { 
                error, 
                errorType, 
                requestId,
                responseElement,
                canRetry: this.retryAttempts < this.maxRetries
            }
        }));
    }
    
    /**
     * Categorize error types for appropriate handling
     */
    categorizeError(error) {
        if (error.name === 'AbortError') {
            return 'timeout';
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return 'network';
        } else if (error.message.includes('AI service') || error.message.includes('Ollama')) {
            return 'ai_service';
        } else if (error.message.includes('timeout')) {
            return 'timeout';
        } else if (error.message.includes('validation') || error.message.includes('Invalid')) {
            return 'validation';
        } else if (error.message.includes('rate limit') || error.message.includes('429')) {
            return 'rate_limit';
        } else if (error.message.includes('server') || error.message.includes('500')) {
            return 'server_error';
        } else {
            return 'unknown';
        }
    }
    
    /**
     * Show error UI with recovery options
     */
    showErrorUI(responseElement, errorType, error) {
        const contentElement = responseElement.querySelector('.message-content');
        if (!contentElement) return;
        
        const errorConfig = this.getErrorConfig(errorType, error);
        
        contentElement.innerHTML = `
            <div class="streaming-error-container">
                <div class="error-header">
                    <div class="error-icon">${errorConfig.icon}</div>
                    <h4 class="error-title">${errorConfig.title}</h4>
                </div>
                <div class="error-content">
                    <p class="error-message">${errorConfig.message}</p>
                    ${errorConfig.suggestion ? `<p class="error-suggestion">${errorConfig.suggestion}</p>` : ''}
                </div>
                <div class="error-actions">
                    ${this.generateErrorActions(errorType, responseElement)}
                </div>
                ${this.retryAttempts > 0 ? `<div class="retry-info">Retry attempt: ${this.retryAttempts}/${this.maxRetries}</div>` : ''}
            </div>
        `;
    }
    
    /**
     * Get error configuration based on error type
     */
    getErrorConfig(errorType, error) {
        const configs = {
            timeout: {
                icon: '⏱️',
                title: 'Response Timeout',
                message: 'The AI is taking longer than expected to respond. This might be a complex query.',
                suggestion: 'Try simplifying your question or check if the AI service is running properly.'
            },
            network: {
                icon: '🌐',
                title: 'Connection Error',
                message: 'Unable to connect to the server. Please check your internet connection.',
                suggestion: 'Verify your network connection and try again.'
            },
            ai_service: {
                icon: '🤖',
                title: 'AI Service Unavailable',
                message: 'The AI service is currently unavailable or not responding.',
                suggestion: 'Please ensure Ollama is running and the AI model is loaded.'
            },
            rate_limit: {
                icon: '🚦',
                title: 'Rate Limit Exceeded',
                message: 'Too many requests have been sent. Please wait before trying again.',
                suggestion: 'Wait a moment before sending your next message.'
            },
            server_error: {
                icon: '⚠️',
                title: 'Server Error',
                message: 'The server encountered an error while processing your request.',
                suggestion: 'This is usually temporary. Please try again in a moment.'
            },
            validation: {
                icon: '❌',
                title: 'Invalid Request',
                message: 'There was an issue with your message format.',
                suggestion: 'Please try rephrasing your message and send it again.'
            },
            unknown: {
                icon: '❓',
                title: 'Unexpected Error',
                message: error.message || 'An unexpected error occurred.',
                suggestion: 'Please try again. If the problem persists, check the console for more details.'
            }
        };
        
        return configs[errorType] || configs.unknown;
    }
    
    /**
     * Generate error action buttons based on error type
     */
    generateErrorActions(errorType, responseElement) {
        const actions = [];
        
        // Retry action (if retries available)
        if (this.retryAttempts < this.maxRetries && errorType !== 'validation') {
            actions.push(`
                <button class="error-action-button retry-button" onclick="window.streamingErrorHandler.retryStreaming('${responseElement.id}')">
                    <span class="button-icon">🔄</span>
                    Retry Streaming
                </button>
            `);
        }
        
        // Fallback to standard mode
        if (errorType !== 'validation') {
            actions.push(`
                <button class="error-action-button fallback-button" onclick="window.streamingErrorHandler.fallbackToStandard('${responseElement.id}')">
                    <span class="button-icon">📝</span>
                    Use Standard Mode
                </button>
            `);
        }
        
        // Refresh page for severe errors
        if (['server_error', 'unknown'].includes(errorType)) {
            actions.push(`
                <button class="error-action-button refresh-button" onclick="window.location.reload()">
                    <span class="button-icon">🔄</span>
                    Refresh Page
                </button>
            `);
        }
        
        // Show error details for debugging
        actions.push(`
            <button class="error-action-button details-button" onclick="window.streamingErrorHandler.showErrorDetails('${responseElement.id}')">
                <span class="button-icon">🔍</span>
                Show Details
            </button>
        `);
        
        return actions.join('');
    }
    
    /**
     * Retry streaming with exponential backoff
     */
    async retryStreaming(elementId) {
        const responseElement = document.getElementById(elementId);
        if (!responseElement) return;
        
        this.retryAttempts++;
        
        // Show retry loading state
        const contentElement = responseElement.querySelector('.message-content');
        contentElement.innerHTML = `
            <div class="retry-loading">
                <div class="loading-spinner"></div>
                <p>Retrying... (${this.retryAttempts}/${this.maxRetries})</p>
            </div>
        `;
        
        // Wait with exponential backoff
        const delay = this.retryDelay * Math.pow(2, this.retryAttempts - 1);
        await this.sleep(delay);
        
        try {
            // Get the original message from conversation history
            const originalMessage = this.getOriginalMessage(responseElement);
            if (!originalMessage) {
                throw new Error('Could not find original message to retry');
            }
            
            // Retry streaming
            if (window.streamingResponseHandler) {
                await window.streamingResponseHandler.handleStreamingResponse(
                    responseElement, 
                    Date.now()
                );
            } else {
                throw new Error('Streaming handler not available');
            }
            
            // Reset retry count on success
            this.retryAttempts = 0;
            
        } catch (error) {
            console.error('Retry failed:', error);
            
            if (this.retryAttempts >= this.maxRetries) {
                // Max retries reached, fallback to standard mode
                this.fallbackToStandard(elementId);
            } else {
                // Show error and allow another retry
                this.handleStreamingError(error, responseElement, Date.now(), 'retry_' + Date.now());
            }
        }
    }
    
    /**
     * Fallback to standard (non-streaming) mode
     */
    async fallbackToStandard(elementId) {
        const responseElement = document.getElementById(elementId);
        if (!responseElement) return;
        
        const contentElement = responseElement.querySelector('.message-content');
        contentElement.innerHTML = `
            <div class="fallback-loading">
                <div class="loading-spinner"></div>
                <p>Switching to standard mode...</p>
            </div>
        `;
        
        try {
            // Get conversation history
            const conversation = window.conversationHistory || [];
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation: conversation,
                    stream: false
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.message || 'Unknown error occurred');
            }
            
            // Display response
            contentElement.innerHTML = `
                <div class="standard-response">
                    <div class="response-text">${data.response}</div>
                    <div class="response-mode-indicator">Standard Mode</div>
                </div>
            `;
            
            // Update conversation history
            if (window.conversationHistory) {
                window.conversationHistory.push({
                    role: 'assistant',
                    content: data.response,
                    timestamp: new Date().toISOString(),
                    mode: 'standard'
                });
                
                if (window.saveConversationToStorage) {
                    window.saveConversationToStorage();
                }
            }
            
            // Remove error classes
            responseElement.classList.remove('streaming-error');
            responseElement.classList.add('standard-response');
            
            // Reset retry count
            this.retryAttempts = 0;
            
        } catch (error) {
            console.error('Standard mode fallback failed:', error);
            this.showFinalError(responseElement, error);
        }
    }
    
    /**
     * Show error details for debugging
     */
    showErrorDetails(elementId) {
        const responseElement = document.getElementById(elementId);
        if (!responseElement) return;
        
        const recentErrors = this.errorLog.slice(-5); // Show last 5 errors
        
        const detailsHTML = `
            <div class="error-details-modal">
                <div class="error-details-content">
                    <h4>Error Details</h4>
                    <div class="error-log">
                        ${recentErrors.map(log => `
                            <div class="error-log-entry">
                                <div class="error-timestamp">${new Date(log.timestamp).toLocaleString()}</div>
                                <div class="error-type">${log.type}</div>
                                <div class="error-message">${log.error.message}</div>
                                <div class="error-metadata">
                                    ${Object.entries(log.metadata).map(([key, value]) => 
                                        `<span class="metadata-item">${key}: ${value}</span>`
                                    ).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="error-details-actions">
                        <button onclick="this.closest('.error-details-modal').remove()">Close</button>
                        <button onclick="window.streamingErrorHandler.copyErrorLog()">Copy Log</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', detailsHTML);
    }
    
    /**
     * Show final error when all recovery attempts fail
     */
    showFinalError(responseElement, error) {
        const contentElement = responseElement.querySelector('.message-content');
        contentElement.innerHTML = `
            <div class="final-error">
                <div class="error-icon">💥</div>
                <h4>Unable to Process Request</h4>
                <p>All recovery attempts have failed. Please try refreshing the page or check your connection.</p>
                <div class="final-error-actions">
                    <button onclick="window.location.reload()" class="error-action-button">
                        Refresh Page
                    </button>
                    <button onclick="window.streamingErrorHandler.reportError('${error.message}')" class="error-action-button">
                        Report Issue
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Get original message for retry
     */
    getOriginalMessage(responseElement) {
        // Try to find the user message that preceded this AI response
        const messages = Array.from(document.querySelectorAll('.message'));
        const responseIndex = messages.indexOf(responseElement);
        
        if (responseIndex > 0) {
            const userMessage = messages[responseIndex - 1];
            if (userMessage.classList.contains('user-message')) {
                return userMessage.querySelector('.message-content').textContent;
            }
        }
        
        return null;
    }
    
    /**
     * Log error for debugging and analytics
     */
    logError(type, error, metadata = {}) {
        const errorLog = {
            type,
            error: {
                name: error.name,
                message: error.message,
                stack: error.stack
            },
            metadata,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        this.errorLog.push(errorLog);
        
        // Keep only last 50 errors to prevent memory issues
        if (this.errorLog.length > 50) {
            this.errorLog = this.errorLog.slice(-50);
        }
        
        // Send to server for logging (if endpoint exists)
        this.sendErrorToServer(errorLog);
    }
    
    /**
     * Send error to server for logging
     */
    async sendErrorToServer(errorLog) {
        try {
            await fetch('/api/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(errorLog)
            });
        } catch (e) {
            // Silently fail if logging endpoint is not available
            console.warn('Could not send error log to server:', e);
        }
    }
    
    /**
     * Copy error log to clipboard
     */
    copyErrorLog() {
        const logText = this.errorLog.map(log => 
            `[${log.timestamp}] ${log.type}: ${log.error.message}\n${JSON.stringify(log.metadata, null, 2)}`
        ).join('\n\n');
        
        navigator.clipboard.writeText(logText).then(() => {
            alert('Error log copied to clipboard');
        }).catch(() => {
            console.error('Failed to copy error log');
        });
    }
    
    /**
     * Report error to support
     */
    reportError(errorMessage) {
        const reportData = {
            error: errorMessage,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            recentErrors: this.errorLog.slice(-3)
        };
        
        // This could open a support form or send to a support endpoint
        console.log('Error report:', reportData);
        alert('Error report generated. Check console for details.');
    }
    
    /**
     * Utility function for delays
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Reset error handler state
     */
    reset() {
        this.retryAttempts = 0;
        this.errorLog = [];
    }
    
    /**
     * Get error statistics
     */
    getErrorStats() {
        const stats = {
            totalErrors: this.errorLog.length,
            errorsByType: {},
            recentErrors: this.errorLog.slice(-10)
        };
        
        this.errorLog.forEach(log => {
            stats.errorsByType[log.type] = (stats.errorsByType[log.type] || 0) + 1;
        });
        
        return stats;
    }
}

/**
 * ChartErrorHandler - Handles chart rendering errors and data loading failures
 */
class ChartErrorHandler {
    constructor(chartManager) {
        this.chartManager = chartManager;
        this.errorLog = [];
        this.retryAttempts = {};
        this.maxRetries = 3;
    }
    
    /**
     * Handle chart-specific errors
     */
    handleChartError(chartId, chartType, error, context = {}) {
        console.error(`Chart error (${chartId}):`, error);
        
        // Log error for debugging
        this.logError(chartId, chartType, error, context);
        
        // Show error state in chart container
        this.showChartErrorState(chartId, chartType, error);
        
        // Dispatch error event
        document.dispatchEvent(new CustomEvent('chartError', {
            detail: { 
                chartId, 
                chartType, 
                error,
                context,
                canRetry: (this.retryAttempts[chartId] || 0) < this.maxRetries
            }
        }));
    }
    
    /**
     * Show error state in chart container
     */
    showChartErrorState(chartId, chartType, error) {
        const container = document.getElementById(`${chartId}-container`);
        if (!container) return;
        
        const errorType = this.categorizeChartError(error);
        const errorConfig = this.getChartErrorConfig(errorType, chartType);
        
        // Hide chart canvas
        const canvas = container.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'none';
        }
        
        // Remove any existing error states
        const existingError = container.querySelector('.chart-error-state');
        if (existingError) {
            existingError.remove();
        }
        
        // Create error state element
        const errorElement = document.createElement('div');
        errorElement.className = 'chart-error-state';
        errorElement.innerHTML = `
            <div class="chart-error-content">
                <div class="error-icon">${errorConfig.icon}</div>
                <h4 class="error-title">${errorConfig.title}</h4>
                <p class="error-message">${errorConfig.message}</p>
                ${errorConfig.suggestion ? `<p class="error-suggestion">${errorConfig.suggestion}</p>` : ''}
                <div class="chart-error-actions">
                    ${this.generateChartErrorActions(chartId, chartType, errorType)}
                </div>
                ${this.retryAttempts[chartId] ? `<div class="retry-info">Retry attempt: ${this.retryAttempts[chartId]}/${this.maxRetries}</div>` : ''}
            </div>
        `;
        
        container.appendChild(errorElement);
        
        // Update chart status
        this.updateChartStatus(chartId, 'Error', 'error');
    }
    
    /**
     * Categorize chart error types
     */
    categorizeChartError(error) {
        if (error.message.includes('Canvas')) {
            return 'canvas_error';
        } else if (error.message.includes('data') || error.message.includes('dataset')) {
            return 'data_error';
        } else if (error.message.includes('fetch') || error.message.includes('network')) {
            return 'network_error';
        } else if (error.message.includes('Chart') || error.message.includes('chart')) {
            return 'chart_library_error';
        } else if (error.message.includes('memory') || error.message.includes('Memory')) {
            return 'memory_error';
        } else {
            return 'unknown_error';
        }
    }
    
    /**
     * Get chart error configuration
     */
    getChartErrorConfig(errorType, chartType) {
        const configs = {
            canvas_error: {
                icon: '🖼️',
                title: 'Canvas Error',
                message: `Unable to create ${chartType} chart canvas.`,
                suggestion: 'Try refreshing the page or check if your browser supports HTML5 Canvas.'
            },
            data_error: {
                icon: '📊',
                title: 'Data Error',
                message: `Invalid or missing data for ${chartType} chart.`,
                suggestion: 'Have more conversations to generate chart data, or try refreshing the charts.'
            },
            network_error: {
                icon: '🌐',
                title: 'Network Error',
                message: `Unable to load data for ${chartType} chart.`,
                suggestion: 'Check your internet connection and try again.'
            },
            chart_library_error: {
                icon: '📈',
                title: 'Chart Library Error',
                message: `Error in chart rendering library for ${chartType} chart.`,
                suggestion: 'This is usually temporary. Try refreshing the page.'
            },
            memory_error: {
                icon: '💾',
                title: 'Memory Error',
                message: `Insufficient memory to render ${chartType} chart.`,
                suggestion: 'Try closing other tabs or refreshing the page.'
            },
            unknown_error: {
                icon: '❓',
                title: 'Chart Error',
                message: `Unable to render ${chartType} chart.`,
                suggestion: 'Try refreshing the charts or the page.'
            }
        };
        
        return configs[errorType] || configs.unknown_error;
    }
    
    /**
     * Generate chart error action buttons
     */
    generateChartErrorActions(chartId, chartType, errorType) {
        const actions = [];
        
        // Retry action
        if ((this.retryAttempts[chartId] || 0) < this.maxRetries) {
            actions.push(`
                <button class="chart-error-button retry-button" onclick="window.chartErrorHandler.retryChart('${chartId}', '${chartType}')">
                    <span class="button-icon">🔄</span>
                    Retry
                </button>
            `);
        }
        
        // Refresh all charts
        actions.push(`
            <button class="chart-error-button refresh-button" onclick="window.chartErrorHandler.refreshAllCharts()">
                <span class="button-icon">🔄</span>
                Refresh All
            </button>
        `);
        
        // Show placeholder data
        if (errorType === 'data_error' || errorType === 'network_error') {
            actions.push(`
                <button class="chart-error-button placeholder-button" onclick="window.chartErrorHandler.showPlaceholderChart('${chartId}', '${chartType}')">
                    <span class="button-icon">📊</span>
                    Show Sample
                </button>
            `);
        }
        
        return actions.join('');
    }
    
    /**
     * Retry specific chart
     */
    async retryChart(chartId, chartType) {
        this.retryAttempts[chartId] = (this.retryAttempts[chartId] || 0) + 1;
        
        // Show loading state
        this.showChartLoadingState(chartId);
        
        try {
            // Wait a moment before retry
            await this.sleep(1000);
            
            // Retry chart creation through chart manager
            if (this.chartManager && typeof this.chartManager.refreshCharts === 'function') {
                await this.chartManager.refreshCharts();
            } else if (window.globalChartManager) {
                await window.globalChartManager.refreshCharts();
            } else {
                throw new Error('Chart manager not available');
            }
            
            // Reset retry count on success
            this.retryAttempts[chartId] = 0;
            
        } catch (error) {
            console.error(`Chart retry failed for ${chartId}:`, error);
            
            if (this.retryAttempts[chartId] >= this.maxRetries) {
                // Max retries reached, show final error
                this.showFinalChartError(chartId, chartType, error);
            } else {
                // Show error and allow another retry
                this.handleChartError(chartId, chartType, error, { isRetry: true });
            }
        }
    }
    
    /**
     * Refresh all charts
     */
    async refreshAllCharts() {
        // Reset all retry attempts
        this.retryAttempts = {};
        
        // Show loading states for all charts
        const chartIds = ['core-values', 'recurring-themes', 'emotional-landscape'];
        chartIds.forEach(chartId => {
            this.showChartLoadingState(chartId);
        });
        
        try {
            if (this.chartManager && typeof this.chartManager.refreshCharts === 'function') {
                await this.chartManager.refreshCharts();
            } else if (window.globalChartManager) {
                await window.globalChartManager.refreshCharts();
            } else {
                throw new Error('Chart manager not available');
            }
        } catch (error) {
            console.error('Failed to refresh all charts:', error);
            chartIds.forEach(chartId => {
                this.handleChartError(chartId, 'chart', error, { isRefreshAll: true });
            });
        }
    }
    
    /**
     * Show placeholder chart with sample data
     */
    showPlaceholderChart(chartId, chartType) {
        try {
            // Remove error state
            this.removeChartErrorState(chartId);
            
            // Show placeholder through chart manager
            if (this.chartManager && typeof this.chartManager.showChartPlaceholders === 'function') {
                this.chartManager.showChartPlaceholders();
            } else if (window.globalChartManager) {
                window.globalChartManager.showChartPlaceholders();
            }
            
            // Update status
            this.updateChartStatus(chartId, 'Sample Data', 'placeholder');
            
        } catch (error) {
            console.error(`Failed to show placeholder for ${chartId}:`, error);
            this.handleChartError(chartId, chartType, error, { isPlaceholder: true });
        }
    }
    
    /**
     * Show loading state for chart
     */
    showChartLoadingState(chartId) {
        const container = document.getElementById(`${chartId}-container`);
        if (!container) return;
        
        // Remove error state
        this.removeChartErrorState(chartId);
        
        // Show canvas
        const canvas = container.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'block';
        }
        
        // Update status
        this.updateChartStatus(chartId, 'Loading...', 'loading');
    }
    
    /**
     * Remove chart error state
     */
    removeChartErrorState(chartId) {
        const container = document.getElementById(`${chartId}-container`);
        if (!container) return;
        
        const errorState = container.querySelector('.chart-error-state');
        if (errorState) {
            errorState.remove();
        }
        
        // Show canvas
        const canvas = container.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'block';
        }
    }
    
    /**
     * Show final error when all retries fail
     */
    showFinalChartError(chartId, chartType, error) {
        const container = document.getElementById(`${chartId}-container`);
        if (!container) return;
        
        const errorElement = document.createElement('div');
        errorElement.className = 'chart-final-error';
        errorElement.innerHTML = `
            <div class="final-error-content">
                <div class="error-icon">💥</div>
                <h4>Chart Unavailable</h4>
                <p>Unable to load ${chartType} chart after multiple attempts.</p>
                <div class="final-error-actions">
                    <button onclick="window.location.reload()" class="chart-error-button">
                        Refresh Page
                    </button>
                </div>
            </div>
        `;
        
        // Replace error state with final error
        const existingError = container.querySelector('.chart-error-state');
        if (existingError) {
            existingError.replaceWith(errorElement);
        } else {
            container.appendChild(errorElement);
        }
        
        this.updateChartStatus(chartId, 'Failed', 'failed');
    }
    
    /**
     * Update chart status indicator
     */
    updateChartStatus(chartId, message, type = 'info') {
        const statusElement = document.getElementById(`${chartId}-status`);
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `chart-status ${type}`;
        }
    }
    
    /**
     * Log chart error for debugging
     */
    logError(chartId, chartType, error, context) {
        const errorLog = {
            chartId,
            chartType,
            error: {
                name: error.name,
                message: error.message,
                stack: error.stack
            },
            context,
            timestamp: new Date().toISOString(),
            retryAttempt: this.retryAttempts[chartId] || 0
        };
        
        this.errorLog.push(errorLog);
        
        // Keep only last 50 errors
        if (this.errorLog.length > 50) {
            this.errorLog = this.errorLog.slice(-50);
        }
        
        // Send to server for logging
        this.sendErrorToServer(errorLog);
    }
    
    /**
     * Send error to server for logging
     */
    async sendErrorToServer(errorLog) {
        try {
            await fetch('/api/log-chart-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(errorLog)
            });
        } catch (e) {
            console.warn('Could not send chart error log to server:', e);
        }
    }
    
    /**
     * Utility function for delays
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Get chart error statistics
     */
    getErrorStats() {
        const stats = {
            totalErrors: this.errorLog.length,
            errorsByChart: {},
            errorsByType: {},
            recentErrors: this.errorLog.slice(-10)
        };
        
        this.errorLog.forEach(log => {
            stats.errorsByChart[log.chartId] = (stats.errorsByChart[log.chartId] || 0) + 1;
            const errorType = this.categorizeChartError(log.error);
            stats.errorsByType[errorType] = (stats.errorsByType[errorType] || 0) + 1;
        });
        
        return stats;
    }
    
    /**
     * Reset error handler state
     */
    reset() {
        this.retryAttempts = {};
        this.errorLog = [];
    }
}

// Initialize error handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize streaming error handler
    window.streamingErrorHandler = new StreamingErrorHandler();
    
    // Initialize chart error handler (will be connected to chart manager when available)
    window.chartErrorHandler = new ChartErrorHandler();
    
    // Connect chart error handler to chart manager when it becomes available
    const connectChartErrorHandler = () => {
        if (window.globalChartManager) {
            window.chartErrorHandler.chartManager = window.globalChartManager;
            console.log('Chart error handler connected to chart manager');
        } else {
            // Try again in 1 second
            setTimeout(connectChartErrorHandler, 1000);
        }
    };
    
    connectChartErrorHandler();
    
    console.log('Error handling system initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StreamingErrorHandler, ChartErrorHandler };
}