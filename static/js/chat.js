// Chat interface JavaScript
document.addEventListener('DOMContentLoaded', function () {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatLog = document.getElementById('chat-log');

    // Conversation history array to maintain context
    let conversationHistory = [];

    // Track if we're currently processing a message
    let isProcessing = false;

    // Markdown rendering utilities
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
        },

        /**
         * Append content with markdown rendering (for streaming)
         * @param {HTMLElement} element - Target element
         * @param {string} content - New markdown content to append
         */
        appendContent(element, content) {
            const existingContent = element.getAttribute('data-raw-content') || '';
            const newContent = existingContent + content;
            element.setAttribute('data-raw-content', newContent);
            this.setContent(element, newContent);
        }
    };

    // Initialize markdown renderer
    MarkdownRenderer.configure();

    // Expose MarkdownRenderer globally for use by performance optimizer
    window.MarkdownRenderer = MarkdownRenderer;

    // Performance and optimization settings
    const PERFORMANCE_CONFIG = {
        MAX_CONVERSATION_LENGTH: 100,
        CLEANUP_THRESHOLD: 80, // Start cleanup at 80% of max
        MAX_MESSAGE_AGE_HOURS: 24,
        RESPONSE_TIMEOUT_MS: 120000, // 2 minutes for low-end systems
        TYPING_INDICATOR_DELAY: 500, // Show typing after 500ms
        AUTO_CLEANUP_INTERVAL: 300000 // 5 minutes
    };

    // Performance metrics
    let performanceMetrics = {
        responseTimeHistory: [],
        messageCount: 0,
        lastCleanup: Date.now(),
        averageResponseTime: 0
    };

    // Auto-cleanup timer
    let autoCleanupTimer = null;

    // Setup event listeners for loading feedback integration
    function setupLoadingFeedbackIntegration() {
        // Listen for retry streaming events
        document.addEventListener('retryStreaming', async (e) => {
            const { container, options } = e.detail;
            if (options && options.originalMessage) {
                // Retry the last message
                await retryLastMessage(container, options);
            }
        });

        // Listen for fallback to standard events
        document.addEventListener('fallbackToStandard', async (e) => {
            const { container, options } = e.detail;
            if (options && options.originalMessage) {
                // Use standard (non-streaming) mode
                await handleStandardResponse(container, options);
            }
        });

        // Listen for chart retry events
        document.addEventListener('retryChart', (e) => {
            const { chartId } = e.detail;
            if (window.globalChartManager) {
                window.globalChartManager.refreshCharts();
            }
        });
    }

    // Retry last message with streaming
    async function retryLastMessage(container, options) {
        try {
            isProcessing = true;
            updateUIState(true);

            // Clear container and show loading
            const contentElement = container.querySelector('.message-content');
            contentElement.innerHTML = '';

            if (window.loadingFeedbackManager) {
                window.loadingFeedbackManager.createStreamingIndicator(contentElement, 'Retrying...');
            }

            const requestStartTime = Date.now();
            const streamingHandler = new StreamingResponseHandler();
            await streamingHandler.handleStreamingResponse(container, requestStartTime);

        } catch (error) {
            console.error('Retry failed:', error);
            // Fall back to standard mode
            await handleStandardResponse(container, options);
        } finally {
            isProcessing = false;
            updateUIState(false);
        }
    }

    // Handle standard (non-streaming) response
    async function handleStandardResponse(container, options) {
        try {
            const contentElement = container.querySelector('.message-content');
            contentElement.innerHTML = '';

            if (window.loadingFeedbackManager) {
                window.loadingFeedbackManager.createStreamingIndicator(contentElement, 'Processing...');
            }

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation: conversationHistory,
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

            // Clear loading and show response
            contentElement.innerHTML = '';
            const textElement = document.createElement('div');
            textElement.classList.add('message-text-content');
            MarkdownRenderer.setContent(textElement, data.response);
            contentElement.appendChild(textElement);

            // Remove streaming class
            container.classList.remove('streaming', 'streaming-error');
            container.classList.add('standard-response');

            // Add to conversation history
            const assistantMessage = {
                role: 'assistant',
                content: data.response,
                timestamp: new Date().toISOString()
            };
            conversationHistory.push(assistantMessage);
            saveConversationToStorage();

            if (window.loadingFeedbackManager) {
                window.loadingFeedbackManager.showSuccessIndicator(container, 'Response completed');
            }

        } catch (error) {
            console.error('Standard response failed:', error);
            displayErrorMessage(error.message, 'standard', true);
        }
    }

    // Load conversation history from localStorage on page load
    function loadConversationFromStorage() {
        try {
            const stored = localStorage.getItem('synapse_conversation_history');
            if (stored) {
                const parsedHistory = JSON.parse(stored);
                if (Array.isArray(parsedHistory)) {
                    conversationHistory = parsedHistory;

                    // Clean up conversation history on load
                    conversationHistory = cleanupConversationHistory(conversationHistory);

                    // Restore conversation display
                    restoreConversationDisplay();

                    // Update performance metrics
                    performanceMetrics.messageCount = conversationHistory.length;

                    // If history is not empty after cleanup, we're done.
                    // Otherwise, fall through to initialize with a welcome message.
                    if (conversationHistory.length > 0) {
                        return;
                    }
                }
            }
        } catch (error) {
            console.warn('Failed to load conversation from localStorage:', error);
        }

        // If no stored conversation or error loading, start with welcome message
        initializeWithWelcomeMessage();
    }

    // Save conversation history to localStorage
    function saveConversationToStorage() {
        try {
            localStorage.setItem('synapse_conversation_history', JSON.stringify(conversationHistory));
        } catch (error) {
            console.warn('Failed to save conversation to localStorage:', error);
        }
    }

    // Restore conversation display from history
    function restoreConversationDisplay() {
        // Clear existing chat log
        chatLog.innerHTML = '';

        // Display all messages from history
        conversationHistory.forEach(message => {
            displayMessage(message.content, message.role);
        });
    }

    // Initialize with welcome message
    function initializeWithWelcomeMessage() {
        const welcomeMessage = {
            role: 'assistant',
            content: 'Hello! I\'m Synapse, your AI cognitive partner. I\'m here to engage in thoughtful conversations and help you explore your ideas. What would you like to discuss?'
        };

        conversationHistory.push(welcomeMessage);
        displayMessage(welcomeMessage.content, welcomeMessage.role);
        saveConversationToStorage();
    }

    // Clean up conversation history based on limits and age
    function cleanupConversationHistory(history) {
        if (!history || history.length === 0) {
            return history;
        }

        const now = new Date();
        const maxAgeMs = PERFORMANCE_CONFIG.MAX_MESSAGE_AGE_HOURS * 60 * 60 * 1000;

        // Remove messages older than max age
        let cleanedHistory = history.filter(message => {
            if (message.timestamp) {
                try {
                    const messageTime = new Date(message.timestamp);
                    return (now - messageTime) <= maxAgeMs;
                } catch (e) {
                    // If timestamp parsing fails, keep the message
                    return true;
                }
            }
            // If no timestamp, add current timestamp and keep
            message.timestamp = now.toISOString();
            return true;
        });

        // Limit number of messages while preserving conversation flow
        if (cleanedHistory.length > PERFORMANCE_CONFIG.MAX_CONVERSATION_LENGTH) {
            const messagesToKeep = PERFORMANCE_CONFIG.MAX_CONVERSATION_LENGTH;
            const result = [];

            // Start from the end and work backwards, keeping user/assistant pairs
            let i = cleanedHistory.length - 1;
            while (i >= 0 && result.length < messagesToKeep) {
                const message = cleanedHistory[i];
                result.unshift(message);

                // If this is an assistant message, try to keep the preceding user message
                if (message.role === 'assistant' &&
                    i > 0 &&
                    cleanedHistory[i - 1].role === 'user' &&
                    result.length < messagesToKeep) {
                    result.unshift(cleanedHistory[i - 1]);
                    i--;
                }
                i--;
            }

            cleanedHistory = result;
        }

        if (cleanedHistory.length !== history.length) {
            console.log(`Conversation history cleaned: ${history.length} -> ${cleanedHistory.length} messages`);
            performanceMetrics.lastCleanup = Date.now();
        }

        return cleanedHistory;
    }

    // Check if conversation history needs cleanup
    function shouldCleanupHistory() {
        const thresholdLength = Math.floor(PERFORMANCE_CONFIG.MAX_CONVERSATION_LENGTH * PERFORMANCE_CONFIG.CLEANUP_THRESHOLD / 100);
        return conversationHistory.length >= thresholdLength;
    }

    // Perform automatic cleanup if needed
    function performAutoCleanup() {
        if (shouldCleanupHistory()) {
            const originalLength = conversationHistory.length;
            conversationHistory = cleanupConversationHistory(conversationHistory);

            if (conversationHistory.length !== originalLength) {
                saveConversationToStorage();
                showCleanupNotification(originalLength, conversationHistory.length);
            }
        }
    }

    // Show cleanup notification to user
    function showCleanupNotification(oldCount, newCount) {
        const notification = document.createElement('div');
        notification.classList.add('message', 'system-message');
        notification.innerHTML = `
            <div class="system-notification">
                <strong>Conversation Optimized:</strong> Cleaned up conversation history 
                (${oldCount} → ${newCount} messages) to improve performance.
            </div>
        `;
        chatLog.appendChild(notification);

        // Auto-remove notification after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        scrollToBottom();
    }

    // Clear conversation history (useful for testing or starting fresh)
    function clearConversationHistory() {
        conversationHistory = [];
        chatLog.innerHTML = '';
        localStorage.removeItem('synapse_conversation_history');
        performanceMetrics.messageCount = 0;
        performanceMetrics.responseTimeHistory = [];
        initializeWithWelcomeMessage();
    }

    // Expose functions to global scope for debugging/testing
    window.clearConversationHistory = clearConversationHistory;
    window.getPerformanceMetrics = () => performanceMetrics;
    window.forceCleanup = performAutoCleanup;

    // Handle send button click
    sendButton.addEventListener('click', function () {
        sendMessage();
    });

    // Handle Enter key press in input field
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    async function sendMessage() {
        const message = messageInput.value.trim();

        // Validate input
        if (message === '' || isProcessing) {
            return;
        }

        // Check if cleanup is needed before sending
        if (shouldCleanupHistory()) {
            performAutoCleanup();
        }

        // Set processing state
        isProcessing = true;
        updateUIState(true);

        // Start response time tracking
        const requestStartTime = Date.now();

        // OPTIMISTIC UI: Display user message immediately
        displayMessage(message, 'user');

        // Add user message to conversation history with timestamp
        const userMessage = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        };
        conversationHistory.push(userMessage);

        // Save updated conversation to localStorage
        saveConversationToStorage();

        // Clear input field
        messageInput.value = '';

        // OPTIMISTIC UI: Create AI response bubble immediately with loading indicator
        const aiResponseElement = createStreamingResponseElement();

        try {
            // Try streaming first, fallback to regular if not supported
            const useStreaming = true; // Can be made configurable

            if (useStreaming) {
                await handleStreamingResponse(aiResponseElement, requestStartTime);
            } else {
                await handleRegularResponse(aiResponseElement, requestStartTime);
            }

        } catch (error) {
            // Remove the AI response element if there was an error
            if (aiResponseElement && aiResponseElement.parentNode) {
                aiResponseElement.remove();
            }

            // Calculate response time even for errors
            const responseTime = Date.now() - requestStartTime;
            updatePerformanceMetrics(responseTime, true);

            // Use the new error handling system
            if (window.streamingErrorHandler) {
                // Create a temporary response element for error display
                const errorResponseElement = createStreamingResponseElement();
                errorResponseElement.id = 'error_' + Date.now();

                window.streamingErrorHandler.handleStreamingError(
                    error,
                    errorResponseElement,
                    requestStartTime,
                    'chat_' + Date.now()
                );
            } else {
                // Fallback to old error handling
                displayErrorMessage(error.message || 'An unexpected error occurred. Please try again.', 'unknown', true);
            }

            console.error('Chat error:', error);
        } finally {
            // Reset processing state
            isProcessing = false;
            updateUIState(false);
        }
    }

    function createStreamingResponseElement() {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'ai-message', 'streaming');

        // Create content container
        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        messageElement.appendChild(contentElement);

        // Use enhanced loading feedback manager if available
        if (window.loadingFeedbackManager) {
            window.loadingFeedbackManager.createStreamingIndicator(contentElement, 'Synapse is thinking...');
            window.loadingFeedbackManager.createStreamingProgress(contentElement);
        } else {
            // Fallback to basic loading indicator
            const loadingElement = document.createElement('div');
            loadingElement.classList.add('streaming-indicator');
            loadingElement.innerHTML = `
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="streaming-text">Synapse is thinking...</span>
            `;
            contentElement.appendChild(loadingElement);
        }

        // Add to chat log
        chatLog.appendChild(messageElement);
        scrollToBottom();

        return messageElement;
    }

    /**
     * StreamingResponseHandler class to manage real-time response display
     * Handles Server-Sent Events, typewriter effects, cursor animation, and error recovery
     */
    class StreamingResponseHandler {
        constructor(chatInterface) {
            this.chatInterface = chatInterface;
            this.currentStream = null;
            this.abortController = null;
            this.typewriterSpeed = 30; // milliseconds between characters
            this.enableTypewriter = true;
            this.enableCursor = true;
        }

        /**
         * Handle streaming response with enhanced error handling and visual effects
         */
        async handleStreamingResponse(responseElement, requestStartTime) {
            const contentElement = responseElement.querySelector('.message-content');
            const loadingElement = responseElement.querySelector('.streaming-indicator');
            const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

            try {
                // Dispatch streaming started event
                document.dispatchEvent(new CustomEvent('streamingStarted', {
                    detail: {
                        requestId,
                        container: responseElement,
                        startTime: requestStartTime
                    }
                }));

                // Create AbortController for request timeout
                this.abortController = new AbortController();
                
                // Use adaptive timeout from performance monitor if available
                const adaptiveTimeout = window.streamingPerformanceMonitor ? 
                    window.streamingPerformanceMonitor.getCurrentTimeout() : 
                    PERFORMANCE_CONFIG.RESPONSE_TIMEOUT_MS;
                
                console.log(`Using timeout: ${adaptiveTimeout}ms (${Math.round(adaptiveTimeout/1000)}s)`);
                
                const timeoutSignal = setTimeout(() => {
                    console.log(`Streaming timeout reached after ${adaptiveTimeout}ms`);
                    this.abortController.abort();
                }, adaptiveTimeout);

                // Send streaming request
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        conversation: conversationHistory,
                        stream: true
                    }),
                    signal: this.abortController.signal
                });

                clearTimeout(timeoutSignal);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
                }

                // Remove loading indicator and prepare for streaming
                if (loadingElement) {
                    loadingElement.remove();
                }

                // Create streaming text element with cursor
                const textElement = this.createStreamingTextElement(contentElement);

                // Process streaming response with ReadableStream
                await this.processStreamingResponse(response, textElement, responseElement, requestStartTime, requestId);

            } catch (error) {
                this.handleStreamingError(error, responseElement, requestStartTime, requestId);
            }
        }

        /**
         * Create streaming text element with typewriter cursor
         */
        createStreamingTextElement(contentElement) {
            const textElement = document.createElement('div');
            textElement.classList.add('message-text-content');

            if (this.enableCursor) {
                textElement.classList.add('streaming-cursor');
            }

            contentElement.appendChild(textElement);
            return textElement;
        }

        /**
         * Process ReadableStream for Server-Sent Events
         */
        async processStreamingResponse(response, textElement, responseElement, requestStartTime, requestId) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';
            let buffer = '';
            let chunkCount = 0;

            // Track streaming performance
            const streamingStats = {
                startTime: Date.now(),
                totalChunks: 0,
                totalCharacters: 0,
                wordsPerSecond: 0
            };

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                // Decode chunk and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete lines from buffer
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.error) {
                                throw new Error(data.error);
                            }

                            if (data.content) {
                                chunkCount++;
                                streamingStats.totalChunks++;
                                streamingStats.totalCharacters += data.content.length;

                                // Dispatch chunk received event for performance monitoring
                                document.dispatchEvent(new CustomEvent('streamingChunk', {
                                    detail: {
                                        requestId,
                                        chunkContent: data.content,
                                        chunkId: data.chunk_id || chunkCount,
                                        timestamp: Date.now()
                                    }
                                }));

                                // Add content with typewriter effect
                                await this.appendContentWithTypewriter(textElement, data.content, fullResponse);
                                fullResponse += data.content;

                                // Update streaming stats
                                this.updateStreamingStats(streamingStats);
                            }

                            if (data.done) {
                                // Streaming complete
                                await this.finalizeStreamingResponse(
                                    responseElement,
                                    textElement,
                                    fullResponse,
                                    requestStartTime,
                                    streamingStats,
                                    requestId
                                );
                                return;
                            }
                        } catch (parseError) {
                            console.warn('Failed to parse streaming data:', parseError);
                        }
                    }
                }
            }
        }

        /**
         * Append content with typewriter effect and cursor animation
         */
        async appendContentWithTypewriter(textElement, newContent, currentContent) {
            if (!this.enableTypewriter || newContent.length === 0) {
                // No typewriter effect, append immediately
                if (window.performanceOptimizer) {
                    window.performanceOptimizer.optimizeStreamingRender(textElement, currentContent + newContent);
                    window.performanceOptimizer.optimizeDOMUpdate(scrollToBottom);
                } else {
                    // Use Markdown renderer for streaming content
                    MarkdownRenderer.setContent(textElement, currentContent + newContent);
                    scrollToBottom();
                }
                return;
            }

            // Typewriter effect: add characters one by one
            for (let i = 0; i < newContent.length; i++) {
                if (this.abortController && this.abortController.signal.aborted) {
                    break;
                }

                const char = newContent[i];
                if (window.performanceOptimizer) {
                    window.performanceOptimizer.optimizeStreamingRender(textElement, currentContent + newContent.substring(0, i + 1));
                    window.performanceOptimizer.optimizeDOMUpdate(scrollToBottom);
                } else {
                    // Use Markdown renderer for typewriter effect
                    MarkdownRenderer.setContent(textElement, currentContent + newContent.substring(0, i + 1));
                    scrollToBottom();
                }

                // Variable speed based on character type
                let delay = this.typewriterSpeed;
                if (char === ' ') delay = this.typewriterSpeed * 0.5; // Faster for spaces
                if (char === '.' || char === '!' || char === '?') delay = this.typewriterSpeed * 2; // Slower for punctuation

                await this.sleep(delay);
            }
        }

        /**
         * Update streaming performance statistics
         */
        updateStreamingStats(stats) {
            const elapsed = (Date.now() - stats.startTime) / 1000;
            stats.wordsPerSecond = Math.round((stats.totalCharacters / 5) / elapsed * 10) / 10;

            // Optional: Display streaming stats for debugging
            if (window.DEBUG_STREAMING) {
                console.log(`Streaming: ${stats.totalChunks} chunks, ${stats.totalCharacters} chars, ${stats.wordsPerSecond} WPS`);
            }
        }

        /**
         * Finalize streaming response and clean up
         */
        async finalizeStreamingResponse(responseElement, textElement, fullResponse, requestStartTime, streamingStats, requestId) {
            const responseTime = Date.now() - requestStartTime;

            // Remove streaming class and cursor
            responseElement.classList.remove('streaming');
            textElement.classList.remove('streaming-cursor');

            // Add completion class for visual feedback
            responseElement.classList.add('streaming-complete');

            // Dispatch streaming completed event
            document.dispatchEvent(new CustomEvent('streamingCompleted', {
                detail: {
                    requestId,
                    container: responseElement,
                    responseTime,
                    streamingStats,
                    fullResponse
                }
            }));

            // Add to conversation history
            const assistantMessage = {
                role: 'assistant',
                content: fullResponse,
                timestamp: new Date().toISOString(),
                streamingStats: {
                    responseTime,
                    totalChunks: streamingStats.totalChunks,
                    totalCharacters: streamingStats.totalCharacters,
                    wordsPerSecond: streamingStats.wordsPerSecond
                }
            };
            conversationHistory.push(assistantMessage);

            // Update performance metrics
            updatePerformanceMetrics(responseTime);

            // Save updated conversation
            saveConversationToStorage();

            console.log(`Streaming response completed: ${fullResponse.length} characters in ${responseTime}ms (${streamingStats.wordsPerSecond} WPS)`);
        }

        /**
         * Handle streaming errors with graceful fallback
         */
        handleStreamingError(error, responseElement, requestStartTime, requestId) {
            // Dispatch streaming error event for performance monitoring
            let errorType = 'unknown';
            if (error.name === 'AbortError') {
                errorType = 'timeout';
            } else if (error.message && error.message.includes('network')) {
                errorType = 'connection';
            } else if (error.message && error.message.includes('timeout')) {
                errorType = 'timeout';
            }

            document.dispatchEvent(new CustomEvent('streamingError', {
                detail: {
                    requestId,
                    container: responseElement,
                    error,
                    errorType,
                    responseTime: Date.now() - requestStartTime
                }
            }));

            // Use the new comprehensive error handling system
            if (window.streamingErrorHandler) {
                window.streamingErrorHandler.handleStreamingError(
                    error,
                    responseElement,
                    requestStartTime,
                    requestId
                );
            } else {
                // Fallback error handling
                this.showBasicError(responseElement, error);
            }
        }

        /**
         * Basic error display fallback
         */
        showBasicError(responseElement, error) {
            const contentElement = responseElement.querySelector('.message-content');
            if (contentElement) {
                contentElement.innerHTML = `
                    <div class="basic-error">
                        <p>❌ Error: ${error.message}</p>
                        <button onclick="window.location.reload()">Refresh Page</button>
                    </div>
                `;
            }
        }

        /**
         * Handle timeout errors with retry options
         */
        handleTimeoutError(responseElement, requestStartTime) {
    this.showStreamingErrorMessage(responseElement, {
        title: 'Response Timeout',
        message: 'The AI is taking longer than expected. This might be a complex query.',
        category: 'timeout',
        actions: [
            {
                text: 'Retry Streaming',
                action: () => this.retryStreaming(responseElement, requestStartTime),
                primary: true
            },
            {
                text: 'Use Standard Mode',
                action: () => this.fallbackToStandard(responseElement, requestStartTime),
                primary: false
            }
        ]
    });
}

        /**
         * Handle network errors
         */
        handleNetworkError(responseElement, requestStartTime) {
    this.showStreamingErrorMessage(responseElement, {
        title: 'Connection Error',
        message: 'Unable to establish streaming connection. Check your network connection.',
        category: 'network',
        actions: [
            {
                text: 'Retry',
                action: () => this.retryStreaming(responseElement, requestStartTime),
                primary: true
            },
            {
                text: 'Use Standard Mode',
                action: () => this.fallbackToStandard(responseElement, requestStartTime),
                primary: false
            }
        ]
    });
}

        /**
         * Handle generic streaming errors
         */
        handleGenericStreamingError(responseElement, error, requestStartTime) {
    this.showStreamingErrorMessage(responseElement, {
        title: 'Streaming Error',
        message: error.message || 'An unexpected error occurred during streaming.',
        category: 'generic',
        actions: [
            {
                text: 'Try Standard Mode',
                action: () => this.fallbackToStandard(responseElement, requestStartTime),
                primary: true
            }
        ]
    });
}

        /**
         * Show streaming error message with recovery options
         */
        showStreamingErrorMessage(responseElement, errorConfig) {
    const contentElement = responseElement.querySelector('.message-content');
    contentElement.innerHTML = '';

    const errorElement = document.createElement('div');
    errorElement.classList.add('streaming-error-content');
    errorElement.innerHTML = `
                <div class="streaming-error-header">
                    <div class="streaming-error-icon">⚠️</div>
                    <div class="streaming-error-title">${errorConfig.title}</div>
                </div>
                <div class="streaming-error-message">${errorConfig.message}</div>
                <div class="streaming-error-actions">
                    ${errorConfig.actions.map(action => `
                        <button class="streaming-retry-button ${action.primary ? 'primary' : 'secondary'}" 
                                data-action="${action.text}">
                            ${action.text}
                        </button>
                    `).join('')}
                </div>
            `;

    // Add event listeners for action buttons
    errorConfig.actions.forEach(action => {
        const button = errorElement.querySelector(`[data-action="${action.text}"]`);
        if (button) {
            button.addEventListener('click', action.action);
        }
    });

            contentElement.appendChild(errorElement);
            scrollToBottom();
        }


        /**
         * Retry streaming with the same parameters
         */
        async retryStreaming(responseElement, requestStartTime) {
            // Reset element state
            responseElement.classList.remove('streaming-error');
            responseElement.classList.add('streaming');

            // Clear content and show loading
            const contentElement = responseElement.querySelector('.message-content');
            contentElement.innerHTML = '';

            const loadingElement = document.createElement('div');
            loadingElement.classList.add('streaming-indicator');
            loadingElement.innerHTML = `
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="streaming-text">Retrying connection...</span>
            `;
            contentElement.appendChild(loadingElement);

            // Retry streaming
            try {
                await this.handleStreamingResponse(responseElement, requestStartTime);
            } catch (error) {
                console.error('Retry streaming failed:', error);
                this.fallbackToStandard(responseElement, requestStartTime);
            }
        }

        /**
         * Fallback to standard (non-streaming) response mode
         */
        async fallbackToStandard(responseElement, requestStartTime) {
            console.log('Falling back to standard response mode');

            // Reset element state
            responseElement.classList.remove('streaming', 'streaming-error');
            responseElement.classList.add('fallback-mode');

            try {
                await handleRegularResponse(responseElement, requestStartTime);
            } catch (error) {
                console.error('Fallback to standard mode failed:', error);
                throw error; // Re-throw to be handled by parent
            }
        }

        /**
         * Utility function for delays
         */
        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        /**
         * Abort current streaming request
         */
        abort() {
            if (this.abortController) {
                this.abortController.abort();
                this.abortController = null;
            }
        }

        /**
         * Configure typewriter settings
         */
        configureTypewriter(options = {}) {
            this.typewriterSpeed = options.speed || this.typewriterSpeed;
            this.enableTypewriter = options.enabled !== undefined ? options.enabled : this.enableTypewriter;
            this.enableCursor = options.cursor !== undefined ? options.cursor : this.enableCursor;
        }
    }

// Create global streaming handler instance
const streamingHandler = new StreamingResponseHandler({
    scrollToBottom: scrollToBottom
});

// Legacy function wrapper for backward compatibility
async function handleStreamingResponse(aiResponseElement, requestStartTime) {
    return await streamingHandler.handleStreamingResponse(aiResponseElement, requestStartTime);
}

async function handleRegularResponse(aiResponseElement, requestStartTime) {
    const contentElement = aiResponseElement.querySelector('.message-content');
    const loadingElement = aiResponseElement.querySelector('.streaming-indicator');

    try {
        // Create AbortController for request timeout
        const controller = new AbortController();
        
        // Use adaptive timeout from performance monitor if available
        const adaptiveTimeout = window.streamingPerformanceMonitor ? 
            window.streamingPerformanceMonitor.getCurrentTimeout() : 
            PERFORMANCE_CONFIG.RESPONSE_TIMEOUT_MS;
            
        const timeoutSignal = setTimeout(() => controller.abort(), adaptiveTimeout);

        // Send regular request
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                conversation: conversationHistory,
                stream: false
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutSignal);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const responseTime = Date.now() - requestStartTime;

        // Remove loading indicator
        if (loadingElement) {
            loadingElement.remove();
        }

        // Display response
        const textElement = document.createElement('div');
        textElement.classList.add('message-text-content');
        MarkdownRenderer.setContent(textElement, data.message);
        contentElement.appendChild(textElement);

        // Remove streaming class
        aiResponseElement.classList.remove('streaming');

        // Add to conversation history
        const assistantMessage = {
            role: 'assistant',
            content: data.message,
            timestamp: new Date().toISOString()
        };
        conversationHistory.push(assistantMessage);

        // Update performance metrics
        updatePerformanceMetrics(responseTime);

        // Save updated conversation
        saveConversationToStorage();

        // Show performance feedback if response was slow
        if (responseTime > 5000) {
            showPerformanceNotification(responseTime);
        }

        scrollToBottom();

    } catch (error) {
        throw error; // Re-throw to be handled by parent function
    }
}

function displayMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');

    if (sender === 'user') {
        messageElement.classList.add('user-message');
    } else if (sender === 'assistant') {
        messageElement.classList.add('ai-message');
    }

    messageElement.textContent = message;
    chatLog.appendChild(messageElement);

    // Scroll to bottom
    scrollToBottom();
}

function displayErrorMessage(errorText, category = 'unknown', showRetry = true) {
    const errorElement = document.createElement('div');
    errorElement.classList.add('message', 'error-message');
    errorElement.setAttribute('data-error-category', category);

    // Create error content
    const errorContent = document.createElement('div');
    errorContent.classList.add('error-content');
    errorContent.textContent = `Error: ${errorText}`;
    errorElement.appendChild(errorContent);

    // Add retry button if applicable
    if (showRetry) {
        const retryButton = document.createElement('button');
        retryButton.classList.add('retry-button');
        retryButton.textContent = 'Retry';
        retryButton.onclick = function () {
            // Remove error message and retry last message
            errorElement.remove();
            retryLastMessage();
        };
        errorElement.appendChild(retryButton);
    }

    // Add recovery suggestions based on error category
    const suggestions = getRecoverySuggestions(category);
    if (suggestions.length > 0) {
        const suggestionsElement = document.createElement('div');
        suggestionsElement.classList.add('error-suggestions');
        suggestionsElement.innerHTML = '<strong>Suggestions:</strong><ul>' +
            suggestions.map(s => `<li>${s}</li>`).join('') + '</ul>';
        errorElement.appendChild(suggestionsElement);
    }

    chatLog.appendChild(errorElement);

    // Scroll to bottom
    scrollToBottom();
}

function getRecoverySuggestions(category) {
    const suggestions = {
        'network': [
            'Check your internet connection',
            'Refresh the page and try again',
            'Wait a moment and retry'
        ],
        'ai_service': [
            'Ensure Ollama is running on your system',
            'Check that the llama3:8b model is installed',
            'Try restarting Ollama service'
        ],
        'timeout': [
            'Try asking a simpler question',
            'Break complex requests into smaller parts',
            'Wait a moment before retrying'
        ],
        'validation': [
            'Check your message for special characters',
            'Try rephrasing your question',
            'Ensure your message is not empty'
        ]
    };

    return suggestions[category] || [
        'Refresh the page if the problem persists',
        'Try again in a few moments',
        'Check the browser console for more details'
    ];
}

function retryLastMessage() {
    // Get the last user message from conversation history
    const lastUserMessage = [...conversationHistory].reverse().find(msg => msg.role === 'user');
    if (lastUserMessage) {
        // Remove the last user message from history and display
        const lastUserIndex = conversationHistory.lastIndexOf(lastUserMessage);
        if (lastUserIndex !== -1) {
            conversationHistory.splice(lastUserIndex, 1);

            // Remove the last AI response if it exists
            if (conversationHistory.length > 0 && conversationHistory[conversationHistory.length - 1].role === 'assistant') {
                conversationHistory.pop();
            }

            // Restore conversation display
            restoreConversationDisplay();

            // Set the input field with the last message and send it
            messageInput.value = lastUserMessage.content;
            sendMessage();
        }
    }
}

function logClientError(error, category, context) {
    // Log error to browser console with additional context
    console.group('Synapse Client Error');
    console.error('Error:', error);
    console.log('Category:', category);
    console.log('Context:', context);
    console.log('Timestamp:', new Date().toISOString());
    console.log('User Agent:', navigator.userAgent);
    console.groupEnd();

    // Store error in localStorage for debugging
    try {
        const errorLog = JSON.parse(localStorage.getItem('synapse_error_log') || '[]');
        errorLog.push({
            timestamp: new Date().toISOString(),
            error: error.message,
            category: category,
            context: context,
            userAgent: navigator.userAgent
        });

        // Keep only last 10 errors
        if (errorLog.length > 10) {
            errorLog.splice(0, errorLog.length - 10);
        }

        localStorage.setItem('synapse_error_log', JSON.stringify(errorLog));
    } catch (e) {
        console.warn('Failed to log error to localStorage:', e);
    }
}

function showEnhancedLoadingIndicator() {
    const loadingElement = document.createElement('div');
    loadingElement.classList.add('message', 'loading-message');
    loadingElement.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <span class="loading-text">Synapse is thinking<span class="dots">...</span></span>
                <div class="loading-progress">
                    <div class="progress-bar"></div>
                </div>
                <div class="loading-time">0s</div>
            </div>
        `;
    chatLog.appendChild(loadingElement);

    // Start timer for loading indicator
    const startTime = Date.now();
    const timeElement = loadingElement.querySelector('.loading-time');
    const progressBar = loadingElement.querySelector('.progress-bar');

    const updateTimer = setInterval(() => {
        if (!loadingElement.parentNode) {
            clearInterval(updateTimer);
            return;
        }

        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        timeElement.textContent = `${elapsed}s`;

        // Update progress bar (visual feedback)
        const progress = Math.min((elapsed / 30) * 100, 95); // Max 95% until complete
        progressBar.style.width = `${progress}%`;

        // Change loading text based on time elapsed
        const textElement = loadingElement.querySelector('.loading-text');
        if (elapsed > 15) {
            textElement.innerHTML = 'Processing complex response<span class="dots">...</span>';
        } else if (elapsed > 8) {
            textElement.innerHTML = 'Generating thoughtful response<span class="dots">...</span>';
        }
    }, 1000);

    // Store timer reference for cleanup
    loadingElement._updateTimer = updateTimer;

    // Scroll to bottom
    scrollToBottom();

    return loadingElement;
}

function updateLoadingIndicator(loadingElement, message) {
    if (loadingElement && loadingElement.parentNode) {
        const textElement = loadingElement.querySelector('.loading-text');
        if (textElement) {
            textElement.innerHTML = message;
        }
    }
}

function removeLoadingIndicator(loadingElement) {
    if (loadingElement && loadingElement.parentNode) {
        // Clear timer if it exists
        if (loadingElement._updateTimer) {
            clearInterval(loadingElement._updateTimer);
        }
        loadingElement.parentNode.removeChild(loadingElement);
    }
}

function showLoadingIndicator() {
    // Fallback to simple loading indicator for compatibility
    return showEnhancedLoadingIndicator();
}

function updateUIState(processing) {
    // Update send button state
    sendButton.disabled = processing;
    sendButton.textContent = processing ? 'Sending...' : 'Send';

    // Update input field state
    messageInput.disabled = processing;

    // Update visual styling
    if (processing) {
        sendButton.classList.add('processing');
        messageInput.classList.add('processing');
    } else {
        sendButton.classList.remove('processing');
        messageInput.classList.remove('processing');
        // Focus back on input after processing
        messageInput.focus();
    }
}

function scrollToBottom() {
    // Smooth scroll to bottom
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Performance monitoring functions
function updatePerformanceMetrics(responseTime, isError = false) {
    performanceMetrics.responseTimeHistory.push({
        time: responseTime,
        timestamp: Date.now(),
        isError: isError
    });

    // Keep only last 50 response times
    if (performanceMetrics.responseTimeHistory.length > 50) {
        performanceMetrics.responseTimeHistory.shift();
    }

    // Calculate average response time
    const validResponses = performanceMetrics.responseTimeHistory.filter(r => !r.isError);
    if (validResponses.length > 0) {
        performanceMetrics.averageResponseTime = validResponses.reduce((sum, r) => sum + r.time, 0) / validResponses.length;
    }

    performanceMetrics.messageCount = conversationHistory.length;
}

function showPerformanceNotification(responseTime) {
    const notification = document.createElement('div');
    notification.classList.add('message', 'performance-notification');
    notification.innerHTML = `
            <div class="performance-info">
                <strong>Performance Notice:</strong> Response took ${(responseTime / 1000).toFixed(1)}s. 
                Consider clearing conversation history if responses continue to be slow.
                <button class="optimize-button" onclick="performAutoCleanup()">Optimize Now</button>
            </div>
        `;
    chatLog.appendChild(notification);

    // Auto-remove notification after 10 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 10000);

    scrollToBottom();
}

function getPerformanceStatus() {
    return {
        ...performanceMetrics,
        conversationLength: conversationHistory.length,
        needsCleanup: shouldCleanupHistory(),
        lastCleanupAge: Date.now() - performanceMetrics.lastCleanup
    };
}

// Auto-cleanup timer setup
function setupAutoCleanup() {
    if (autoCleanupTimer) {
        clearInterval(autoCleanupTimer);
    }

    autoCleanupTimer = setInterval(() => {
        // Only cleanup if conversation is getting long and it's been a while since last cleanup
        const timeSinceLastCleanup = Date.now() - performanceMetrics.lastCleanup;
        if (shouldCleanupHistory() && timeSinceLastCleanup > PERFORMANCE_CONFIG.AUTO_CLEANUP_INTERVAL) {
            performAutoCleanup();
        }
    }, PERFORMANCE_CONFIG.AUTO_CLEANUP_INTERVAL);
}

// Initialize performance monitoring
function initializePerformanceMonitoring() {
    // Record initial memory usage if available
    if (performance && performance.memory) {
        console.log('Initial memory usage:', {
            used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB',
            total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024) + 'MB',
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024) + 'MB'
        });
    }

    // Setup auto-cleanup
    setupAutoCleanup();

    // Expose performance functions globally for debugging
    window.getPerformanceStatus = getPerformanceStatus;
    window.optimizeConversation = performAutoCleanup;
}

// Setup loading feedback integration
setupLoadingFeedbackIntegration();

// Load conversation history from localStorage or initialize with welcome message
loadConversationFromStorage();

// Initialize dashboard functionality if present
function initializeDashboard() {
    const refreshButton = document.getElementById('refresh-dashboard');
    if (refreshButton) {
        refreshButton.addEventListener('click', function () {
            // Trigger dashboard refresh if Dashboard class is available
            if (window.dashboard && typeof window.dashboard.loadDashboardData === 'function') {
                window.dashboard.loadDashboardData();
            }
        });
    }

    // The Dashboard object is now initialized in dashboard.js to prevent duplicates.
    // This function just sets up event listeners that depend on the dashboard.
}

// Initialize performance monitoring
initializePerformanceMonitoring();

// Initialize dashboard if present
initializeDashboard();

// Initialize performance optimizer integration
initializePerformanceOptimizerIntegration();

// Focus on input field when page loads
messageInput.focus();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (autoCleanupTimer) {
        clearInterval(autoCleanupTimer);
    }
});
});

/**
 * Initialize performance optimizer integration with chat functionality
 */
function initializePerformanceOptimizerIntegration() {
    // Wait for performance optimizer to be available
    const checkPerformanceOptimizer = () => {
        if (window.performanceOptimizer) {
            console.log('Integrating chat with performance optimizer...');

            // Override the original streaming text update functions to use performance optimization
            if (window.StreamingResponseHandler) {
                const originalUpdateStreamingText = window.StreamingResponseHandler.prototype.updateStreamingText;
                if (originalUpdateStreamingText) {
                    window.StreamingResponseHandler.prototype.updateStreamingText = function (textElement, content) {
                        // Use performance optimizer for smooth text updates
                        window.performanceOptimizer.optimizeStreamingRender(textElement, content);
                        if (typeof scrollToBottom === 'function') {
                            window.performanceOptimizer.optimizeDOMUpdate(scrollToBottom);
                        }
                    };
                }
            }

            console.log('Chat performance optimization integration completed');
        } else {
            // Retry after a short delay
            setTimeout(checkPerformanceOptimizer, 100);
        }
    };

    checkPerformanceOptimizer();
}