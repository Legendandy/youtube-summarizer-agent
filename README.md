<div align="center">

# YouTube Summarizer Agent 🎥✨

A powerful AI agent built with the [Sentient Agent Framework](https://github.com/sentient-agi/Sentient-Agent-Framework) that automatically generates detailed, timestamped summaries of YouTube videos.



[![GitHub Stars](https://img.shields.io/github/stars/Legendandy/youtube-summarizer-agent.svg?style=flat&logo=github)](https://github.com/Legendandy/youtube-summarizer-agent/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/Legendandy/youtube-summarizer-agent.svg)](https://github.com/Legendandy/youtube-summarizer-agent/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## Features

- 🎯 **Intelligent Summarization**: Creates structured summaries with general overviews and timestamped section breakdowns
- ⚡ **Real-time Streaming**: Streams responses as they're generated for immediate feedback
- 💾 **Smart Caching**: Stores summaries for 7 days to provide instant responses for repeated queries
- 🔒 **Security Validated**: Protects against SQL injection, command injection, XSS, and other attacks
- 🚦 **Rate Limiting**: Fair usage enforcement with per-user and platform-wide limits
- 🌐 **Proxy Support**: Uses Webshare rotating proxies for reliable transcript extraction
- 📝 **English Captions Only**: Currently supports videos with English captions/subtitles

## Architecture

```
youtube-summarizer-agent/
├── src/
│   └── youtube_summarizer_agent/
│       ├── __init__.py              # Package initialization
│       ├── agent.py                 # Main agent orchestration
│       ├── utils.py                 # URL parsing utilities
│       ├── transcript_service.py    # YouTube transcript extraction
│       ├── summarizer_service.py    # AI-powered summarization
│       └── response_generator.py    # Response formatting & streaming
├── utils/
│   ├── cache.py                     # File-based caching system
│   ├── security.py                  # Input validation & security
│   └── rate_limiter.py              # Rate limiting logic
├── config/
│   ├── openrouter_config.py          # AI model configuration
│   └── youtube_config.py            # YouTube API configuration
├── main.py                          # Application entry point
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
└── pyproject.toml                   # Project metadata

```

## Installation

### Prerequisites

- Python 3.12 or higher
- OpenRouter API key (for AI summarization)
- Webshare.io rotating proxy credentials (for transcript extraction)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Legendandy/youtube-summarizer-agent.git
cd youtube-summarizer-agent
```

### Step 2: Set Up Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# OpenRouter API Key (get from https://openrouter.ai/)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Webshare Proxy Credentials (get from https://webshare.io/)
YOUTUBE_PROXY_USERNAME=your_proxy_username
YOUTUBE_PROXY_PASSWORD=your_proxy_password
```

### Step 5: Run the Agent

```bash
python main.py
```

You should see output like:

```
============================================================
🚀 Starting YouTube Summarizer Agent
============================================================
📝 Language Support: English captions only
🔥 AI Provider: Openrouter AI
🤖 Model: z-ai/glm-4.5-air:free
💾 Cache: Enabled (7 day TTL)
🔒 Security: Input validation enabled
⏱️  Rate Limiting (Video Summarization Only):
   - 10 requests/minute per user
   - 50 requests/hour per user
   - No cooldown between requests
   - 200 max concurrent queries platform-wide
🎯 Status: Ready to process YouTube URLs
📡 Server: Running with streaming support
============================================================
```

## Usage

### Option 1: Using cURL

The agent exposes a RESTful API endpoint at `http://localhost:8000/assist`.

**Basic Request:**

```bash
curl -N --location 'http://localhost:8000/assist' \
  --header 'Content-Type: application/json' \
  --data '{
    "query": {
        "id": "01K6YDCXXV62EJV0KAP7JEGCGP",
        "prompt": "Can you summarize this video https://youtu.be/dQw4w9WgXcQ"
    },
    "session": {
        "processor_id": "YouTube Summarizer",
        "activity_id": "01JR8SXE9B92YDKKNMYHYFZY1T",
        "request_id": "01JR8SY5PHB9X2FET1QRXGZW76",
        "interactions": []
    }
}'
```

**Request Fields:**
- `query.id`: Unique identifier for the query (ULID format recommended)
- `query.prompt`: Your message containing the YouTube URL
- `session.processor_id`: Must be `"YouTube Summarizer"`
- `session.activity_id`: Activity identifier (ULID format)
- `session.request_id`: Request identifier (ULID format)
- `session.interactions`: Array of previous interactions (empty for new sessions)

**Example Queries:**

1. **Summarize a video:**
```bash
curl -N --location 'http://localhost:8000/assist' \
  --header 'Content-Type: application/json' \
  --data '{
    "query": {
        "id": "01K6YDCXXV62EJV0KAP7JEGCGP",
        "prompt": "https://youtu.be/dQw4w9WgXcQ"
    },
    "session": {
        "processor_id": "YouTube Summarizer",
        "activity_id": "01JR8SXE9B92YDKKNMYHYFZY1T",
        "request_id": "01JR8SY5PHB9X2FET1QRXGZW76",
        "interactions": []
    }
}'
```

2. **Ask about agent capabilities:**
```bash
curl -N --location 'http://localhost:8000/assist' \
  --header 'Content-Type: application/json' \
  --data '{
    "query": {
        "id": "01K6YDCXXV62EJV0KAP7JEGCGP",
        "prompt": "who are you"
    },
    "session": {
        "processor_id": "YouTube Summarizer",
        "activity_id": "01JR8SXE9B92YDKKNMYHYFZY1T",
        "request_id": "01JR8SY5PHB9X2FET1QRXGZW76",
        "interactions": []
    }
}'
```

3. **Response Format with cURL:**

The agent uses Server-Sent Events (SSE) to stream responses in real-time:

```
data: {"type": "text_block", "id": "STATUS", "text": "Thinking about your query..."}

data: {"type": "text_chunk", "id": "FINAL_RESPONSE", "text": "# YouTube"}

data: {"type": "text_chunk", "id": "FINAL_RESPONSE", "text": " Video Summary"}

data: {"type": "done"}
```

### Option 2: Using Sentient Agent Client

Clone the repository:

```bash
git clone https://github.com/sentient-agi/Sentient-Agent-Client.git
cd Sentient-Agent-Client
```

Create Python virtual environment
```
python3 -m venv .venv
```

Activate Python virtual environment
```
source .venv/bin/activate
```

Install the dependencies
```bash
pip install -r requirements.txt
```

Run the client with your agent's URL
```bash
python3 -m src.sentient_agent_client --url http://0.0.0.0:8000/assist
```

Follow the instructions and query away!

```
Enter your message: can you summarize this youtube video https://youtu.be/dQw4w9WgXcQ
```

## Summary Format

The agent generates structured summaries with:

### General Summary
A 2-3 paragraph overview covering:
- Main topic and subject
- Key items or concepts presented
- Important demonstrations or examples
- Creator's perspective and tone
- Notable features or details

### Section Breakdown
4-8 timestamped sections with:
- Descriptive subheadings (not generic names like "Introduction")
- Timestamp ranges: `[MM:SS] - [MM:SS]`
- 4+ sentence summaries of each section
- Specific details and examples mentioned
- Chronological order maintained

## Rate Limits

**Per User:**
- 10 requests per minute
- 50 requests per hour
- 5 minute block for violations

**Platform-Wide:**
- 200 concurrent queries maximum

**Note:** Greetings and identity questions are NOT rate-limited.

## Cache System

- **Storage**: File-based caching in `.cache/` directory
- **TTL**: 7 days (168 hours)
- **Key**: SHA-256 hash of video ID
- **Benefits**: Instant responses for repeated queries, reduced API costs

## Security Features

Protects against:
- ✅ SQL injection attacks
- ✅ Command injection attempts
- ✅ XSS and script injection
- ✅ Path traversal attacks
- ✅ DoS via excessive length
- ✅ Null byte injection

## Configuration

### AI Model Settings

Edit `config/openrouter_config.py`:

```python
MODEL = "z-ai/glm-4.5-air:free"  # Change model
MAX_TOKENS = 2048                 # Adjust max length
TEMPERATURE = 0.3                 # Control randomness (0-1)
```

### Rate Limiting

Edit `src/youtube_summarizer_agent/agent.py`:

```python
self.rate_limiter = RateLimiter(
    requests_per_minute=10,      # Adjust per-minute limit
    requests_per_hour=50,        # Adjust per-hour limit
    max_concurrent_platform=200  # Platform-wide limit
)
```

### Cache Duration

Edit `src/youtube_summarizer_agent/agent.py`:

```python
self.cache_manager = CacheManager(
    cache_dir=".cache",
    ttl_hours=168  # Change cache duration
)
```

## Troubleshooting

### "OPENROUTER_API_KEY environment variable is required"
- Ensure `.env` file exists in project root
- Add your OpenRouter API key: `OPENROUTER_API_KEY=sk-...`

### "No English captions available for this video"
- Video doesn't have English subtitles/captions
- Try a different video or wait for auto-captions to be generated

### "Rate limit exceeded"
- You've exceeded per-minute or per-hour limits
- Wait for the specified time before retrying

### "Connection timeout while fetching transcript"
- Network issues or proxy problems
- Check your internet connection
- Verify Webshare proxy credentials

### Agent not responding
- Ensure agent is running: `python main.py`
- Check if port 8000 is available
- Try restarting the agent

## Development

### Project Structure

- **src/youtube_summarizer_agent/**: Core agent logic
  - `agent.py`: Main orchestration and request handling
  - `transcript_service.py`: YouTube transcript extraction
  - `summarizer_service.py`: AI summarization logic
  - `response_generator.py`: Response formatting
  - `utils.py`: URL parsing utilities

- **utils/**: Shared utilities
  - `cache.py`: Caching system
  - `security.py`: Security validation
  - `rate_limiter.py`: Rate limiting logic

- **config/**: Configuration modules
  - `openrouter_config.py`: AI model settings
  - `youtube_config.py`: YouTube API settings

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Adding New Features

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature-name`
7. Open a Pull Request

## Roadmap

- [ ] Multi-language support (Spanish, French, German, etc.)
- [ ] Custom summary lengths (short, medium, detailed)
- [ ] Export summaries to PDF/Markdown
- [ ] Support for other video platforms (Vimeo, TikTok)
- [ ] Topic categorization and tagging
- [ ] Sentiment analysis
- [ ] Key quote extraction

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](docs/CONTRIBUTING.md) before submitting PRs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Sentient Agent Framework](https://github.com/sentient-agi/Sentient-Agent-Framework)
- Powered by [OpenRouter](https://openrouter.ai/)
- Transcript extraction via [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)

## Support

- **Issues**: [GitHub Issues](https://github.com/Legendandy/youtube-summarizer-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Legendandy/youtube-summarizer-agent/discussions)
- **Email**: olasanmiayoola@gmail.com

---

**Built for the Sentient AI Builder Program** 🚀
