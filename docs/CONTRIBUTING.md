# Contributing to YouTube Summarizer Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install dev dependencies: `pip install -e ".[dev]"`
5. Create a `.env` file with your API keys

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run before committing:
```bash
black src/ utils/ config/
ruff check src/ utils/ config/
mypy src/ utils/ config/
```

## Testing

Add tests for new features:
```bash
pytest tests/
```

## Pull Request Process

1. Update README.md with new features
2. Ensure all tests pass
3. Follow existing code style
4. Write clear commit messages
5. Reference issues in PR description

## Questions?

Open an issue or start a discussion on GitHub!