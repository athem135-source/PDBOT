# Changelog

All notable changes to PDBOT are documented in this file.

## [2.2.0] - 2024-12-01

### 🆕 Added

#### React Widget
- Standalone floating chat widget (no Streamlit dependency)
- Draggable, minimizable, closeable interface
- Government of Pakistan official color scheme
- Typewriter effect for bot responses
- Download chat as TXT or PDF
- Settings menu with New Chat, Clear Chat options

#### Contextual Memory
- Session-based conversation memory
- Follow-up question understanding
- Automatic memory cleanup on new chat
- Server-side memory management API

#### Source Transparency
- "View Passages" button - shows retrieved text chunks
- "View Sources" button - shows page references with relevance
- Modal overlays for detailed information
- Relevance percentage display

#### User Experience
- Accuracy warning disclaimer under input box
- Like/Dislike feedback buttons
- Regenerate response button
- Suggested questions for new users

### 🔧 Changed
- Updated Qdrant default port to 6338
- Improved error handling in API
- Enhanced CORS configuration
- Unified launcher script (start_pdbot.bat)

### 🐛 Fixed
- Typewriter effect first character bug
- Clear chat not working properly
- Drag functionality on widget header
- Session memory persistence issues

---

## [2.1.0] - 2024-11-15

### 🆕 Added

#### Multi-Class Query Classifier
- 12-class classification system
- Intent detection before RAG processing
- Classification: in_scope, numeric_query, definition_query, procedure_query, compliance_query, timeline_query, formula_or_method, monitoring_evaluation, off_scope, red_line, abusive, fallback_required
- Retrieval hints from classifier

#### Groq Fallback Pipeline
- Automatic fallback when Ollama fails
- Same guardrails as primary model
- Dual model support (llama-3.1-8b, mixtral-8x7b)

#### Enhanced Retrieval
- Procedure boost (+0.15)
- Formula boost (+0.15)
- Monitoring/M&E boost (+0.15)
- Multi-sentence preference for complex queries

### 🔧 Changed
- Improved guardrail response system
- Cleaner off-scope handling
- Development governance whitelist

---

## [2.0.8] - 2024-10-31

### 🐛 Fixed
- Duplicate "✅ Answer:" prefix bug
- Answer sanitization improvements
- Numeric extraction reliability

### 🔧 Changed
- Strict 45-70 word answer limits
- Clean single-line citations
- Improved post-generation cleanup

---

## [2.0.0] - 2024-10-15

### 🆕 Added
- Sentence-level RAG chunking
- Cross-encoder reranking
- Numeric boosting for financial queries
- Streamlit admin interface

---

**Government of Pakistan**
*Ministry of Planning, Development & Special Initiatives*
