from flask import Flask, render_template, request, jsonify, Response
import os
import logging
import time
from datetime import datetime
from config import get_config, print_config_summary
from ai_service import get_ai_service, AIServiceError
from memory_service import get_memory_service, MemoryServiceError
from serendipity_service import get_serendipity_service, SerendipityServiceError
from prompt_service import get_prompt_service, PromptServiceError
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, create_error_response
from performance_optimizer import (
    performance_metrics, conversation_manager, file_optimizer, response_monitor,
    cleanup_system_resources, get_performance_status
)
from security import (
    security_required, InputValidator, get_file_system_security, 
    validate_file_access, sanitize_error_for_user, ErrorSanitizer
)

# Load configuration
config = get_config()

# Configure logging based on config
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Apply configuration to Flask app
app.config.update(config.get_config_dict())

# Print configuration summary in development mode
if getattr(config, 'DEBUG', False):
    print_config_summary(config)

# Global error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    error_handler = get_error_handler()
    error_info = error_handler.log_error(
        Exception("Page not found"),
        ErrorCategory.UNKNOWN,
        ErrorSeverity.LOW,
        {"path": request.path, "method": request.method}
    )
    response, status_code = create_error_response(error_info, 404)
    return jsonify(response), status_code

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    error_handler = get_error_handler()
    error_info = error_handler.log_error(
        error.original_exception if hasattr(error, 'original_exception') else Exception("Internal server error"),
        ErrorCategory.UNKNOWN,
        ErrorSeverity.HIGH,
        {"path": request.path, "method": request.method}
    )
    response, status_code = create_error_response(error_info, 500)
    return jsonify(response), status_code

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    error_handler = get_error_handler()
    error_info = error_handler.log_error(
        e,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.CRITICAL,
        {"path": request.path, "method": request.method}
    )
    response, status_code = create_error_response(error_info, 500)
    return jsonify(response), status_code

# System prompt will be loaded from prompt service
def get_current_system_prompt():
    """Get the current system prompt from the prompt service"""
    try:
        prompt_service = get_prompt_service()
        return prompt_service.get_current_prompt()
    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        # Fallback to default prompt
        return """You are Synapse, an intelligent cognitive partner designed to engage in thoughtful, insightful conversations. You are curious, analytical, and genuinely interested in understanding the user's thoughts and perspectives. You ask probing questions, make connections between ideas, and help users explore their thinking more deeply. You are supportive but also intellectually challenging, encouraging users to consider new angles and possibilities. Your responses are conversational yet substantive, balancing warmth with intellectual rigor."""

@app.route('/')
def index():
    """Main route to serve the chat interface"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard route to serve the cognitive insights interface"""
    return render_template('dashboard.html')

@app.route('/prompts')
def prompts():
    """Prompts route to serve the system prompt management interface"""
    return render_template('prompts.html')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    return '', 204  # No Content response

@app.route('/api/status')
def api_status():
    """API endpoint to check AI service status with enhanced error handling"""
    try:
        ai_service = get_ai_service(
            model=config.OLLAMA_MODEL,
            system_prompt=get_current_system_prompt()
        )
        status = ai_service.test_connection()
        
        # Add error handler statistics
        error_handler = get_error_handler()
        status['error_stats'] = error_handler.get_error_stats()
        
        return jsonify(status)
    except AIServiceError as e:
        error_handler = get_error_handler()
        error_info = error_handler.log_error(e, ErrorCategory.AI_SERVICE, ErrorSeverity.MEDIUM)
        response, status_code = create_error_response(error_info, 503)
        return jsonify(response), status_code
    except Exception as e:
        error_handler = get_error_handler()
        error_info = error_handler.log_error(e, ErrorCategory.AI_SERVICE, ErrorSeverity.HIGH)
        response, status_code = create_error_response(error_info, 500)
        return jsonify(response), status_code

@app.route('/api/log-error', methods=['POST'])
def log_client_error():
    """API endpoint to log client-side errors for debugging"""
    try:
        error_data = request.get_json()
        if not error_data:
            return jsonify({'error': 'No error data provided'}), 400
        
        # Sanitize error data
        sanitized_data = {
            'type': error_data.get('type', 'unknown'),
            'error_name': error_data.get('error', {}).get('name', 'Unknown'),
            'error_message': error_data.get('error', {}).get('message', 'No message'),
            'timestamp': error_data.get('timestamp'),
            'url': error_data.get('url'),
            'user_agent': error_data.get('userAgent', '')[:200],  # Limit length
            'metadata': error_data.get('metadata', {})
        }
        
        # Log the client error
        logger.error(f"Client Error - {sanitized_data['type']}: {sanitized_data['error_message']}", 
                    extra={'client_error_data': sanitized_data})
        
        return jsonify({'status': 'logged', 'timestamp': datetime.now().isoformat()})
        
    except Exception as e:
        logger.error(f"Failed to log client error: {e}")
        return jsonify({'error': 'Failed to log error'}), 500

@app.route('/api/log-chart-error', methods=['POST'])
def log_chart_error():
    """API endpoint to log chart-specific errors for debugging"""
    try:
        error_data = request.get_json()
        if not error_data:
            return jsonify({'error': 'No error data provided'}), 400
        
        # Sanitize chart error data
        sanitized_data = {
            'chart_id': error_data.get('chartId', 'unknown'),
            'chart_type': error_data.get('chartType', 'unknown'),
            'error_name': error_data.get('error', {}).get('name', 'Unknown'),
            'error_message': error_data.get('error', {}).get('message', 'No message'),
            'timestamp': error_data.get('timestamp'),
            'retry_attempt': error_data.get('retryAttempt', 0),
            'context': error_data.get('context', {})
        }
        
        # Log the chart error
        logger.error(f"Chart Error - {sanitized_data['chart_id']} ({sanitized_data['chart_type']}): {sanitized_data['error_message']}", 
                    extra={'chart_error_data': sanitized_data})
        
        return jsonify({'status': 'logged', 'timestamp': datetime.now().isoformat()})
        
    except Exception as e:
        logger.error(f"Failed to log chart error: {e}")
        return jsonify({'error': 'Failed to log error'}), 500

@app.route('/chat', methods=['POST', 'OPTIONS'])
@response_monitor.monitor_request
@security_required(validate_json=True, validate_conversation=True)
def chat():
    """
    Chat API endpoint to handle conversation requests
    
    Expects JSON payload with conversation history array and optional stream parameter
    Returns JSON response with AI-generated message or streaming response
    """
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Cache-Control, X-Requested-With')
        return response
    
    try:
        # Validate request content type
        if not request.is_json:
            logger.warning("Chat request received without JSON content type")
            return jsonify({
                "error": "Request must be JSON",
                "message": "Content-Type must be application/json"
            }), 400
        
        # Get request data (already validated by security decorator)
        data = request.get_json()
        
        # Validate that data is not None and has conversation key
        if data is None:
            return jsonify({
                "error": "Invalid request data",
                "message": "Request data cannot be null"
            }), 400
        
        if 'conversation' not in data:
            return jsonify({
                "error": "Invalid request data", 
                "message": "Missing 'conversation' field"
            }), 400
        
        # Check if streaming is requested
        stream_requested = data.get('stream', False)
        
        # Conversation history has already been validated and sanitized by security decorator
        conversation_history = data['conversation']
        
        # Validate conversation is not empty
        if len(conversation_history) == 0:
            return jsonify({
                "error": "Invalid conversation data",
                "message": "Conversation history cannot be empty"
            }), 400
        
        # Apply conversation history cleanup if needed
        if conversation_manager.should_cleanup(len(conversation_history)):
            original_length = len(conversation_history)
            conversation_history = conversation_manager.cleanup_conversation_history(conversation_history)
            if len(conversation_history) != original_length:
                logger.info(f"Cleaned up conversation history: {original_length} -> {len(conversation_history)} messages")
        
        # Record conversation statistics
        performance_metrics.conversation_stats['total_requests'] += 1
        performance_metrics.conversation_stats['total_messages'] += len(conversation_history)
        
        # Log the incoming request
        logger.info(f"Processing chat request with {len(conversation_history)} messages (streaming: {stream_requested})")
        
        # Get AI service instance
        ai_service = get_ai_service(
            model=config.OLLAMA_MODEL,
            system_prompt=get_current_system_prompt()
        )
        
        if stream_requested:
            # Return streaming response
            return handle_streaming_chat(ai_service, conversation_history)
        else:
            # Process conversation with AI (non-streaming)
            ai_response = ai_service.chat(conversation_history)
            
            # Return successful response
            response_data = {
                "message": ai_response,
                "timestamp": datetime.now().isoformat(),
                "model": config.OLLAMA_MODEL
            }
            
            logger.info(f"Successfully processed chat request, response length: {len(ai_response)}")
            return jsonify(response_data)
        
    except AIServiceError as e:
        error_handler = get_error_handler()
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "AI service error")
        error_info = error_handler.log_error(
            e,
            ErrorCategory.AI_SERVICE,
            ErrorSeverity.MEDIUM,
            {"conversation_length": len(conversation_history) if 'conversation_history' in locals() else 0}
        )
        # Override user message with sanitized version
        error_info["user_message"] = sanitized_message
        response, status_code = create_error_response(error_info, 503)
        return jsonify(response), status_code
    
    except Exception as e:
        error_handler = get_error_handler()
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Chat processing error")
        error_info = error_handler.log_error(
            e,
            ErrorCategory.UNKNOWN,
            ErrorSeverity.HIGH,
            {"conversation_length": len(conversation_history) if 'conversation_history' in locals() else 0}
        )
        # Override user message with sanitized version
        error_info["user_message"] = sanitized_message
        response, status_code = create_error_response(error_info, 500)
        return jsonify(response), status_code

def generate_streaming_response(ai_service, conversation_history):
    """
    Generate Server-Sent Events for streaming AI response
    
    This function yields AI response chunks in real-time as Server-Sent Events,
    providing proper error handling and performance monitoring.
    
    Args:
        ai_service: The AI service instance
        conversation_history: The conversation history
        
    Yields:
        str: Server-Sent Event formatted data chunks
    """
    import json
    
    try:
        # Record streaming start time for performance monitoring
        stream_start_time = time.time()
        total_chunks = 0
        total_characters = 0
        
        logger.info(f"Starting streaming response for conversation with {len(conversation_history)} messages")
        
        # Get streaming response from AI service
        stream_generator = ai_service.chat(conversation_history, stream=True)
        
        for chunk_data in stream_generator:
            total_chunks += 1
            chunk_content = chunk_data.get("content", "")
            total_characters += len(chunk_content)
            
            # Calculate streaming performance metrics
            elapsed_time = time.time() - stream_start_time
            words_per_second = (total_characters / 5) / elapsed_time if elapsed_time > 0 else 0  # Approximate words
            
            # Calculate performance metrics for monitoring
            chunk_latency = time.time() - (chunk_data.get("chunk_start_time", stream_start_time))
            
            # Format chunk as Server-Sent Events with enhanced metadata
            chunk_json = json.dumps({
                "content": chunk_content,
                "full_content": chunk_data.get("full_content", ""),
                "chunk_id": chunk_data.get("chunk_id", total_chunks),
                "timestamp": datetime.now().isoformat(),
                "done": chunk_data.get("done", False),
                "model": config.OLLAMA_MODEL,
                "error": chunk_data.get("error"),
                "streaming_stats": {
                    "total_chunks": total_chunks,
                    "total_characters": total_characters,
                    "elapsed_time": round(elapsed_time, 3),
                    "words_per_second": round(words_per_second, 1),
                    "chunk_latency": round(chunk_latency, 3),
                    "average_chunk_size": round(total_characters / total_chunks, 1) if total_chunks > 0 else 0
                },
                "performance_metrics": {
                    "response_time_ms": round(elapsed_time * 1000),
                    "throughput_chars_per_sec": round(total_characters / elapsed_time) if elapsed_time > 0 else 0,
                    "chunk_frequency_hz": round(total_chunks / elapsed_time) if elapsed_time > 0 else 0
                }
            })
            
            yield f"data: {chunk_json}\n\n"
            
            # If this is the final chunk, log completion and break
            if chunk_data.get("done", False):
                logger.info(f"Streaming completed: {total_chunks} chunks, {total_characters} characters in {elapsed_time:.2f}s")
                break
                
    except Exception as e:
        # Log streaming error
        error_handler = get_error_handler()
        error_info = error_handler.log_error(
            e,
            ErrorCategory.AI_SERVICE,
            ErrorSeverity.HIGH,
            {
                "streaming": True,
                "conversation_length": len(conversation_history),
                "chunks_sent": total_chunks if 'total_chunks' in locals() else 0
            }
        )
        
        # Send error chunk with sanitized error message
        sanitized_error = sanitize_error_for_user(e, "Streaming response error")
        error_chunk = json.dumps({
            "content": "",
            "full_content": "",
            "chunk_id": total_chunks + 1 if 'total_chunks' in locals() else 1,
            "timestamp": datetime.now().isoformat(),
            "done": True,
            "error": sanitized_error,
            "model": config.OLLAMA_MODEL,
            "error_id": error_info.get("error_id")
        })
        yield f"data: {error_chunk}\n\n"

def handle_streaming_chat(ai_service, conversation_history):
    """
    Handle streaming chat response with enhanced CORS and browser compatibility
    
    Args:
        ai_service: The AI service instance
        conversation_history: The conversation history
        
    Returns:
        Flask streaming response with proper headers for browser compatibility
    """
    return Response(
        generate_streaming_response_with_timeout(ai_service, conversation_history),
        mimetype='text/event-stream',
        headers={
            # Essential SSE headers
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream',
            
            # CORS headers for browser compatibility
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Cache-Control, X-Requested-With',
            'Access-Control-Expose-Headers': 'Content-Type',
            
            # Additional headers for streaming reliability
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Transfer-Encoding': 'chunked'
        }
    )

def generate_streaming_response_with_timeout(ai_service, conversation_history):
    """
    Generate streaming response with timeout handling and graceful degradation
    
    Args:
        ai_service: The AI service instance
        conversation_history: The conversation history
        
    Yields:
        str: Server-Sent Event formatted data chunks with timeout handling
    """
    import json
    import threading
    import queue
    
    # Get streaming timeout from configuration
    STREAMING_TIMEOUT = config.STREAMING_TIMEOUT
    logger.info(f"Using streaming timeout: {STREAMING_TIMEOUT} seconds")
    
    # Use a queue to communicate between threads
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    
    def streaming_worker():
        """Worker function to run streaming in a separate thread"""
        try:
            for chunk in generate_streaming_response(ai_service, conversation_history):
                result_queue.put(chunk)
            result_queue.put(None)  # Signal completion
        except Exception as e:
            exception_queue.put(e)
            result_queue.put(None)
    
    # Start the streaming worker thread
    worker_thread = threading.Thread(target=streaming_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    start_time = time.time()
    
    try:
        while True:
            try:
                # Check for timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > STREAMING_TIMEOUT:
                    raise TimeoutError(f"Streaming timeout after {STREAMING_TIMEOUT} seconds")
                
                # Get chunk with timeout
                remaining_time = STREAMING_TIMEOUT - elapsed_time
                chunk = result_queue.get(timeout=min(remaining_time, 1.0))
                
                if chunk is None:  # Completion signal
                    break
                
                yield chunk
                
            except queue.Empty:
                # Continue checking for timeout
                continue
                
        # Check for exceptions from worker thread
        if not exception_queue.empty():
            raise exception_queue.get()
            
    except TimeoutError as e:
        # Handle streaming timeout with graceful degradation
        logger.warning(f"Streaming timeout occurred: {e}")
        
        # Send timeout notification to client
        timeout_chunk = json.dumps({
            "content": "",
            "full_content": "",
            "chunk_id": 0,
            "timestamp": datetime.now().isoformat(),
            "done": False,
            "error": "streaming_timeout",
            "error_message": "AI processing is taking longer than usual. This is normal for complex requests on slower systems. Switching to standard mode for faster completion...",
            "model": config.OLLAMA_MODEL,
            "timeout_info": {
                "timeout_seconds": STREAMING_TIMEOUT,
                "suggestion": "For faster responses on your system, consider using standard (non-streaming) mode for complex queries"
            }
        })
        yield f"data: {timeout_chunk}\n\n"
        
        # Attempt to get a standard (non-streaming) response as fallback
        try:
            logger.info("Attempting fallback to standard response mode")
            fallback_response = ai_service.chat(conversation_history, stream=False)
            
            # Send the fallback response as a single chunk
            fallback_chunk = json.dumps({
                "content": fallback_response,
                "full_content": fallback_response,
                "chunk_id": 1,
                "timestamp": datetime.now().isoformat(),
                "done": True,
                "model": config.OLLAMA_MODEL,
                "fallback_mode": True,
                "fallback_reason": "streaming_timeout"
            })
            yield f"data: {fallback_chunk}\n\n"
            
        except Exception as fallback_error:
            logger.error(f"Fallback response also failed: {fallback_error}")
            
            # Send final error chunk
            error_chunk = json.dumps({
                "content": "",
                "full_content": "",
                "chunk_id": 1,
                "timestamp": datetime.now().isoformat(),
                "done": True,
                "error": "complete_failure",
                "error_message": "Unable to generate response. Please try again or refresh the page.",
                "model": config.OLLAMA_MODEL
            })
            yield f"data: {error_chunk}\n\n"
            
    except Exception as e:
        # Handle other streaming errors
        logger.error(f"Streaming error: {e}")
        
        error_chunk = json.dumps({
            "content": "",
            "full_content": "",
            "chunk_id": 0,
            "timestamp": datetime.now().isoformat(),
            "done": True,
            "error": "streaming_error",
            "error_message": "An error occurred during streaming. Please try again.",
            "model": config.OLLAMA_MODEL
        })
        yield f"data: {error_chunk}\n\n"

@app.route('/chat_legacy', methods=['POST'])
@security_required(validate_json=True, validate_conversation=True)
def chat_legacy():
    """
    Legacy chat API endpoint for non-streaming requests
    
    Expects JSON payload with conversation history array
    Returns JSON response with AI-generated message
    """
    try:
        # Validate request content type
        if not request.is_json:
            logger.warning("Chat request received without JSON content type")
            return jsonify({
                "error": "Request must be JSON",
                "message": "Content-Type must be application/json"
            }), 400
        
        # Get request data (already validated by security decorator)
        data = request.get_json()
        
        # Validate that data is not None and has conversation key
        if data is None:
            return jsonify({
                "error": "Invalid request data",
                "message": "Request data cannot be null"
            }), 400
        
        if 'conversation' not in data:
            return jsonify({
                "error": "Invalid request data", 
                "message": "Missing 'conversation' field"
            }), 400
        
        # Conversation history has already been validated and sanitized by security decorator
        conversation_history = data['conversation']
        
        # Validate conversation is not empty
        if len(conversation_history) == 0:
            return jsonify({
                "error": "Invalid conversation data",
                "message": "Conversation history cannot be empty"
            }), 400
        
        # Apply conversation history cleanup if needed
        if conversation_manager.should_cleanup(len(conversation_history)):
            original_length = len(conversation_history)
            conversation_history = conversation_manager.cleanup_conversation_history(conversation_history)
            if len(conversation_history) != original_length:
                logger.info(f"Cleaned up conversation history: {original_length} -> {len(conversation_history)} messages")
        
        # Record conversation statistics
        performance_metrics.conversation_stats['total_requests'] += 1
        performance_metrics.conversation_stats['total_messages'] += len(conversation_history)
        
        # Log the incoming request
        logger.info(f"Processing chat request with {len(conversation_history)} messages")
        
        # Get AI service instance
        ai_service = get_ai_service(
            model=config.OLLAMA_MODEL,
            system_prompt=get_current_system_prompt()
        )
        
        # Process conversation with AI
        ai_response = ai_service.chat(conversation_history)
        
        # Return successful response
        response_data = {
            "message": ai_response,
            "timestamp": datetime.now().isoformat(),
            "model": config.OLLAMA_MODEL
        }
        
        logger.info(f"Successfully processed chat request, response length: {len(ai_response)}")
        return jsonify(response_data)
        
    except AIServiceError as e:
        error_handler = get_error_handler()
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "AI service error")
        error_info = error_handler.log_error(
            e,
            ErrorCategory.AI_SERVICE,
            ErrorSeverity.MEDIUM,
            {"conversation_length": len(conversation_history) if 'conversation_history' in locals() else 0}
        )
        # Override user message with sanitized version
        error_info["user_message"] = sanitized_message
        response, status_code = create_error_response(error_info, 503)
        return jsonify(response), status_code
    
    except Exception as e:
        error_handler = get_error_handler()
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Chat processing error")
        error_info = error_handler.log_error(
            e,
            ErrorCategory.UNKNOWN,
            ErrorSeverity.HIGH,
            {"conversation_length": len(conversation_history) if 'conversation_history' in locals() else 0}
        )
        # Override user message with sanitized version
        error_info["user_message"] = sanitized_message
        response, status_code = create_error_response(error_info, 500)
        return jsonify(response), status_code

@app.route('/memory/process', methods=['POST'])
@security_required(validate_json=True, validate_conversation=True)
def process_memory():
    """
    Memory processing endpoint to extract insights from conversation
    
    Expects JSON payload with conversation history array
    Returns JSON response with processing results and insights
    """
    try:
        # Get request data (already validated by security decorator)
        data = request.get_json()
        
        # Validate that data is not None and has conversation key
        if data is None:
            return jsonify({
                "error": "Invalid request data",
                "message": "Request data cannot be null"
            }), 400
        
        if 'conversation' not in data:
            return jsonify({
                "error": "Invalid request data", 
                "message": "Missing 'conversation' field"
            }), 400
        
        # Conversation history has already been validated and sanitized by security decorator
        conversation_history = data['conversation']
        
        # Validate conversation history has sufficient content for insight extraction
        if len(conversation_history) < 2:
            logger.warning("Memory processing request received with insufficient conversation history")
            return jsonify({
                "error": "Insufficient conversation data",
                "message": "At least 2 messages required for insight extraction"
            }), 400
        
        # Log the incoming request
        logger.info(f"Processing memory extraction request with {len(conversation_history)} messages")
        
        # Get memory service instance
        memory_service = get_memory_service(
            model=config.OLLAMA_MODEL,
            memory_file=config.MEMORY_FILE
        )
        
        # Process conversation for memory insights
        processing_result = memory_service.process_conversation(conversation_history)
        
        # Return successful response
        logger.info(f"Successfully processed memory extraction, extracted {processing_result.get('insights_extracted', 0)} insights")
        return jsonify(processing_result)
        
    except MemoryServiceError as e:
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Memory processing error")
        logger.error(f"Memory service error in memory processing endpoint: {e}")
        return jsonify({
            "error": "Memory service error",
            "message": sanitized_message
        }), 503
    
    except Exception as e:
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Memory processing error")
        logger.error(f"Unexpected error in memory processing endpoint: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": sanitized_message
        }), 500

@app.route('/memory/stats')
def memory_stats():
    """
    Memory statistics endpoint to get information about stored insights
    
    Returns JSON response with memory statistics
    """
    try:
        # Get memory service instance
        memory_service = get_memory_service(
            model=config.OLLAMA_MODEL,
            memory_file=config.MEMORY_FILE
        )
        
        # Get memory statistics
        stats = memory_service.get_memory_stats()
        
        logger.info("Successfully retrieved memory statistics")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error retrieving memory statistics: {e}")
        return jsonify({
            "error": "Failed to retrieve memory statistics",
            "message": str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Simple health check endpoint for connection testing"""
    try:
        # Test AI service connection
        ai_status = 'unavailable'
        try:
            ai_service = get_ai_service(
                model=config.OLLAMA_MODEL,
                system_prompt=get_current_system_prompt()
            )
            status_result = ai_service.test_connection()
            ai_status = 'ready' if status_result.get('status') == 'connected' else 'unavailable'
        except Exception as ai_error:
            logger.warning(f"AI service health check failed: {ai_error}")
            ai_status = 'unavailable'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'memory': 'available',
                'ai': ai_status
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/insights')
def get_insights():
    """
    API endpoint to get all insights and conversation data for the dashboard
    
    Returns JSON response with insights, summaries, and statistics
    """
    try:
        # Get memory service instance
        memory_service = get_memory_service(
            model=config.OLLAMA_MODEL,
            memory_file=config.MEMORY_FILE
        )
        
        # Load the complete memory data
        memory_data = memory_service._load_memory_file()
        
        # Get statistics
        stats = memory_service.get_memory_stats()
        
        # Prepare response data
        response_data = {
            'insights': memory_data.get('insights', []),
            'conversation_summaries': memory_data.get('conversation_summaries', []),
            'metadata': memory_data.get('metadata', {}),
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Successfully retrieved {len(response_data['insights'])} insights for dashboard")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error retrieving insights for dashboard: {e}")
        return jsonify({
            "error": "Failed to retrieve insights",
            "message": str(e)
        }), 500

@app.route('/api/serendipity', methods=['GET', 'HEAD', 'POST'])
def discover_serendipity():
    """
    Serendipity engine endpoint to discover unexpected connections in memory data
    
    Returns JSON response with discovered connections and patterns
    """
    try:
        # Handle HEAD requests for availability check
        if request.method == 'HEAD':
            return '', 200
        
        # Handle GET requests for basic status
        if request.method == 'GET':
            return jsonify({
                'status': 'available',
                'endpoint': '/api/serendipity',
                'methods': ['GET', 'HEAD', 'POST'],
                'description': 'Serendipity engine for discovering unexpected connections'
            })
        
        # For POST requests, validate JSON
        if request.method == 'POST':
            if not request.is_json:
                return jsonify({
                    "error": "Invalid request format",
                    "message": "Request must be JSON"
                }), 400
        
        logger.info("Processing serendipity discovery request")
        
        # Get serendipity service instance
        serendipity_service = get_serendipity_service(
            model=config.OLLAMA_MODEL,
            memory_file=config.MEMORY_FILE
        )
        
        # Analyze memory for connections
        connections_data = serendipity_service.analyze_memory()
        
        # Return successful response
        logger.info(f"Successfully discovered {len(connections_data.get('connections', []))} connections")
        return jsonify(connections_data)
        
    except SerendipityServiceError as e:
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Serendipity analysis error")
        logger.error(f"Serendipity service error: {e}")
        return jsonify({
            "error": "Serendipity analysis error",
            "message": sanitized_message,
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Unable to analyze connections at this time.",
            "recommendations": ["Please try again later or ensure you have sufficient conversation history."]
        }), 503
    
    except Exception as e:
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Serendipity analysis error")
        logger.error(f"Unexpected error in serendipity endpoint: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": sanitized_message,
            "connections": [],
            "meta_patterns": [],
            "serendipity_summary": "Analysis temporarily unavailable.",
            "recommendations": ["Please try again later."]
        }), 500

@app.route('/api/prompt/current')
def get_current_prompt():
    """
    Get the current system prompt
    
    Returns JSON response with current prompt and metadata
    """
    try:
        prompt_service = get_prompt_service()
        current_prompt = prompt_service.get_current_prompt()
        stats = prompt_service.get_prompt_stats()
        
        return jsonify({
            "prompt": current_prompt,
            "length": len(current_prompt),
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving current prompt: {e}")
        return jsonify({
            "error": "Failed to retrieve current prompt",
            "message": str(e)
        }), 500

@app.route('/api/prompt/update', methods=['POST'])
@security_required(validate_json=True)
def update_prompt():
    """
    Update the system prompt
    
    Expects JSON payload with 'prompt' and optional 'name' fields
    Returns JSON response with update result
    """
    try:
        # Get request data (already validated by security decorator)
        data = request.get_json()
        
        if 'prompt' not in data:
            return jsonify({
                "error": "Missing prompt field",
                "message": "Request must include 'prompt' field"
            }), 400
        
        # Validate and sanitize prompt content
        is_valid, result = InputValidator.validate_prompt_content(data['prompt'])
        if not is_valid:
            return jsonify({
                "error": "Invalid prompt content",
                "message": result
            }), 400
        
        new_prompt = result
        prompt_name = data.get('name')
        
        # Get prompt service and update prompt
        prompt_service = get_prompt_service()
        result = prompt_service.update_prompt(new_prompt, prompt_name)
        
        # Update the AI service with the new prompt
        ai_service = get_ai_service()
        ai_service.update_system_prompt(new_prompt)
        
        logger.info(f"Successfully updated system prompt: {result['prompt_name']}")
        return jsonify(result)
        
    except PromptServiceError as e:
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Prompt update error")
        logger.error(f"Prompt service error: {e}")
        return jsonify({
            "error": "Prompt update failed",
            "message": sanitized_message
        }), 400
    
    except Exception as e:
        # Sanitize error message for security
        sanitized_message = sanitize_error_for_user(e, "Prompt update error")
        logger.error(f"Unexpected error updating prompt: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": sanitized_message
        }), 500

@app.route('/api/prompt/validate', methods=['POST'])
@security_required(validate_json=True)
def validate_prompt():
    """
    Validate a system prompt
    
    Expects JSON payload with 'prompt' field
    Returns JSON response with validation result
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "error": "Empty request data",
                "message": "Request body cannot be empty"
            }), 400
        
        if 'prompt' not in data:
            return jsonify({
                "error": "Missing prompt field",
                "message": "Request must include 'prompt' field"
            }), 400
        
        prompt = data['prompt']
        
        # Get prompt service and validate prompt
        prompt_service = get_prompt_service()
        validation_result = prompt_service.validate_prompt(prompt)
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        return jsonify({
            "valid": False,
            "error": f"Validation failed: {str(e)}"
        }), 500

@app.route('/api/prompt/test', methods=['POST'])
@security_required(validate_json=True)
def test_prompt():
    """
    Test a system prompt with a sample message
    
    Expects JSON payload with 'prompt' and optional 'test_message' fields
    Returns JSON response with test result
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "error": "Empty request data",
                "message": "Request body cannot be empty"
            }), 400
        
        if 'prompt' not in data:
            return jsonify({
                "error": "Missing prompt field",
                "message": "Request must include 'prompt' field"
            }), 400
        
        prompt = data['prompt']
        test_message = data.get('test_message', "Hello, how are you?")
        
        # Get prompt service and test prompt
        prompt_service = get_prompt_service()
        test_result = prompt_service.test_prompt(prompt, test_message)
        
        logger.info(f"Successfully tested prompt, response length: {test_result['response_length']}")
        return jsonify(test_result)
        
    except PromptServiceError as e:
        logger.error(f"Prompt service error during test: {e}")
        return jsonify({
            "error": "Prompt test failed",
            "message": str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error testing prompt: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred while testing the prompt"
        }), 500

@app.route('/api/prompt/history')
def get_prompt_history():
    """
    Get the history of all system prompts
    
    Returns JSON response with prompt history
    """
    try:
        prompt_service = get_prompt_service()
        history = prompt_service.get_prompt_history()
        stats = prompt_service.get_prompt_stats()
        
        return jsonify({
            "history": history,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving prompt history: {e}")
        return jsonify({
            "error": "Failed to retrieve prompt history",
            "message": str(e)
        }), 500

@app.route('/api/prompt/restore', methods=['POST'])
@security_required(validate_json=True)
def restore_prompt():
    """
    Restore a prompt from history as the current prompt
    
    Expects JSON payload with 'index' field
    Returns JSON response with restore result
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "error": "Empty request data",
                "message": "Request body cannot be empty"
            }), 400
        
        if 'index' not in data:
            return jsonify({
                "error": "Missing index field",
                "message": "Request must include 'index' field"
            }), 400
        
        prompt_index = data['index']
        
        if not isinstance(prompt_index, int):
            return jsonify({
                "error": "Invalid index type",
                "message": "Index must be an integer"
            }), 400
        
        # Get prompt service and restore prompt
        prompt_service = get_prompt_service()
        result = prompt_service.restore_prompt(prompt_index)
        
        # Update the AI service with the restored prompt
        restored_prompt = prompt_service.get_current_prompt()
        ai_service = get_ai_service()
        ai_service.update_system_prompt(restored_prompt)
        
        logger.info(f"Successfully restored prompt: {result['prompt_name']}")
        return jsonify(result)
        
    except PromptServiceError as e:
        logger.error(f"Prompt service error during restore: {e}")
        return jsonify({
            "error": "Prompt restore failed",
            "message": str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error restoring prompt: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred while restoring the prompt"
        }), 500

@app.route('/api/errors/stats')
def get_error_stats():
    """
    Get error statistics and recent error information
    
    Returns JSON response with error statistics
    """
    try:
        error_handler = get_error_handler()
        stats = error_handler.get_error_stats()
        
        return jsonify({
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving error statistics: {e}")
        return jsonify({
            "error": "Failed to retrieve error statistics",
            "message": str(e)
        }), 500

@app.route('/api/errors/clear', methods=['POST'])
def clear_error_stats():
    """
    Clear error statistics (useful for testing or maintenance)
    
    Returns JSON response with clear result
    """
    try:
        error_handler = get_error_handler()
        error_handler.clear_error_stats()
        
        logger.info("Error statistics cleared")
        return jsonify({
            "success": True,
            "message": "Error statistics cleared successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing error statistics: {e}")
        return jsonify({
            "error": "Failed to clear error statistics",
            "message": str(e)
        }), 500

@app.route('/api/performance/status')
def get_performance_status_endpoint():
    """
    Get comprehensive performance status and metrics
    
    Returns JSON response with performance data
    """
    try:
        # Record current memory usage
        performance_metrics.record_memory_usage()
        
        # Get comprehensive performance status
        status = get_performance_status()
        
        return jsonify({
            "success": True,
            "performance": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving performance status: {e}")
        return jsonify({
            "error": "Failed to retrieve performance status",
            "message": str(e)
        }), 500

@app.route('/api/performance/cleanup', methods=['POST'])
def trigger_performance_cleanup():
    """
    Trigger manual performance cleanup
    
    Returns JSON response with cleanup results
    """
    try:
        # Perform system cleanup
        cleanup_system_resources()
        
        # Get updated performance status
        status = get_performance_status()
        
        logger.info("Manual performance cleanup completed")
        return jsonify({
            "success": True,
            "message": "Performance cleanup completed successfully",
            "performance": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error during performance cleanup: {e}")
        return jsonify({
            "error": "Failed to perform performance cleanup",
            "message": str(e)
        }), 500

@app.route('/api/performance/conversation/cleanup', methods=['POST'])
@security_required(validate_json=True, validate_conversation=True)
def cleanup_conversation_endpoint():
    """
    Clean up conversation history based on request data
    
    Expects JSON payload with 'conversation' field
    Returns JSON response with cleaned conversation
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "error": "Empty request data",
                "message": "Request body cannot be empty"
            }), 400
        
        if 'conversation' not in data:
            return jsonify({
                "error": "Missing conversation field",
                "message": "Request must include 'conversation' field"
            }), 400
        
        conversation_history = data['conversation']
        
        if not isinstance(conversation_history, list):
            return jsonify({
                "error": "Invalid conversation format",
                "message": "Conversation must be an array"
            }), 400
        
        # Clean up conversation history
        original_length = len(conversation_history)
        cleaned_history = conversation_manager.cleanup_conversation_history(conversation_history)
        
        # Get conversation statistics
        stats = conversation_manager.get_conversation_stats(cleaned_history)
        
        logger.info(f"Conversation cleanup: {original_length} -> {len(cleaned_history)} messages")
        
        return jsonify({
            "success": True,
            "original_length": original_length,
            "cleaned_length": len(cleaned_history),
            "conversation": cleaned_history,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error during conversation cleanup: {e}")
        return jsonify({
            "error": "Failed to clean up conversation",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Ensure templates and static directories exist
    os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
    os.makedirs(config.STATIC_DIR, exist_ok=True)
    
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        logger.warning("Configuration issues detected:")
        for issue in config_issues:
            logger.warning(f"  - {issue}")
    
    # Start the Flask application
    logger.info(f"Starting Synapse AI Web Application")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info(f"AI Model: {config.OLLAMA_MODEL}")
    logger.info(f"Memory File: {config.MEMORY_FILE}")
    
    # Ensure static directories exist
    os.makedirs('static/images', exist_ok=True)
    
    # Run the application
    app.run(
        host=os.environ.get('FLASK_RUN_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_RUN_PORT', '5000')),
        debug=getattr(config, 'DEBUG', False)
    )