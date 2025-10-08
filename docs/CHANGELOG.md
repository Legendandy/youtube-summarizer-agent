# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-08

### Added
- Initial release of YouTube Summarizer Agent
- AI-powered video summarization with timestamps
- Support for English captions
- Real-time streaming responses via SSE
- File-based caching system (7-day TTL)
- Comprehensive security validation
- Rate limiting (per-user and platform-wide)
- Webshare proxy integration for transcript extraction
- Interactive greeting responses
- Detailed error messages with troubleshooting guidance
- Support for multiple YouTube URL formats
- Configuration via environment variables
- Structured project architecture with separation of concerns

### Security
- SQL injection protection
- Command injection prevention
- XSS attack mitigation
- Path traversal blocking
- DoS protection via input length limits
- Rate limiting to prevent abuse

### Documentation
- Comprehensive README with installation guide
- API usage examples (cURL and Sentient Agent Client)
- Security policy
- Contributing guidelines
- MIT License

---

## [Unreleased]

### Planned Features
- Multi-language support (Spanish, French, German)
- Custom summary lengths (short, medium, detailed)
- PDF/Markdown export
- Support for other video platforms (Vimeo, TikTok)
- Topic categorization and tagging
- Sentiment analysis
- Key quote extraction
- Redis caching option
- Webhook notifications

---