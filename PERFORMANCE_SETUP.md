# Synapse AI Performance Setup Guide

This guide helps you optimize Synapse AI for your system's performance capabilities.

## Quick Setup (Recommended)

Run the automatic system detection script:

```bash
python detect_system_performance.py
```

This script will:
- Detect your system's CPU cores and memory
- Classify your system performance level (low/medium/high)
- Recommend optimal timeout settings
- Optionally create/update your `.env` file with optimized settings

## Manual Configuration

If you prefer manual configuration, copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and adjust the timeout values based on your system:

### Low-End Systems (≤2 cores, ≤2GB RAM)
```env
RESPONSE_TIMEOUT=120
STREAMING_TIMEOUT=300
OLLAMA_TIMEOUT=60
```

### Medium Systems (4 cores, 4-8GB RAM)
```env
RESPONSE_TIMEOUT=60
STREAMING_TIMEOUT=180
OLLAMA_TIMEOUT=30
```

### High-End Systems (≥8 cores, ≥8GB RAM)
```env
RESPONSE_TIMEOUT=30
STREAMING_TIMEOUT=90
OLLAMA_TIMEOUT=15
```

## Understanding Timeout Settings

- **RESPONSE_TIMEOUT**: Maximum time to wait for regular (non-streaming) responses
- **STREAMING_TIMEOUT**: Maximum time to wait for streaming responses (usually longer)
- **OLLAMA_TIMEOUT**: Maximum time to wait for the Ollama AI service to respond

## Performance Levels Explained

### Low-End Systems
- **Characteristics**: ≤2 CPU cores or ≤2GB RAM
- **Behavior**: AI processing takes longer, needs patience
- **Timeouts**: Conservative (up to 5 minutes for complex requests)
- **Tips**: 
  - Use shorter, simpler questions
  - Close other applications while using Synapse
  - Consider standard (non-streaming) mode for complex queries

### Medium Systems
- **Characteristics**: 4 CPU cores, 4-8GB RAM
- **Behavior**: Good balance of speed and capability
- **Timeouts**: Balanced (up to 3 minutes for complex requests)
- **Tips**: 
  - Streaming mode works well for most queries
  - Can handle moderately complex conversations

### High-End Systems
- **Characteristics**: ≥8 CPU cores and ≥8GB RAM
- **Behavior**: Fast AI processing, real-time responses
- **Timeouts**: Optimized (up to 1.5 minutes for complex requests)
- **Tips**: 
  - Full streaming experience with minimal delays
  - Can handle complex, multi-part conversations
  - Consider running multiple AI models

## Troubleshooting

### "AI is taking longer than expected" Errors

1. **Check your system performance level**:
   ```bash
   python detect_system_performance.py
   ```

2. **Increase timeout values** in your `.env` file:
   ```env
   STREAMING_TIMEOUT=300  # 5 minutes
   ```

3. **Restart Synapse AI** after changing configuration

### Slow Response Times

1. **Close other applications** to free up system resources
2. **Use shorter questions** for faster responses
3. **Switch to standard mode** instead of streaming for complex queries
4. **Check Ollama service** is running properly

### Frequent Timeouts

1. **Increase all timeout values** by 50-100%
2. **Check system resources** (CPU, memory usage)
3. **Verify Ollama model** is properly installed and accessible
4. **Consider using a smaller AI model** (e.g., llama3:8b instead of larger models)

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMING_TIMEOUT` | 180 | Streaming response timeout (seconds) |
| `RESPONSE_TIMEOUT` | 60 | Regular response timeout (seconds) |
| `OLLAMA_TIMEOUT` | 30 | Ollama service timeout (seconds) |
| `OLLAMA_MODEL` | llama3:8b | AI model to use |
| `MAX_CONVERSATION_LENGTH` | 100 | Maximum conversation history |

## Performance Monitoring

Synapse AI includes built-in performance monitoring that:
- Automatically detects your system capabilities
- Adjusts timeouts based on actual performance
- Shows helpful progress messages during long processing
- Provides system-specific error messages and suggestions

The system will learn your hardware's capabilities over time and optimize accordingly.

## Getting Help

If you continue to experience timeout issues:

1. Check the Synapse error logs: `synapse_errors.log`
2. Verify Ollama is running: `ollama list`
3. Test with a simple question first
4. Consider using a smaller AI model for better performance

For more help, check the main documentation or create an issue with your system specifications and error details.