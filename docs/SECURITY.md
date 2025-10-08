# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Features

The YouTube Summarizer Agent includes multiple security layers:

### Input Validation
- SQL injection protection
- Command injection prevention
- XSS attack mitigation
- Path traversal blocking
- DoS protection (input length limits)
- Null byte filtering

### Rate Limiting
- Per-user request limits
- Platform-wide concurrency limits
- Automatic blocking for abuse

### Data Protection
- No sensitive data logging
- Secure environment variable handling
- Cache encryption ready

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@yourdomain.com**

Include the following information:
- Type of vulnerability
- Full paths of affected source files
- Location of the affected code (tag/branch/commit)
- Step-by-step instructions to reproduce
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolved
- **Fix Timeline**: Critical issues within 7 days, others within 30 days

### Disclosure Policy

- Security advisories will be published after fixes are deployed
- Credit will be given to reporters (unless anonymity is requested)
- CVE IDs will be requested for significant vulnerabilities

## Security Best Practices

### For Users

1. **API Keys**: Never commit `.env` files to version control
2. **Updates**: Keep dependencies up to date: `pip install --upgrade -r requirements.txt`
3. **Deployment**: Use HTTPS in production
4. **Access**: Restrict API access with firewall rules
5. **Monitoring**: Enable logging and monitor for suspicious activity

### For Contributors

1. **Dependencies**: Check for known vulnerabilities before adding new packages
2. **Code Review**: Security-focused review for all PRs
3. **Testing**: Include security test cases
4. **Documentation**: Document security implications of changes

## Known Limitations

- Currently supports only English captions
- Relies on external APIs (OpenRouter, Webshare)
- Cache stored unencrypted on disk (planned for future versions)

## Security Contacts

- **Project Maintainer**: olasanmiayoola@gmail.com
