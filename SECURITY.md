# Security Policy

## ⚠️ PROPRIETARY SOFTWARE - GOVERNMENT USE ONLY

**PDBot is proprietary software owned by the Planning & Development Commission, Government of Pakistan.**

Unauthorized access, use, or distribution is strictly prohibited and may be subject to legal action under Pakistani law.

### Licensing & Authorization

For licensing inquiries or authorized use requests, contact:
- **Hassan Arif Afridi**
- **Email:** hassanarifafridi@gmail.com
- **Organization:** Planning & Development Commission, Government of Pakistan

---

## Supported Versions

We actively support the following versions of PDBot with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.3.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :x:                |
| 1.0.x   | :x:                |

## Security Features

### Data Privacy

PDBot is designed with privacy-first principles:

- **Local Deployment** - All processing happens on your machine
- **No External API Calls** - LLM inference via Ollama (local)
- **No Data Collection** - We don't collect, store, or transmit user queries
- **Document Security** - Uploaded PDFs stay on your local filesystem
- **Vector Store** - Qdrant runs locally, no cloud storage

### Input Sanitization

- File upload validation (PDF only, max 200MB)
- Query length limits (max 2000 characters)
- Path traversal protection for file operations
- Markdown injection prevention in responses

### Red Line Protocols

Built-in safety mechanisms for government deployment:

1. **Illegal Content Detection**
   - Fraud, bribery, corruption warnings
   - Legal channels provided (ACE, Citizen Portal)
   - No facilitation of illegal activities

2. **Abuse Handling**
   - Polite pushback for offensive language
   - Maintains professional tone
   - Doesn't refuse service, just maintains dignity

3. **Off-Topic Queries**
   - Clear scope definition
   - Redirection to manual topics
   - No generic conversations

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do Not Publicly Disclose

**DO NOT** create a public GitHub issue for security vulnerabilities. This could put users at risk.

### 2. Contact Us Privately

**Email:** hassanarifafridi@gmail.com  
**Subject:** [SECURITY] Brief description of the issue

**Note:** Only authorized users should report security issues. Include your authorization details in the report.

### 3. Provide Details

Include the following information:

```markdown
**Vulnerability Type:**
[e.g., Code Injection, XSS, Path Traversal, etc.]

**Affected Component:**
[e.g., File Upload, Query Processing, Vector Store, etc.]

**Affected Versions:**
[e.g., v1.3.0, all versions, etc.]

**Description:**
Clear description of the vulnerability

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Impact:**
What could an attacker do with this vulnerability?

**Proof of Concept:**
Code or screenshots demonstrating the issue (if applicable)

**Suggested Fix:**
Your recommendation for fixing (optional)

**Discoverer:**
Your name/handle for credit (optional)
```

### 4. Response Timeline

- **Initial Response:** Within 48 hours
- **Assessment:** Within 7 days
- **Fix Development:** 7-30 days (depending on severity)
- **Public Disclosure:** After fix is released and users have time to update

### 5. Severity Levels

We use the following severity classification:

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, data breach | 24 hours |
| **High** | Privilege escalation, authentication bypass | 7 days |
| **Medium** | Information disclosure, DoS | 14 days |
| **Low** | Minor security improvements | 30 days |

## Security Best Practices

### For Users

1. **Keep Software Updated**
   ```bash
   git pull origin main
   pip install -r requirements.txt --upgrade
   ollama pull mistral  # Update model
   ```

2. **Secure Your Environment**
   - Run PDBot in a dedicated virtual environment
   - Don't expose Streamlit port (8501) to the internet
   - Use localhost access only: `http://localhost:8501`

3. **Validate Uploads**
   - Only upload trusted PDF files
   - Scan files with antivirus before uploading
   - Don't upload sensitive personal information

4. **Monitor Resource Usage**
   - Check RAM/CPU usage regularly
   - Watch for unusual spikes
   - Restart if performance degrades

5. **Backup Data**
   ```bash
   # Backup vector store
   cp -r data/qdrant_storage data/qdrant_backup
   
   # Backup uploaded PDFs
   cp -r data/uploads data/uploads_backup
   ```

### For Developers

1. **Code Review**
   - All PRs require security review
   - Check for common vulnerabilities (OWASP Top 10)
   - Use static analysis tools

2. **Dependencies**
   ```bash
   # Check for vulnerable dependencies
   pip-audit
   
   # Keep dependencies updated
   pip list --outdated
   ```

3. **Input Validation**
   - Validate all user inputs
   - Sanitize file paths
   - Escape special characters

4. **Secure Coding**
   - No hardcoded secrets
   - Use environment variables for configuration
   - Implement proper error handling (don't leak stack traces)

5. **Testing**
   - Include security test cases
   - Test edge cases and malformed inputs
   - Verify file upload restrictions

## Known Security Considerations

### 1. Local LLM Limitations

- **Jailbreaking:** LLMs can sometimes bypass safety prompts with clever wording
- **Mitigation:** Red Line Protocols + prompt engineering
- **User Action:** Report any successful prompt injection attempts

### 2. PDF Parsing

- **Malicious PDFs:** Crafted PDFs could potentially exploit parsing libraries
- **Mitigation:** File size limits, type validation, sandboxed processing
- **User Action:** Only upload trusted PDFs from official sources

### 3. Streamlit Session State

- **Session Hijacking:** If exposed to network, sessions could be vulnerable
- **Mitigation:** Localhost-only deployment recommended
- **User Action:** Don't expose port 8501 to public networks

### 4. Vector Store Access

- **Data Leakage:** Vector embeddings could theoretically leak information
- **Mitigation:** Local storage only, no network access
- **User Action:** Protect `data/qdrant_storage` directory

## Security Updates

Security updates will be:

1. **Announced** in GitHub Security Advisories
2. **Tagged** with severity level
3. **Released** as patch versions (e.g., v1.3.1)
4. **Documented** in CHANGELOG.md

Subscribe to releases: https://github.com/athem135-source/PDBOT/releases

## Compliance

PDBot is designed for government use and considers:

- **Data Sovereignty:** All processing on-premises
- **Privacy Laws:** No external data transmission
- **Audit Trails:** Feedback system for query tracking
- **Access Control:** File-based permissions (OS-level)
- **Proprietary Rights:** Government of Pakistan exclusive ownership
- **Restricted Distribution:** Authorized government entities only

## Security Roadmap

Future security enhancements:

- [ ] Rate limiting for queries
- [ ] Session timeout mechanisms
- [ ] Enhanced file validation (magic number checks)
- [ ] Encrypted vector storage
- [ ] Audit logging system
- [ ] User authentication (multi-user deployments)
- [ ] Role-based access control

## Credits

We acknowledge security researchers who responsibly disclose vulnerabilities:

- *No reports yet - be the first!*

Thank you for helping keep PDBot secure! 🛡️

---

**Last Updated:** November 24, 2025  
**Version:** 1.0
