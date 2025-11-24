# Contributing to PDBot

## ⚠️ PROPRIETARY SOFTWARE NOTICE

**PDBot is proprietary software owned by the Planning & Development Commission, Government of Pakistan.**

This software is **NOT open source**. Contributions are restricted to authorized government personnel and approved contractors only.

### Licensing & Access

For authorization requests or licensing inquiries, contact:
- **Hassan Arif Afridi**
- **Email:** hassanarifafridi@gmail.com
- **Organization:** Planning & Development Commission, Government of Pakistan

---

## Guidelines for Authorized Contributors

If you are an authorized contributor, this document provides guidelines for contributing to the project.

## 🚀 Quick Start (Authorized Personnel Only)

**IMPORTANT:** You must be an authorized government employee or approved contractor to contribute.

1. **Request Authorization**
   - Contact: hassanarifafridi@gmail.com
   - Provide: Name, Organization, Purpose
   - Wait for approval before proceeding

2. **Fork the repository** (after authorization)
   ```bash
   gh repo fork athem135-source/PDBOT
   ```

3. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/PDBOT.git
   cd PDBOT
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Set up development environment**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Pull required models
   ollama pull mistral
   
   # Run the app
   streamlit run src/app.py
   ```

## 📋 Development Guidelines

### Code Style

- **Python:** Follow PEP 8 style guidelines
- **Line length:** 120 characters maximum
- **Imports:** Group by standard library, third-party, local modules
- **Type hints:** Use type hints for function signatures
- **Docstrings:** Use Google-style docstrings for functions/classes

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(rag): add support for DOCX file uploads
fix(ui): correct floating action bar positioning on mobile
docs(readme): update installation instructions for Windows
refactor(prompts): simplify system prompt to reduce token usage
```

### Testing

Before submitting a PR, ensure:

1. **Manual Testing**
   - Test simple queries: "What is PC-I?"
   - Test complex queries: "Explain CDWP approval process"
   - Test safety protocols: Check Red Line Protocol responses
   - Test citations: Verify `[p.X]` format
   - Test formatting: Check bold, bullets, tables

2. **Performance Testing**
   - Measure tokens/second (should be 20-40 for Mistral 7B)
   - Check RAM usage (should be ~8GB)
   - Verify response time (<5 seconds for typical queries)

3. **Edge Cases**
   - Empty queries
   - Very long queries (>500 words)
   - Off-topic queries
   - Abusive/illegal content (verify warnings)
   - OCR errors (PC-l, Rs.lOOM, etc.)

## 🎯 Contribution Areas

### High Priority

1. **Model Optimization**
   - Quantization for lower RAM usage
   - Context window management
   - Caching strategies

2. **RAG Improvements**
   - Better chunking strategies
   - Improved retrieval accuracy
   - Multi-document support

3. **UI/UX Enhancements**
   - Mobile responsiveness
   - Dark mode
   - Export chat history
   - Keyboard shortcuts

4. **Safety & Security**
   - Additional Red Line Protocols
   - Input sanitization
   - Rate limiting

### Medium Priority

1. **Documentation**
   - API documentation
   - Architecture diagrams
   - Video tutorials
   - Translation to Urdu

2. **Testing**
   - Unit tests
   - Integration tests
   - Performance benchmarks

3. **Features**
   - Multi-user support
   - Session management
   - Advanced search filters
   - Feedback collection

### Low Priority

1. **Integrations**
   - REST API
   - Slack/Teams bots
   - Email notifications

2. **Analytics**
   - Usage statistics
   - Query patterns
   - Performance metrics

## 🔍 Pull Request Process

1. **Before Submitting**
   - Ensure your branch is up-to-date with `main`
   - Run manual tests
   - Update documentation if needed
   - Add entry to CHANGELOG.md (if applicable)

2. **PR Description Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Manual testing completed
   - [ ] Edge cases tested
   - [ ] Performance verified
   
   ## Screenshots (if UI changes)
   Add screenshots here
   
   ## Related Issues
   Closes #123
   ```

3. **Review Process**
   - PRs require at least one approval
   - Address review comments promptly
   - Keep discussions professional and constructive

4. **Merging**
   - Use "Squash and merge" for feature branches
   - Use "Rebase and merge" for hotfixes
   - Delete branch after merging

## 🐛 Bug Reports

Use the following template for bug reports:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
Add screenshots if applicable

**Environment:**
- OS: [e.g., Windows 11]
- Python version: [e.g., 3.12.7]
- Ollama version: [e.g., 0.1.17]
- Model: [e.g., mistral:7b]

**Additional context**
Any other relevant information
```

## 💡 Feature Requests

Use the following template:

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Use case**
Who would benefit and how?

**Additional context**
Mockups, examples, etc.
```

## 📚 Resources

- **LangChain Docs:** https://python.langchain.com/docs/
- **Ollama Docs:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Streamlit Docs:** https://docs.streamlit.io/
- **Mistral AI:** https://docs.mistral.ai/

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy towards other members

**Unacceptable behavior:**
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct inappropriate in a professional setting

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

## 📧 Contact

- **GitHub Issues:** https://github.com/athem135-source/PDBOT/issues (authorized users only)
- **Discussions:** https://github.com/athem135-source/PDBOT/discussions (authorized users only)
- **Licensing & Authorization:** hassanarifafridi@gmail.com
- **Technical Issues:** hassanarifafridi@gmail.com

## 🏆 Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes for significant contributions
- Project documentation

Thank you for contributing to PDBot! 🚀
