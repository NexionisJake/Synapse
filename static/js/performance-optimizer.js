/**
 * Performance Optimizer - Final optimization and memory leak prevention
 * Handles frame throttling, memory management, and performance monitoring
 */

class PerformanceOptimizer {
    constructor() {
        this.frameThrottler = new FrameThrottler();
        this.memoryManager = new MemoryManager();
        this.renderQueue = new RenderQueue();
        this.performanceMonitor = new PerformanceMonitor();
        this.registeredCharts = new Map(); // Track registered charts
        
        // Performance thresholds
        this.thresholds = {
            maxMemoryUsage: 100 * 1024 * 1024, // 100MB
            maxRenderTime: 16, // 16ms for 60fps
            maxConversationLength: 100,
            maxChartInstances: 10,
            gcInterval: 300000 // 5 minutes
        };
        
        this.init();
    }
    
    init() {
        this.startPerformanceMonitoring();
        this.setupMemoryCleanup();
        this.optimizeEventListeners();
        
        // Expose to global scope for debugging
        window.performanceOptimizer = this;
    }
    
    /**
     * Optimize streaming text rendering with frame throttling
     */
    optimizeStreamingRender(textElement, content) {
        this.frameThrottler.throttle(() => {
            if (textElement && textElement.isConnected) {
                textElement.textContent = content;
            }
        });
    }
    
    /**
     * Optimize DOM updates with batching
     */
    optimizeDOMUpdate(callback) {
        this.renderQueue.add(callback);
    }
    
    /**
     * Optimize chart updates to prevent excessive redraws
     */
    optimizeChartUpdates(chart, newData, options = {}) {
        if (!chart || !chart.data) return;
        
        this.renderQueue.add(() => {
            try {
                chart.data = newData;
                chart.update(options.animation || 'none');
            } catch (error) {
                console.warn('Chart update failed:', error);
            }
        });
    }
    
    /**
     * Manage memory usage and prevent leaks
     */
    manageMemoryUsage() {
        this.memoryManager.cleanup();
        
        // Clean up conversation history
        if (window.conversationHistory && window.conversationHistory.length > this.thresholds.maxConversationLength) {
            const keepCount = Math.floor(this.thresholds.maxConversationLength * 0.7);
            window.conversationHistory = window.conversationHistory.slice(-keepCount);
            console.log(`Conversation history trimmed to ${keepCount} messages`);
        }
        
        // Clean up chart instances
        if (window.globalChartManager && typeof window.globalChartManager.cleanupAllCharts === 'function') {
            window.globalChartManager.cleanupAllCharts();
        }
        
        // Clean up old registered charts
        if (this.registeredCharts.size > this.thresholds.maxChartInstances) {
            this.cleanupOldestCharts();
        }
        
        // Force garbage collection if available
        if (window.gc && typeof window.gc === 'function') {
            window.gc();
        }
    }
    
    /**
     * Start performance monitoring
     */
    startPerformanceMonitoring() {
        this.performanceMonitor.start();
        
        // Monitor memory usage
        setInterval(() => {
            if (performance.memory) {
                const memoryUsage = performance.memory.usedJSHeapSize;
                if (memoryUsage > this.thresholds.maxMemoryUsage) {
                    console.warn(`High memory usage detected: ${Math.round(memoryUsage / 1024 / 1024)}MB`);
                    this.manageMemoryUsage();
                }
            }
        }, 30000); // Check every 30 seconds
    }
    
    /**
     * Setup automatic memory cleanup
     */
    setupMemoryCleanup() {
        setInterval(() => {
            this.manageMemoryUsage();
        }, this.thresholds.gcInterval);
        
        // Cleanup on page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.manageMemoryUsage();
            }
        });
        
        // Cleanup before page unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    /**
     * Optimize event listeners to prevent memory leaks
     */
    optimizeEventListeners() {
        // Use passive listeners where possible
        const passiveEvents = ['scroll', 'wheel', 'touchstart', 'touchmove'];
        
        passiveEvents.forEach(eventType => {
            const originalAddEventListener = EventTarget.prototype.addEventListener;
            EventTarget.prototype.addEventListener = function(type, listener, options) {
                if (passiveEvents.includes(type) && typeof options !== 'object') {
                    options = { passive: true };
                } else if (typeof options === 'object' && !options.hasOwnProperty('passive')) {
                    options.passive = true;
                }
                return originalAddEventListener.call(this, type, listener, options);
            };
        });
    }
    
    /**
     * Register a chart for performance monitoring and optimization
     */
    registerChart(chartId, chart) {
        if (!chartId || !chart) {
            console.warn('Invalid chart registration:', chartId, chart);
            return;
        }
        
        this.registeredCharts.set(chartId, {
            chart: chart,
            registeredAt: Date.now(),
            updateCount: 0,
            lastUpdate: Date.now()
        });
        
        console.log(`Chart registered: ${chartId}`);
        
        // Limit number of registered charts
        if (this.registeredCharts.size > this.thresholds.maxChartInstances) {
            this.cleanupOldestCharts();
        }
    }
    
    /**
     * Unregister a chart from performance monitoring
     */
    unregisterChart(chartId) {
        if (this.registeredCharts.has(chartId)) {
            const chartInfo = this.registeredCharts.get(chartId);
            
            // Destroy chart if it has a destroy method
            if (chartInfo.chart && typeof chartInfo.chart.destroy === 'function') {
                try {
                    chartInfo.chart.destroy();
                } catch (error) {
                    console.warn(`Error destroying chart ${chartId}:`, error);
                }
            }
            
            this.registeredCharts.delete(chartId);
            console.log(`Chart unregistered: ${chartId}`);
        }
    }
    
    /**
     * Clean up oldest registered charts when limit is exceeded
     */
    cleanupOldestCharts() {
        const charts = Array.from(this.registeredCharts.entries());
        charts.sort((a, b) => a[1].registeredAt - b[1].registeredAt);
        
        const toRemove = charts.slice(0, charts.length - this.thresholds.maxChartInstances + 1);
        toRemove.forEach(([chartId]) => {
            this.unregisterChart(chartId);
        });
    }
    
    /**
     * Get information about registered charts
     */
    getRegisteredCharts() {
        const charts = {};
        this.registeredCharts.forEach((info, chartId) => {
            charts[chartId] = {
                registeredAt: info.registeredAt,
                updateCount: info.updateCount,
                lastUpdate: info.lastUpdate,
                age: Date.now() - info.registeredAt
            };
        });
        return charts;
    }
    
    /**
     * Get current performance metrics
     */
    getPerformanceMetrics() {
        return {
            ...this.performanceMonitor.getMetrics(),
            registeredCharts: this.getRegisteredCharts()
        };
    }
    
    /**
     * Cleanup all resources
     */
    cleanup() {
        // Unregister all charts
        const chartIds = Array.from(this.registeredCharts.keys());
        chartIds.forEach(chartId => this.unregisterChart(chartId));
        
        this.frameThrottler.cleanup();
        this.memoryManager.cleanup();
        this.renderQueue.cleanup();
        this.performanceMonitor.stop();
    }
}

/**
 * Frame Throttler - Ensures smooth animations at 60fps
 */
class FrameThrottler {
    constructor() {
        this.pending = false;
        this.callbacks = [];
        this.lastFrame = 0;
        this.targetFPS = 60;
        this.frameInterval = 1000 / this.targetFPS;
    }
    
    throttle(callback) {
        this.callbacks.push(callback);
        
        if (!this.pending) {
            this.pending = true;
            this.scheduleFrame();
        }
    }
    
    scheduleFrame() {
        const now = performance.now();
        const elapsed = now - this.lastFrame;
        
        if (elapsed >= this.frameInterval) {
            this.executeCallbacks();
        } else {
            const delay = this.frameInterval - elapsed;
            setTimeout(() => {
                requestAnimationFrame(() => this.executeCallbacks());
            }, delay);
        }
    }
    
    executeCallbacks() {
        const callbacks = [...this.callbacks];
        this.callbacks = [];
        this.pending = false;
        this.lastFrame = performance.now();
        
        callbacks.forEach(callback => {
            try {
                callback();
            } catch (error) {
                console.warn('Frame callback error:', error);
            }
        });
    }
    
    cleanup() {
        this.callbacks = [];
        this.pending = false;
    }
}

/**
 * Memory Manager - Prevents memory leaks and manages resources
 */
class MemoryManager {
    constructor() {
        this.trackedObjects = new WeakSet();
        this.eventListeners = new Map();
        this.timers = new Set();
        this.observers = new Set();
    }
    
    /**
     * Track object for cleanup
     */
    track(object) {
        this.trackedObjects.add(object);
    }
    
    /**
     * Track event listener for cleanup
     */
    trackEventListener(element, event, listener, options) {
        const key = `${element.constructor.name}_${event}`;
        if (!this.eventListeners.has(key)) {
            this.eventListeners.set(key, []);
        }
        this.eventListeners.get(key).push({ element, event, listener, options });
    }
    
    /**
     * Track timer for cleanup
     */
    trackTimer(timerId) {
        this.timers.add(timerId);
    }
    
    /**
     * Track observer for cleanup
     */
    trackObserver(observer) {
        this.observers.add(observer);
    }
    
    /**
     * Cleanup all tracked resources
     */
    cleanup() {
        // Clear timers
        this.timers.forEach(timerId => {
            clearTimeout(timerId);
            clearInterval(timerId);
        });
        this.timers.clear();
        
        // Disconnect observers
        this.observers.forEach(observer => {
            if (observer.disconnect) {
                observer.disconnect();
            }
        });
        this.observers.clear();
        
        // Remove event listeners
        this.eventListeners.forEach(listeners => {
            listeners.forEach(({ element, event, listener, options }) => {
                if (element && element.removeEventListener) {
                    element.removeEventListener(event, listener, options);
                }
            });
        });
        this.eventListeners.clear();
        
        console.log('Memory cleanup completed');
    }
}

/**
 * Render Queue - Batches DOM updates for better performance
 */
class RenderQueue {
    constructor() {
        this.queue = [];
        this.isProcessing = false;
        this.maxBatchSize = 50;
    }
    
    add(callback) {
        this.queue.push(callback);
        
        if (!this.isProcessing) {
            this.process();
        }
    }
    
    process() {
        if (this.queue.length === 0) {
            this.isProcessing = false;
            return;
        }
        
        this.isProcessing = true;
        
        requestAnimationFrame(() => {
            const batch = this.queue.splice(0, this.maxBatchSize);
            
            batch.forEach(callback => {
                try {
                    callback();
                } catch (error) {
                    console.warn('Render queue callback error:', error);
                }
            });
            
            // Continue processing if there are more items
            if (this.queue.length > 0) {
                this.process();
            } else {
                this.isProcessing = false;
            }
        });
    }
    
    cleanup() {
        this.queue = [];
        this.isProcessing = false;
    }
}

/**
 * Performance Monitor - Tracks performance metrics
 */
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            frameRate: 0,
            renderTime: 0,
            memoryUsage: 0,
            networkLatency: 0,
            errorCount: 0,
            startTime: Date.now()
        };
        
        this.frameCount = 0;
        this.lastFrameTime = 0;
        this.isMonitoring = false;
    }
    
    start() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.startFrameRateMonitoring();
        this.startMemoryMonitoring();
        this.startErrorMonitoring();
    }
    
    stop() {
        this.isMonitoring = false;
    }
    
    startFrameRateMonitoring() {
        const measureFrameRate = (timestamp) => {
            if (!this.isMonitoring) return;
            
            if (this.lastFrameTime) {
                const delta = timestamp - this.lastFrameTime;
                this.metrics.frameRate = Math.round(1000 / delta);
                this.metrics.renderTime = delta;
            }
            
            this.lastFrameTime = timestamp;
            this.frameCount++;
            
            requestAnimationFrame(measureFrameRate);
        };
        
        requestAnimationFrame(measureFrameRate);
    }
    
    startMemoryMonitoring() {
        if (!performance.memory) return;
        
        setInterval(() => {
            if (!this.isMonitoring) return;
            
            this.metrics.memoryUsage = {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            };
        }, 5000);
    }
    
    startErrorMonitoring() {
        window.addEventListener('error', () => {
            this.metrics.errorCount++;
        });
        
        window.addEventListener('unhandledrejection', () => {
            this.metrics.errorCount++;
        });
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            uptime: Date.now() - this.metrics.startTime,
            frameCount: this.frameCount
        };
    }
}

// Initialize performance optimizer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PerformanceOptimizer();
});