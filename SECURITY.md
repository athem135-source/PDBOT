# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.8.x   | :x:                |
| < 1.8   | :x:                |

## Security Updates in v2.0.0

PDBot v2.0.0 includes comprehensive security updates addressing all known vulnerabilities:

### Fixed CVEs

| Package | CVE | Severity | Fix |
|---------|-----|----------|-----|
| requests | CVE-2024-35195 | High | 2.32.0 → 2.32.3 |
| streamlit | Multiple XSS | Medium | 1.36.0 → 1.40.0 |
| pypdf | Malicious PDF | High | 4.2.0 → 5.1.0 |
| PyMuPDF | Buffer Overflow | Medium | 1.24.0 → 1.25.2 |
| transformers | Model Loading | Medium | 4.44.2 → 4.47.0 |
| sentence-transformers | Dependencies | Low | 3.0.0 → 3.3.1 |
| qdrant-client | API Security | Low | 1.9.0 → 1.12.1 |
| langchain | Multiple | High | 0.2.0 → 0.3.0 |
| nltk | Minor Patches | Low | 3.8.1 → 3.9.1 |

### Additional Security Measures

**New Security Dependencies (v2.0.0):**
- `urllib3 >= 2.2.3` - HTTP client security
- `certifi >= 2024.8.30` - SSL certificate management  
- `cryptography >= 44.0.0` - Critical cryptographic updates

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Preferred Method

Email security concerns to: [Contact via GitHub Issues with "SECURITY" label](https://github.com/athem135-source/PDBOT/issues/new?labels=security)

When reporting, please include:

1. **Type of issue** (e.g., buffer overflow, SQL injection, XSS)
2. **Full paths** of source file(s) related to the issue
3. **Location** of the affected source code (tag/branch/commit or direct URL)
4. **Step-by-step instructions** to reproduce the issue
5. **Proof-of-concept or exploit code** (if possible)
6. **Impact** of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response:** Within 48 hours
- **Confirmation:** Within 7 days  
- **Fix Timeline:** Varies by severity (Critical: 7 days, High: 30 days, Medium: 90 days)
- **Disclosure:** After fix is released and deployed

## Security Best Practices

### For Users

1. **Always use the latest version** - Run `pip install --upgrade -r requirements.txt`
2. **Keep dependencies updated** - Check for updates monthly
3. **Run in isolated environment** - Use virtual environments (`.venv`)
4. **Limit network exposure** - Run Ollama and Qdrant on localhost only
5. **Review uploaded PDFs** - Only upload trusted documents
6. **Use HTTPS** - If exposing to network, use reverse proxy with SSL
7. **Monitor logs** - Check `logs/` folder for suspicious activity

### For Developers

1. **Dependency scanning** - Run `pip audit` before releasing
2. **Code review** - All PRs must be reviewed
3. **Input validation** - Sanitize all user inputs
4. **Secrets management** - Never commit `.env` files
5. **Docker security** - Use non-root user in containers
6. **Regular updates** - Check for security updates weekly

## Security Architecture

### Data Privacy

- **Local-only processing:** No data sent to external servers
- **No telemetry:** Zero data collection or tracking
- **GDPR compliant:** Data stays on your infrastructure
- **SOC2 ready:** Audit logs available in `logs/` and `feedback/`

### Network Security

- **Ollama:** localhost:11434 (no external exposure)
- **Qdrant:** localhost:6333 (no external exposure)
- **Streamlit:** localhost:8501 (behind reverse proxy in production)

### Authentication

Currently, PDBot does not include built-in authentication. For production deployment:

1. **Use a reverse proxy** (Nginx, Apache) with HTTP Basic Auth
2. **Implement OAuth2** via Streamlit authentication extension
3. **Use VPN** for secure remote access
4. **Network isolation** via Docker networks

## Compliance

### Data Protection

- **No PII collection:** User queries are stored only locally
- **Data retention:** Controlled by user (delete `logs/` and `feedback/`)
- **Right to erasure:** Delete all files in `data/`, `logs/`, `feedback/`

### Audit Trail

- **Query logging:** All interactions logged to `logs/`
- **Feedback:** User ratings stored in `feedback/`
- **Red-line detection:** Bribery/corruption attempts flagged and logged

## Security Contact

- **GitHub Issues:** [Create a security issue](https://github.com/athem135-source/PDBOT/issues/new?labels=security)
- **Repository:** https://github.com/athem135-source/PDBOT
- **Maintainer:** [@athem135-source](https://github.com/athem135-source)

---

**Last Updated:** November 26, 2025  
**Version:** 2.0.0
