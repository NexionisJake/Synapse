/**
 * Streaming Performance Monitoring and Optimization System
 * 
 * Implements comprehensive performance tracking, user feedback, and automatic optimization
 * for streaming responses in the Synapse AI web application.
 */

class StreamingPerformanceMonitor {
    constructor() {
        this.metrics = {
            responseTime: [],
            wordsPerSecond: [],
            chunkLatency: [],
            connectionFailures: 0,
            timeouts: 0,
            totalRequests: 0,
            successfulRequests: 0
        };
        
        // Initialize thresholds first
        this.thresholds = {
            slowResponseTime: 5000, // 5 seconds
            verySlowResponseTime: 10000, // 10 seconds
            minWordsPerSecond: 10,
            maxChunkLatency: 2000, // 2 seconds
            timeoutThreshold: 60000, // Start with 60 seconds for low-end systems
            maxTimeoutThreshold: 180000, // Maximum 3 minutes for very slow systems
            minTimeoutThreshold: 30000, // Minimum 30 seconds
            connectionFailureRate: 0.1, // 10%
            adaptiveTimeoutEnabled: true
        };
        
        // Detect system performance after thresholds are initialized
        this.systemPerformance = this.detectSystemPerformance();
        
        this.config = {
            enableNotifications: true,
            enableOptimizations: true,
            enableMetricsLogging: true,
            performanceCheckInterval: 5000, // 5 seconds
            metricsRetentionCount: 100 // Keep last 100 measurements
        };
        
        this.isMonitoring = false;
        this.performanceCheckTimer = null;
        this.currentStreamingSessions = new Map();
        
        this.init();
    }
    
    /**
     * Initialize the performance monitoring system
     */
    init() {
        console.log('Initializing Streaming Performance Monitor...');
        
        // Set up event listeners for streaming events
        this.setupEventListeners();
        
        // Start performance monitoring
        this.startPerformanceMonitoring();
        
        // Expose to global scope for debugging
        window.streamingPerformanceMonitor = this;
        
        // Show system performance indicator
        this.showSystemPerformanceIndicator();
        
        console.log('Streaming Performance Monitor initialized');
        console.log('Detected system performance level:', this.systemPerformance?.level || 'unknown');
        console.log('System specs:', {
            cores: this.systemPerformance?.cpuCores,
            memory: this.systemPerformance?.memoryGB,
            timeout: this.thresholds?.timeoutThreshold
        });
    }
    
    /**
     * Detect system performance characteristics
     */
    detectSystemPerformance() {
        try {
            const performance = {
                level: 'medium', // low, medium, high
                cpuCores: navigator.hardwareConcurrency || 4,
                memoryGB: navigator.deviceMemory || 4,
                connectionType: 'unknown',
                adjustedTimeouts: {}
            };
            
            // Detect connection type if available
            if (navigator.connection) {
                performance.connectionType = navigator.connection.effectiveType || 'unknown';
            }
        
        // Classify system performance
        if (performance.cpuCores <= 2 || performance.memoryGB <= 2) {
            performance.level = 'low';
        } else if (performance.cpuCores >= 8 && performance.memoryGB >= 8) {
            performance.level = 'high';
        }
        
        // Adjust timeouts based on system performance
        switch (performance.level) {
            case 'low':
                performance.adjustedTimeouts = {
                    timeoutThreshold: 180000, // 3 minutes
                    slowResponseTime: 15000, // 15 seconds
                    verySlowResponseTime: 30000, // 30 seconds
                    minWordsPerSecond: 3,
                    maxChunkLatency: 5000
                };
                break;
            case 'high':
                performance.adjustedTimeouts = {
                    timeoutThreshold: 45000, // 45 seconds
                    slowResponseTime: 3000, // 3 seconds
                    verySlowResponseTime: 8000, // 8 seconds
                    minWordsPerSecond: 15,
                    maxChunkLatency: 1500
                };
                break;
            default: // medium
                performance.adjustedTimeouts = {
                    timeoutThreshold: 180000, // 3 minutes
                    slowResponseTime: 5000, // 5 seconds
                    verySlowResponseTime: 12000, // 12 seconds
                    minWordsPerSecond: 8,
                    maxChunkLatency: 2500
                };
        }
        
            // Apply system-specific adjustments
            if (performance.adjustedTimeouts && this.thresholds) {
                Object.assign(this.thresholds, performance.adjustedTimeouts);
            }
            
            return performance;
        } catch (error) {
            console.warn('Error detecting system performance, using defaults:', error);
            return {
                level: 'medium',
                cpuCores: 4,
                memoryGB: 4,
                connectionType: 'unknown',
                adjustedTimeouts: {
                    timeoutThreshold: 90000, // 1.5 minutes default
                    slowResponseTime: 5000,
                    verySlowResponseTime: 12000,
                    minWordsPerSecond: 8,
                    maxChunkLatency: 2500
                }
            };
        }
    }
    
    /**
     * Set up event listeners for streaming performance tracking
     */
    setupEventListeners() {
        // Listen for streaming started events
        document.addEventListener('streamingStarted', (e) => {
            this.onStreamingStarted(e.detail);
        });
        
        // Listen for streaming completed events
        document.addEventListener('streamingCompleted', (e) => {
            this.onStreamingCompleted(e.detail);
        });
        
        // Listen for streaming error events
        document.addEventListener('streamingError', (e) => {
            this.onStreamingError(e.detail);
        });
        
        // Listen for chunk received events
        document.addEventListener('streamingChunk', (e) => {
            this.onStreamingChunk(e.detail);
        });
    }
    
    /**
     * Start performance monitoring loop
     */
    startPerformanceMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.performanceCheckTimer = setInterval(() => {
            this.checkPerformanceThresholds();
        }, this.config.performanceCheckInterval);
        
        console.log('Performance monitoring started');
    }
    
    /**
     * Stop performance monitoring
     */
    stopPerformanceMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        if (this.performanceCheckTimer) {
            clearInterval(this.performanceCheckTimer);
            this.performanceCheckTimer = null;
        }
        
        console.log('Performance monitoring stopped');
    }
    
    /**
     * Handle streaming session started
     */
    onStreamingStarted(detail) {
        const { requestId, startTime, container } = detail;
        
        this.currentStreamingSessions.set(requestId, {
            startTime,
            container,
            chunkCount: 0,
            totalCharacters: 0,
            lastChunkTime: startTime,
            timeoutTimer: this.createTimeoutTimer(requestId),
            progressTimer: this.createProgressTimer(requestId)
        });
        
        this.metrics.totalRequests++;
        
        if (this.config.enableMetricsLogging) {
            console.log(`Streaming session started: ${requestId}`);
        }
    }
    
    /**
     * Create progress timer to show helpful messages during long processing
     */
    createProgressTimer(requestId) {
        const session = this.currentStreamingSessions.get(requestId);
        if (!session) return null;
        
        const progressIntervals = [];
        
        // Show progress messages at different intervals based on system performance
        const intervals = this.systemPerformance.level === 'low' ? 
            [15000, 30000, 60000, 120000] : // Low-end: 15s, 30s, 1m, 2m
            [10000, 20000, 40000, 80000];   // Medium/High-end: 10s, 20s, 40s, 80s
        
        intervals.forEach((delay, index) => {
            const timer = setTimeout(() => {
                const currentSession = this.currentStreamingSessions.get(requestId);
                if (currentSession && currentSession.chunkCount === 0) {
                    this.showProgressMessage(requestId, index + 1, delay);
                }
            }, delay);
            
            progressIntervals.push(timer);
        });
        
        return progressIntervals;
    }
    
    /**
     * Show progress message during long processing
     */
    showProgressMessage(requestId, stage, elapsed) {
        const session = this.currentStreamingSessions.get(requestId);
        if (!session) return;
        
        const isSlowSystem = this.systemPerformance.level === 'low';
        const messages = isSlowSystem ? [
            'AI is processing your request... Complex responses may take longer on your system.',
            'Still processing... Your system may need extra time for AI computations.',
            'Processing continues... Please be patient, AI responses can take up to 3 minutes on slower systems.',
            'Almost there... Complex AI processing is still in progress.'
        ] : [
            'AI is thinking about your request...',
            'Processing a complex response...',
            'Still working on your response...',
            'Finalizing the response...'
        ];
        
        const message = messages[Math.min(stage - 1, messages.length - 1)];
        
        // Update the loading indicator if it exists
        const container = session.container;
        const loadingElement = container.querySelector('.streaming-indicator, .loading-indicator');
        if (loadingElement) {
            const textElement = loadingElement.querySelector('.streaming-text, .loading-text');
            if (textElement) {
                textElement.textContent = message;
            }
        }
        
        // Also show a subtle notification for very long waits
        if (stage >= 3 && isSlowSystem) {
            this.showPerformanceNotification({
                type: 'long_processing',
                title: 'Processing Complex Request',
                message: `Your AI request is still being processed. On slower systems, this can take up to ${Math.round(this.thresholds.maxTimeoutThreshold/60000)} minutes for complex responses.`,
                suggestions: [
                    'Please continue waiting - processing is still active',
                    'Consider shorter questions for faster responses in the future',
                    'Your system performance has been automatically detected and timeouts adjusted'
                ],
                severity: 'info',
                persistent: false
            });
        }
    }
    
    /**
     * Handle streaming chunk received
     */
    onStreamingChunk(detail) {
        const { requestId, chunkContent, timestamp } = detail;
        const session = this.currentStreamingSessions.get(requestId);
        
        if (!session) return;
        
        const now = Date.now();
        const chunkLatency = now - session.lastChunkTime;
        
        // Update session metrics
        session.chunkCount++;
        session.totalCharacters += chunkContent ? chunkContent.length : 0;
        session.lastChunkTime = now;
        
        // Record chunk latency
        this.recordMetric('chunkLatency', chunkLatency);
        
        // Check for slow chunks
        if (chunkLatency > this.thresholds.maxChunkLatency) {
            this.handleSlowChunk(requestId, chunkLatency);
        }
    }
    
    /**
     * Handle streaming session completed
     */
    onStreamingCompleted(detail) {
        const { requestId, responseTime, streamingStats } = detail;
        const session = this.currentStreamingSessions.get(requestId);
        
        if (!session) return;
        
        // Clear timeout and progress timers
        if (session.timeoutTimer) {
            clearTimeout(session.timeoutTimer);
        }
        if (session.progressTimer && Array.isArray(session.progressTimer)) {
            session.progressTimer.forEach(timer => clearTimeout(timer));
        }
        
        // Calculate performance metrics
        const wordsPerSecond = streamingStats?.wordsPerSecond || 
            (session.totalCharacters / 5) / (responseTime / 1000);
        
        // Record metrics
        this.recordMetric('responseTime', responseTime);
        this.recordMetric('wordsPerSecond', wordsPerSecond);
        this.metrics.successfulRequests++;
        
        // Check performance thresholds
        this.checkResponsePerformance(requestId, responseTime, wordsPerSecond);
        
        // Clean up session
        this.currentStreamingSessions.delete(requestId);
        
        if (this.config.enableMetricsLogging) {
            console.log(`Streaming completed: ${requestId}, ${responseTime}ms, ${wordsPerSecond.toFixed(1)} WPS`);
        }
    }
    
    /**
     * Handle streaming error
     */
    onStreamingError(detail) {
        const { requestId, error, errorType } = detail;
        const session = this.currentStreamingSessions.get(requestId);
        
        if (session) {
            if (session.timeoutTimer) {
                clearTimeout(session.timeoutTimer);
            }
            if (session.progressTimer && Array.isArray(session.progressTimer)) {
                session.progressTimer.forEach(timer => clearTimeout(timer));
            }
        }
        
        // Record error metrics
        if (errorType === 'timeout') {
            this.metrics.timeouts++;
        } else if (errorType === 'connection') {
            this.metrics.connectionFailures++;
        }
        
        // Clean up session
        this.currentStreamingSessions.delete(requestId);
        
        // Check if error rate is too high
        this.checkErrorRates();
        
        if (this.config.enableMetricsLogging) {
            console.log(`Streaming error: ${requestId}, type: ${errorType}`);
        }
    }
    
    /**
     * Create timeout timer for streaming session with adaptive timeout
     */
    createTimeoutTimer(requestId) {
        const adaptiveTimeout = this.calculateAdaptiveTimeout();
        
        return setTimeout(() => {
            const session = this.currentStreamingSessions.get(requestId);
            if (session) {
                // Dispatch timeout event
                document.dispatchEvent(new CustomEvent('streamingError', {
                    detail: {
                        requestId,
                        container: session.container,
                        error: new Error('Streaming timeout'),
                        errorType: 'timeout'
                    }
                }));
                
                this.handleStreamingTimeout(requestId);
            }
        }, adaptiveTimeout);
    }
    
    /**
     * Calculate adaptive timeout based on system performance and history
     */
    calculateAdaptiveTimeout() {
        if (!this.thresholds.adaptiveTimeoutEnabled) {
            return this.thresholds.timeoutThreshold;
        }
        
        // Base timeout
        let adaptiveTimeout = this.thresholds.timeoutThreshold;
        
        // Adjust based on recent response times
        const recentResponses = this.metrics.responseTime.slice(-5); // Last 5 responses
        if (recentResponses.length > 0) {
            const avgResponseTime = recentResponses.reduce((a, b) => a + b, 0) / recentResponses.length;
            
            // If average response time is slow, increase timeout proportionally
            if (avgResponseTime > this.thresholds.slowResponseTime) {
                const multiplier = Math.min(3, avgResponseTime / this.thresholds.slowResponseTime);
                adaptiveTimeout = Math.min(
                    this.thresholds.maxTimeoutThreshold,
                    this.thresholds.timeoutThreshold * multiplier
                );
            }
        }
        
        // Adjust based on recent timeout rate
        const recentTimeouts = this.metrics.timeouts;
        const recentRequests = this.metrics.totalRequests;
        if (recentRequests > 0) {
            const timeoutRate = recentTimeouts / recentRequests;
            if (timeoutRate > 0.2) { // If more than 20% timeout rate
                adaptiveTimeout = Math.min(
                    this.thresholds.maxTimeoutThreshold,
                    adaptiveTimeout * 1.5
                );
            }
        }
        
        // Ensure timeout is within bounds
        adaptiveTimeout = Math.max(this.thresholds.minTimeoutThreshold, adaptiveTimeout);
        adaptiveTimeout = Math.min(this.thresholds.maxTimeoutThreshold, adaptiveTimeout);
        
        if (this.config.enableMetricsLogging && adaptiveTimeout !== this.thresholds.timeoutThreshold) {
            console.log(`Adaptive timeout calculated: ${adaptiveTimeout}ms (base: ${this.thresholds.timeoutThreshold}ms)`);
        }
        
        return adaptiveTimeout;
    }
    
    /**
     * Handle streaming timeout with adaptive messaging
     */
    handleStreamingTimeout(requestId) {
        const currentTimeout = this.calculateAdaptiveTimeout();
        const isSlowSystem = currentTimeout > this.thresholds.timeoutThreshold * 1.5;
        
        if (this.config.enableNotifications) {
            this.showPerformanceNotification({
                type: 'timeout',
                title: isSlowSystem ? 'Processing Taking Longer' : 'Streaming Timeout',
                message: isSlowSystem ? 
                    `The AI is still processing your request. On slower systems, complex responses may take up to ${Math.round(currentTimeout/1000)} seconds. Please wait a bit longer.` :
                    'The AI response is taking longer than expected. This might indicate a complex query or server load.',
                suggestions: isSlowSystem ? [
                    'Please be patient - your system may need more time for complex AI processing',
                    'Consider using shorter, simpler questions for faster responses',
                    'Try standard (non-streaming) mode if timeouts persist'
                ] : [
                    'Try breaking down complex questions into smaller parts',
                    'Check your internet connection',
                    'Consider using standard (non-streaming) mode for complex queries'
                ],
                severity: isSlowSystem ? 'info' : 'warning',
                persistent: isSlowSystem
            });
        }
        
        // Automatically increase timeout for next request if this was a slow system timeout
        if (isSlowSystem) {
            this.thresholds.timeoutThreshold = Math.min(
                this.thresholds.maxTimeoutThreshold,
                this.thresholds.timeoutThreshold * 1.2
            );
            console.log(`Increased base timeout to ${this.thresholds.timeoutThreshold}ms for slow system`);
        }
    }
    
    /**
     * Handle slow chunk delivery
     */
    handleSlowChunk(requestId, chunkLatency) {
        if (this.config.enableNotifications) {
            this.showPerformanceNotification({
                type: 'slow_chunk',
                title: 'Slow Response',
                message: `Response chunks are arriving slowly (${chunkLatency}ms delay). This may affect the streaming experience.`,
                suggestions: [
                    'Check your network connection',
                    'Close other bandwidth-intensive applications',
                    'Consider switching to standard mode if issues persist'
                ],
                severity: 'info'
            });
        }
    }
    
    /**
     * Check response performance against thresholds
     */
    checkResponsePerformance(requestId, responseTime, wordsPerSecond) {
        let performanceIssues = [];
        
        // Check response time
        if (responseTime > this.thresholds.verySlowResponseTime) {
            performanceIssues.push({
                type: 'very_slow_response',
                metric: 'response_time',
                value: responseTime,
                threshold: this.thresholds.verySlowResponseTime,
                severity: 'warning'
            });
        } else if (responseTime > this.thresholds.slowResponseTime) {
            performanceIssues.push({
                type: 'slow_response',
                metric: 'response_time',
                value: responseTime,
                threshold: this.thresholds.slowResponseTime,
                severity: 'info'
            });
        }
        
        // Check words per second
        if (wordsPerSecond < this.thresholds.minWordsPerSecond) {
            performanceIssues.push({
                type: 'slow_generation',
                metric: 'words_per_second',
                value: wordsPerSecond,
                threshold: this.thresholds.minWordsPerSecond,
                severity: 'info'
            });
        }
        
        // Show notifications for performance issues
        if (performanceIssues.length > 0 && this.config.enableNotifications) {
            this.showPerformanceIssueNotification(performanceIssues);
        }
        
        // Apply automatic optimizations
        if (this.config.enableOptimizations) {
            this.applyPerformanceOptimizations(performanceIssues);
        }
    }
    
    /**
     * Check error rates and show notifications if needed
     */
    checkErrorRates() {
        if (this.metrics.totalRequests === 0) return;
        
        const failureRate = (this.metrics.connectionFailures + this.metrics.timeouts) / this.metrics.totalRequests;
        
        if (failureRate > this.thresholds.connectionFailureRate) {
            if (this.config.enableNotifications) {
                this.showPerformanceNotification({
                    type: 'high_error_rate',
                    title: 'Connection Issues Detected',
                    message: `High failure rate detected (${(failureRate * 100).toFixed(1)}%). This may indicate network or server issues.`,
                    suggestions: [
                        'Check your internet connection',
                        'Try refreshing the page',
                        'Consider using standard mode temporarily',
                        'Contact support if issues persist'
                    ],
                    severity: 'warning'
                });
            }
        }
    }
    
    /**
     * Check overall performance thresholds
     */
    checkPerformanceThresholds() {
        if (this.metrics.responseTime.length === 0) return;
        
        // Calculate recent averages
        const recentResponses = this.metrics.responseTime.slice(-10); // Last 10 responses
        const avgResponseTime = recentResponses.reduce((a, b) => a + b, 0) / recentResponses.length;
        
        const recentWPS = this.metrics.wordsPerSecond.slice(-10);
        const avgWordsPerSecond = recentWPS.length > 0 ? 
            recentWPS.reduce((a, b) => a + b, 0) / recentWPS.length : 0;
        
        // Check if performance is consistently poor
        if (avgResponseTime > this.thresholds.slowResponseTime && recentResponses.length >= 3) {
            this.handleConsistentlySlowPerformance(avgResponseTime, avgWordsPerSecond);
        }
    }
    
    /**
     * Handle consistently slow performance
     */
    handleConsistentlySlowPerformance(avgResponseTime, avgWordsPerSecond) {
        if (this.config.enableNotifications) {
            this.showPerformanceNotification({
                type: 'consistently_slow',
                title: 'Performance Degradation Detected',
                message: `Recent responses have been consistently slow (avg: ${(avgResponseTime/1000).toFixed(1)}s, ${avgWordsPerSecond.toFixed(1)} WPS).`,
                suggestions: [
                    'Consider switching to standard (non-streaming) mode',
                    'Check system resources and close unnecessary applications',
                    'Verify network connection stability',
                    'Try shorter, more focused questions'
                ],
                severity: 'warning',
                persistent: true
            });
        }
        
        // Apply automatic optimizations
        if (this.config.enableOptimizations) {
            this.applyPerformanceOptimizations([{
                type: 'consistently_slow',
                severity: 'warning'
            }]);
        }
    }
    
    /**
     * Show performance issue notification
     */
    showPerformanceIssueNotification(issues) {
        const primaryIssue = issues.find(i => i.severity === 'warning') || issues[0];
        
        let message = '';
        let suggestions = [];
        
        switch (primaryIssue.type) {
            case 'very_slow_response':
                message = `Very slow response detected (${(primaryIssue.value/1000).toFixed(1)}s). This significantly exceeds normal response times.`;
                suggestions = [
                    'Consider breaking complex questions into smaller parts',
                    'Switch to standard mode for better reliability',
                    'Check your network connection'
                ];
                break;
                
            case 'slow_response':
                message = `Slow response detected (${(primaryIssue.value/1000).toFixed(1)}s). Response time is higher than optimal.`;
                suggestions = [
                    'Try more focused questions',
                    'Check network connection',
                    'Consider standard mode for complex queries'
                ];
                break;
                
            case 'slow_generation':
                message = `Slow text generation detected (${primaryIssue.value.toFixed(1)} words/sec). AI processing may be under load.`;
                suggestions = [
                    'Try simpler questions',
                    'Wait for server load to decrease',
                    'Use standard mode for immediate responses'
                ];
                break;
        }
        
        this.showPerformanceNotification({
            type: primaryIssue.type,
            title: 'Performance Issue Detected',
            message,
            suggestions,
            severity: primaryIssue.severity
        });
    }
    
    /**
     * Show performance notification to user
     */
    showPerformanceNotification(notification) {
        // Create notification element
        const notificationElement = document.createElement('div');
        notificationElement.className = `performance-notification ${notification.severity}`;
        notificationElement.innerHTML = `
            <div class="notification-header">
                <div class="notification-icon">
                    ${notification.severity === 'warning' ? '⚠️' : 'ℹ️'}
                </div>
                <div class="notification-title">${notification.title}</div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="notification-body">
                <p class="notification-message">${notification.message}</p>
                ${notification.suggestions && notification.suggestions.length > 0 ? `
                    <div class="notification-suggestions">
                        <strong>Suggestions:</strong>
                        <ul>
                            ${notification.suggestions.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Add to notification container or create one
        let container = document.getElementById('performance-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'performance-notifications';
            container.className = 'performance-notifications-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notificationElement);
        
        // Auto-remove notification after delay (unless persistent)
        if (!notification.persistent) {
            setTimeout(() => {
                if (notificationElement.parentNode) {
                    notificationElement.remove();
                }
            }, notification.severity === 'warning' ? 10000 : 5000);
        }
    }
    
    /**
     * Apply automatic performance optimizations
     */
    applyPerformanceOptimizations(issues) {
        console.log('Applying performance optimizations for issues:', issues);
        
        // Suggest switching to standard mode for severe issues
        const severeIssues = issues.filter(i => i.severity === 'warning');
        if (severeIssues.length > 0) {
            this.suggestStandardMode();
        }
        
        // Optimize streaming parameters
        this.optimizeStreamingParameters();
        
        // Clear old metrics to free memory
        this.cleanupMetrics();
    }
    
    /**
     * Suggest switching to standard mode
     */
    suggestStandardMode() {
        // Dispatch event for UI to handle
        document.dispatchEvent(new CustomEvent('performanceOptimizationSuggestion', {
            detail: {
                type: 'switch_to_standard_mode',
                message: 'Consider switching to standard (non-streaming) mode for better performance',
                action: 'switch_mode'
            }
        }));
    }
    
    /**
     * Optimize streaming parameters based on system performance
     */
    optimizeStreamingParameters() {
        const avgResponseTime = this.getAverageResponseTime();
        const avgChunkLatency = this.getAverageChunkLatency();
        
        // Adaptive timeout adjustment for slow systems
        if (avgResponseTime > this.thresholds.slowResponseTime) {
            const oldTimeout = this.thresholds.timeoutThreshold;
            
            // Calculate new timeout based on average response time with safety margin
            const suggestedTimeout = Math.min(
                this.thresholds.maxTimeoutThreshold,
                Math.max(
                    this.thresholds.minTimeoutThreshold,
                    avgResponseTime * 2.5 // 2.5x average response time as timeout
                )
            );
            
            this.thresholds.timeoutThreshold = suggestedTimeout;
            console.log(`Optimized timeout: ${oldTimeout}ms → ${suggestedTimeout}ms (avg response: ${avgResponseTime}ms)`);
        }
        
        // Adjust chunk latency threshold for slow systems
        if (avgChunkLatency > this.thresholds.maxChunkLatency) {
            const oldLatency = this.thresholds.maxChunkLatency;
            this.thresholds.maxChunkLatency = Math.min(8000, Math.max(2000, avgChunkLatency * 1.5));
            console.log(`Adjusted chunk latency threshold: ${oldLatency}ms → ${this.thresholds.maxChunkLatency}ms`);
        }
        
        // Adjust performance thresholds for slower systems
        if (avgResponseTime > this.thresholds.verySlowResponseTime) {
            // This is a consistently slow system, adjust all thresholds
            this.thresholds.slowResponseTime = Math.min(15000, avgResponseTime * 0.8);
            this.thresholds.verySlowResponseTime = Math.min(30000, avgResponseTime * 1.2);
            this.thresholds.minWordsPerSecond = Math.max(3, this.thresholds.minWordsPerSecond * 0.7);
            
            console.log(`Adjusted thresholds for slow system - slow: ${this.thresholds.slowResponseTime}ms, very slow: ${this.thresholds.verySlowResponseTime}ms, min WPS: ${this.thresholds.minWordsPerSecond}`);
        }
    }
    
    /**
     * Clean up old metrics to prevent memory bloat
     */
    cleanupMetrics() {
        const maxRetention = this.config.metricsRetentionCount;
        
        if (this.metrics.responseTime.length > maxRetention) {
            this.metrics.responseTime = this.metrics.responseTime.slice(-maxRetention);
        }
        
        if (this.metrics.wordsPerSecond.length > maxRetention) {
            this.metrics.wordsPerSecond = this.metrics.wordsPerSecond.slice(-maxRetention);
        }
        
        if (this.metrics.chunkLatency.length > maxRetention) {
            this.metrics.chunkLatency = this.metrics.chunkLatency.slice(-maxRetention);
        }
    }
    
    /**
     * Record a performance metric
     */
    recordMetric(metricName, value) {
        if (!this.metrics[metricName]) {
            this.metrics[metricName] = [];
        }
        
        this.metrics[metricName].push(value);
        
        // Limit array size to prevent memory bloat
        if (this.metrics[metricName].length > this.config.metricsRetentionCount) {
            this.metrics[metricName].shift();
        }
    }
    
    /**
     * Get average response time
     */
    getAverageResponseTime() {
        if (this.metrics.responseTime.length === 0) return 0;
        return this.metrics.responseTime.reduce((a, b) => a + b, 0) / this.metrics.responseTime.length;
    }
    
    /**
     * Get average words per second
     */
    getAverageWordsPerSecond() {
        if (this.metrics.wordsPerSecond.length === 0) return 0;
        return this.metrics.wordsPerSecond.reduce((a, b) => a + b, 0) / this.metrics.wordsPerSecond.length;
    }
    
    /**
     * Get average chunk latency
     */
    getAverageChunkLatency() {
        if (this.metrics.chunkLatency.length === 0) return 0;
        return this.metrics.chunkLatency.reduce((a, b) => a + b, 0) / this.metrics.chunkLatency.length;
    }
    
    /**
     * Get success rate
     */
    getSuccessRate() {
        if (this.metrics.totalRequests === 0) return 1;
        return this.metrics.successfulRequests / this.metrics.totalRequests;
    }
    
    /**
     * Get current timeout value (public method for external use)
     */
    getCurrentTimeout() {
        return this.calculateAdaptiveTimeout();
    }
    
    /**
     * Get comprehensive performance metrics
     */
    getPerformanceMetrics() {
        return {
            averageResponseTime: this.getAverageResponseTime(),
            averageWordsPerSecond: this.getAverageWordsPerSecond(),
            averageChunkLatency: this.getAverageChunkLatency(),
            successRate: this.getSuccessRate(),
            totalRequests: this.metrics.totalRequests,
            successfulRequests: this.metrics.successfulRequests,
            connectionFailures: this.metrics.connectionFailures,
            timeouts: this.metrics.timeouts,
            currentSessions: this.currentStreamingSessions.size,
            thresholds: { ...this.thresholds }
        };
    }
    
    /**
     * Reset performance metrics
     */
    resetMetrics() {
        this.metrics = {
            responseTime: [],
            wordsPerSecond: [],
            chunkLatency: [],
            connectionFailures: 0,
            timeouts: 0,
            totalRequests: 0,
            successfulRequests: 0
        };
        
        console.log('Performance metrics reset');
    }
    
    /**
     * Update configuration
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        console.log('Performance monitor configuration updated:', this.config);
    }
    
    /**
     * Update thresholds
     */
    updateThresholds(newThresholds) {
        this.thresholds = { ...this.thresholds, ...newThresholds };
        console.log('Performance thresholds updated:', this.thresholds);
    }
    
    /**
     * Clean up the performance monitor
     */
    cleanup() {
        this.stopPerformanceMonitoring();
        
        // Clear all active sessions
        for (const [requestId, session] of this.currentStreamingSessions.entries()) {
            if (session.timeoutTimer) {
                clearTimeout(session.timeoutTimer);
            }
        }
        this.currentStreamingSessions.clear();
        
        // Remove notification container
        const container = document.getElementById('performance-notifications');
        if (container) {
            container.remove();
        }
        
        console.log('Streaming Performance Monitor cleaned up');
    }
    
    /**
     * Show system performance indicator to user
     */
    showSystemPerformanceIndicator() {
        try {
            // Remove existing indicator
            const existing = document.getElementById('system-performance-indicator');
            if (existing) {
                existing.remove();
            }
            
            // Ensure we have valid system performance data
            if (!this.systemPerformance || !this.thresholds) {
                console.warn('System performance data not available, skipping indicator');
                return;
            }
            
            const indicator = document.createElement('div');
            indicator.id = 'system-performance-indicator';
            indicator.className = `system-performance-indicator ${this.systemPerformance.level || 'medium'}`;
            
            const levelText = {
                low: 'Slower System Detected',
                medium: 'Standard System',
                high: 'High Performance System'
            };
            
            const timeoutText = {
                low: `Timeouts adjusted to ${Math.round((this.thresholds.timeoutThreshold || 180000)/60000)}min`,
                medium: `Timeouts set to ${Math.round((this.thresholds.timeoutThreshold || 90000)/1000)}s`,
                high: `Timeouts set to ${Math.round((this.thresholds.timeoutThreshold || 45000)/1000)}s`
            };
            
            const level = this.systemPerformance.level || 'medium';
            
            indicator.innerHTML = `
                <div style="font-weight: 600;">${levelText[level] || levelText.medium}</div>
                <div style="font-size: 0.9em; opacity: 0.8;">${timeoutText[level] || timeoutText.medium}</div>
            `;
            
            indicator.title = `System: ${this.systemPerformance.cpuCores || 4} cores, ${this.systemPerformance.memoryGB || 4}GB RAM\nConnection: ${this.systemPerformance.connectionType || 'unknown'}\nTimeouts automatically adjusted for your system performance.`;
            
            document.body.appendChild(indicator);
            
            // Auto-hide after 10 seconds unless it's a low-end system
            if (level !== 'low') {
                setTimeout(() => {
                    if (indicator.parentNode) {
                        indicator.style.opacity = '0';
                        setTimeout(() => {
                            if (indicator.parentNode) {
                                indicator.remove();
                            }
                        }, 300);
                    }
                }, 10000);
            }
        } catch (error) {
            console.warn('Error showing system performance indicator:', error);
        }
    }
}

// Global instance
let globalStreamingPerformanceMonitor = null;

/**
 * Initialize global streaming performance monitor
 */
function initializeStreamingPerformanceMonitor() {
    if (!globalStreamingPerformanceMonitor) {
        globalStreamingPerformanceMonitor = new StreamingPerformanceMonitor();
        console.log('Global Streaming Performance Monitor initialized');
    }
    return globalStreamingPerformanceMonitor;
}

/**
 * Get global streaming performance monitor instance
 */
function getStreamingPerformanceMonitor() {
    if (!globalStreamingPerformanceMonitor) {
        return initializeStreamingPerformanceMonitor();
    }
    return globalStreamingPerformanceMonitor;
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeStreamingPerformanceMonitor();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        StreamingPerformanceMonitor,
        initializeStreamingPerformanceMonitor,
        getStreamingPerformanceMonitor
    };
}