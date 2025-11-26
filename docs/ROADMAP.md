# 🗺️ PDBot Roadmap

## Version History

### ✅ v1.5.0 - Phase 3 & 4: Behavior Engineering + Query Classification (COMPLETED)
**Release Date:** November 2024

**Major Achievements:**
- ✅ Query classification system with pre-RAG routing
- ✅ Anti-leakage prompts (zero template exposure)
- ✅ Honest audit logging (no dramatic/fake language)
- ✅ Abuse vs banter distinction (soft insults handled differently)
- ✅ Bribery/misuse refactoring (440→78 words, -82% reduction)
- ✅ Off-scope detection (medical, sports, politics, general knowledge)
- ✅ 94% improvement in off-scope query latency (3.5s → 0.2s)

**Technical Implementation:**
- New `src/core/classification.py` module with 8 pattern categories
- Priority-based routing: bribery → abuse → banter → off-scope → in-scope
- Template-based responses for non-in-scope queries (no LLM call)
- System prompt rewrite in `local_model.py` and `app.py`

**Performance Impact:**
- Off-scope latency: -94% (3.5s → 0.2s)
- Bribery refusal word count: -82% (440 → 78 words)
- Fake citations: Eliminated entirely
- Classification overhead: +50ms per query
- Memory usage: No change

---

### ✅ v1.4.0 - PDF Indexing & SentenceTransformer Integration (COMPLETED)
**Release Date:** October 2024

**Major Achievements:**
- ✅ PDF indexing working (747 chunks indexed into Qdrant)
- ✅ Keras 3 uninstalled to resolve import conflicts
- ✅ SentenceTransformer imports functional
- ✅ Streamlit running on http://localhost:8501

**Technical Implementation:**
- Fixed sentence-transformers import issues
- Resolved Keras 3 compatibility problems
- Implemented PDF chunking and embedding
- Qdrant vector database integration

---

### ✅ v1.3.0 - RAG Pipeline & Reranking (COMPLETED)
**Release Date:** September 2024

**Major Achievements:**
- ✅ RAG pipeline with cross-encoder reranking
- ✅ Multi-stage retrieval (initial + rerank)
- ✅ Citation system with page numbers
- ✅ Mistral 7B integration via Ollama

---

### ✅ v1.2.0 - Streamlit UI & User Experience (COMPLETED)
**Release Date:** August 2024

**Major Achievements:**
- ✅ Streamlit web interface
- ✅ Chat history persistence
- ✅ Feedback collection (1-5 star ratings)
- ✅ Session management

---

### ✅ v1.1.0 - Core RAG Infrastructure (COMPLETED)
**Release Date:** July 2024

**Major Achievements:**
- ✅ Basic RAG implementation
- ✅ Vector search with embeddings
- ✅ Local LLM integration

---

## Future Roadmap

### 🚧 v1.6.0 - Multi-Model Support & Performance Optimization (Q1 2025)
**Status:** Planning

**Planned Features:**
1. **Multi-Model Backend**
   - Support for multiple LLM providers (Ollama, OpenAI, Anthropic, Groq)
   - Dynamic model switching based on query complexity
   - Cost optimization for API-based models
   - Fallback mechanisms for model failures

2. **Batch Indexing & Incremental Updates**
   - Batch PDF processing for faster indexing
   - Incremental updates (only re-index changed files)
   - Background indexing without blocking queries
   - Index versioning for rollback capability

3. **Citation Verification & Confidence Scoring**
   - Verify citations are accurate (page number matches content)
   - Confidence scores for each citation
   - Highlight low-confidence answers
   - Citation traceability (show exact text from source)

4. **Performance Enhancements**
   - Query caching for repeated questions
   - Embedding caching to reduce computation
   - Parallel retrieval for multiple chunks
   - GPU acceleration for embeddings

**Technical Challenges:**
- Model API abstraction layer design
- Thread-safe background indexing
- Citation extraction accuracy (Mistral 7B limitations)
- Cache invalidation strategy

---

### 🔮 v1.7.0 - Advanced Context Management (Q2 2025)
**Status:** Research

**Planned Features:**
1. **Conversation Memory**
   - Multi-turn conversation tracking
   - Entity extraction across turns
   - Contextual follow-up questions
   - Session-based context windows

2. **Smart Chunk Expansion**
   - Retrieve surrounding context automatically
   - Hierarchical chunking (section → subsection → paragraph)
   - Context-aware chunk boundaries
   - Overlap optimization

3. **Query Understanding**
   - Intent classification refinement
   - Entity recognition (PC-I, CDWP, ECNEC, etc.)
   - Query reformulation for ambiguous questions
   - Acronym expansion

---

### 🔮 v1.8.0 - Multilingual Support & Accessibility (Q3 2025)
**Status:** Exploration

**Planned Features:**
1. **Urdu Language Support**
   - Urdu query understanding
   - Urdu response generation
   - Mixed Urdu-English queries
   - Cultural context adaptation

2. **Voice Interface**
   - Speech-to-text for queries
   - Text-to-speech for responses
   - Voice-controlled navigation
   - Hands-free operation

3. **Accessibility Features**
   - Screen reader compatibility
   - High-contrast themes
   - Keyboard shortcuts
   - Mobile-responsive design

---

### 🔮 v2.0.0 - Enterprise Features (Q4 2025)
**Status:** Vision

**Planned Features:**
1. **Multi-Tenancy**
   - Organization-level isolation
   - User authentication & authorization
   - Role-based access control
   - Usage tracking & quotas

2. **Admin Dashboard**
   - Query analytics (frequency, topics, errors)
   - User behavior insights
   - Manual curation interface
   - A/B testing framework

3. **Compliance & Audit**
   - Full query audit trail
   - Data retention policies
   - GDPR compliance features
   - Export capabilities

4. **Custom Knowledge Bases**
   - Upload custom documents
   - Domain-specific fine-tuning
   - Private knowledge silos
   - Version control for documents

---

## Research Areas

### Ongoing Research
- **Hallucination Detection:** Automated detection of fabricated answers
- **Active Learning:** Incorporate user feedback to improve responses
- **Contextual Summarization:** Multi-document summarization across manual sections
- **Question Generation:** Auto-generate FAQ from manual content

### Experimental Features
- **Graph-Based RAG:** Knowledge graph for complex relationships
- **Hybrid Search:** Combine semantic + keyword search
- **Dynamic Prompting:** Adaptive prompts based on query type
- **Chain-of-Thought:** Explicit reasoning steps in answers

---

## Community & Contributions

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Priority Areas for Contributions
- 🔴 **High Priority:** Citation verification, multi-model support
- 🟡 **Medium Priority:** Query caching, batch indexing
- 🟢 **Low Priority:** UI enhancements, additional themes

---

## Contact & Support

**For Questions:**
- Open an issue on GitHub
- Email: [your-email@example.com]

**For Feature Requests:**
- Use GitHub Discussions
- Submit a feature request issue

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Last Updated:** November 2024  
**Current Version:** v1.5.0  
**Next Milestone:** v1.6.0 (Q1 2025)
