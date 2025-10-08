# Frequently Asked Questions

## General

### Q: What is YouTube Summarizer Agent?
**A:** An AI agent that automatically generates detailed, timestamped summaries of YouTube videos using the Sentient Agent Framework.

### Q: Is it free to use?
**A:** The agent is open source (MIT license), but you need:
- OpenRouter API key (some free models available)
- Webshare proxy subscription (optional but recommended)

### Q: What languages are supported?
**A:** Currently only English captions/subtitles. Multi-language support is planned.

---

## Usage

### Q: How do I summarize a YouTube video?
**A:** Send a query containing the YouTube URL:
```bash
curl -N --location 'http://localhost:8000/assist' \
  --header 'Content-Type: application/json' \
  --data '{"query": {"id": "...", "prompt": "https://youtu.be/..."}, "session": {...}}'
```

### Q: Can I use shortened YouTube URLs?
**A:** Yes! Supported formats:
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/embed/VIDEO_ID`

### Q: How long does summarization take?
**A:** Typically 30-60 seconds depending on video length. Cached results are instant.

### Q: What if the video doesn't have captions?
**A:** The agent will return an error. The video must have English captions/subtitles.

---

## Technical

### Q: Why am I getting "Rate limit exceeded"?
**A:** You've hit the limit of:
- 10 requests per minute, OR
- 50 requests per hour

Wait for the cooldown period (shown in error message).

### Q: Can I change the AI model?
**A:** Yes! Edit `config/fireworks_config.py` and change the `MODEL` variable to any OpenRouter-supported model.

### Q: How does caching work?
**A:** Summaries are cached for 7 days using the video ID as the key. Subsequent requests for the same video return instantly.

### Q: Can I disable caching?
**A:** Not recommended, but you can set `ttl_hours=0` in `agent.py` or delete `.cache/` directory.

---

## Troubleshooting

### Q: "FIREWORKS_API_KEY environment variable is required"
**A:** Create a `.env` file in the project root with:
```
FIREWORKS_API_KEY=your_key_here
```

### Q: Agent hangs on transcript extraction
**A:** Possible causes:
- Network timeout (increase timeout in `config/youtube_config.py`)
- Proxy issues (verify Webshare credentials)
- Video restrictions

### Q: Getting "Connection refused" errors
**A:** Ensure the agent is running: `python main.py`

### Q: Cache not working
**A:** Check:
- `.cache/` directory exists and is writable
- Disk space available
- No permission issues

---

## Security

### Q: Is my data safe?
**A:** Yes:
- No sensitive data is logged
- Summaries stored locally in `.cache/`
- Input validation prevents injection attacks

### Q: Should I expose the API publicly?
**A:** Only with:
- HTTPS enabled
- Firewall rules
- Rate limiting (already included)
- Authentication (not included - add if needed)

### Q: How do I report security issues?
**A:** Email security@yourdomain.com (see SECURITY.md)

---

## Contributing

### Q: How can I contribute?
**A:** See CONTRIBUTING.md for guidelines. We welcome:
- Bug fixes
- New features
- Documentation improvements
- Test coverage

### Q: I found a bug. What should I do?
**A:** Open a GitHub issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details

---

## Roadmap

### Q: Will you support other languages?
**A:** Yes! Spanish, French, and German support is planned for v1.1.0.

### Q: Can it summarize other video platforms?
**A:** Not yet, but Vimeo and TikTok support is on the roadmap.

### Q: Will there be a web interface?
**A:** A simple web UI is planned for v2.0.0.

---

## Contact

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: your.email@example.com

---

# .github/ISSUE_TEMPLATE/bug_report.md

---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. Send query '....'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Actual behavior**
What actually happened.

**Error messages**
```
Paste any error messages here
```

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python version: [e.g. 3.12.1]
 - Agent version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.

---

# .github/ISSUE_TEMPLATE/feature_request.md

---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.

**Would you be willing to contribute this feature?**
- [ ] Yes, I can submit a PR
- [ ] No, but I can help test
- [ ] No, just suggesting