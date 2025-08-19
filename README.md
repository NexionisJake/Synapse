# Synapse AI - Cognitive Partner

A private, local-first AI cognitive partner designed to help users clarify their thinking through Socratic questioning and thoughtful conversation. Built with adaptive performance optimization for systems of all capabilities.

## 🧠 What is Synapse?

Synapse is not just another AI assistant. It's a **Cognitive Partner** that:

- **Facilitates self-discovery** through Socratic questioning rather than providing direct answers
- **Adapts to your thinking style** and helps you explore ideas more deeply
- **Maintains intellectual honesty** by challenging assumptions respectfully
- **Operates locally** for complete privacy and control
- **Automatically optimizes** for your system's performance capabilities

## ✨ Key Features

### 🎯 Cognitive Partnership
- **Socratic Method**: Asks better questions rather than giving direct answers
- **Intellectual Rigor**: Challenges assumptions while remaining supportive
- **Contextual Memory**: Remembers and builds upon previous conversations
- **Adaptive Questioning**: Tailors approach based on your thinking patterns

### 🚀 Performance Optimization
- **Automatic System Detection**: Detects CPU, memory, and connection capabilities
- **Adaptive Timeouts**: Adjusts response times based on your hardware
- **Smart Error Handling**: Provides helpful feedback during longer processing
- **Progressive Loading**: Shows meaningful progress during AI processing

### 🔒 Privacy & Control
- **Local-First**: All processing happens on your machine
- **No Data Collection**: Your conversations stay completely private
- **Offline Capable**: Works without internet (after initial setup)
- **Full Control**: You own your data and AI interactions

### 🎨 Modern Interface
- **Glassmorphism Design**: Beautiful, modern HUD-style interface
- **Real-time Streaming**: Live response generation with typewriter effects
- **Cognitive Charts**: Visual insights into your thinking patterns
- **Responsive Design**: Works on desktop, tablet, and mobile

## 🛠 Quick Setup

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- 4GB+ RAM recommended (2GB minimum)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd synapse-project
   ```

2. **Run automatic system detection** (recommended):
   ```bash
   python detect_system_performance.py
   ```
   This will detect your system capabilities and configure optimal settings.

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install AI model**:
   ```bash
   ollama pull llama3:8b
   ```

5. **Start Synapse**:
   ```bash
   ./start_synapse.sh
   ```

6. **Open your browser** to `http://localhost:5000`

### Manual Configuration

If you prefer manual setup, copy the example environment file:
```bash
cp .env.example .env
```

Then edit `.env` with your preferred settings. See [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md) for detailed configuration options.

## 📊 System Performance Levels

Synapse automatically detects and optimizes for your system:

| System Type | Specs | Timeout Settings | Experience |
|-------------|-------|------------------|------------|
| **Low-end** | ≤2 cores, ≤2GB RAM | Up to 5 minutes | Patient, helpful feedback |
| **Medium** | 4 cores, 4-8GB RAM | Up to 3 minutes | Balanced performance |
| **High-end** | ≥8 cores, ≥8GB RAM | Up to 1.5 minutes | Real-time responses |

## 🎯 How to Use Synapse

### Starting a Conversation
Instead of asking direct questions, try sharing your thoughts:
- "I'm thinking about changing careers but I'm not sure..."
- "I have this idea for a project, but something feels off..."
- "I'm trying to understand why I keep procrastinating..."

### What to Expect
Synapse will:
- Ask clarifying questions about your situation
- Help you explore different perspectives
- Challenge assumptions gently
- Guide you toward your own insights
- Remember context from previous conversations

### Example Interaction
**You**: "I want to start a business but I don't know what kind."

**Synapse**: "What draws you to the idea of starting a business in the first place? Is it the independence, the creative control, solving a particular problem you've noticed, or something else entirely?"

## 📁 Project Structure

```
synapse-project/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── ai_service.py                   # AI communication layer
├── memory_service.py               # Conversation memory
├── prompt_service.py               # Prompt management
├── detect_system_performance.py    # System optimization
├── static/
│   ├── css/style.css              # Glassmorphism UI styles
│   └── js/
│       ├── chat.js                # Chat interface
│       ├── streaming-performance-monitor.js
│       └── cognitive-charts.js    # Thinking pattern visualization
├── templates/                      # HTML templates
├── PERFORMANCE_SETUP.md           # Performance optimization guide
└── .env.example                   # Configuration template
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMING_TIMEOUT` | 180 | Streaming response timeout (seconds) |
| `RESPONSE_TIMEOUT` | 60 | Regular response timeout (seconds) |
| `OLLAMA_MODEL` | llama3:8b | AI model to use |
| `MAX_CONVERSATION_LENGTH` | 100 | Maximum conversation history |

### Performance Tuning

For optimal performance on your system:

1. **Run system detection**: `python detect_system_performance.py`
2. **Monitor performance**: Check the system indicator in the bottom-left
3. **Adjust timeouts**: Edit `.env` file if needed
4. **Restart**: `./start_synapse.sh` to apply changes

## 🚨 Troubleshooting

### Common Issues

**"AI taking longer than expected" errors**:
1. Run `python detect_system_performance.py`
2. Increase timeout values in `.env`
3. Restart Synapse

**Slow responses**:
1. Close other applications
2. Use shorter questions
3. Switch to standard (non-streaming) mode

**Connection errors**:
1. Verify Ollama is running: `ollama list`
2. Check model is installed: `ollama pull llama3:8b`
3. Restart Ollama service

See [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md) for detailed troubleshooting.

## 🤝 Contributing

This is a private repository, but contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is private and proprietary. All rights reserved.

## 🙏 Acknowledgments

- Built with [Ollama](https://ollama.ai) for local AI processing
- Uses [Flask](https://flask.palletsprojects.com/) for the web framework
- Inspired by Socratic questioning methodology
- Designed for privacy-conscious users who value thoughtful AI interaction

---

**Synapse AI** - Your private cognitive partner for deeper thinking and self-discovery.