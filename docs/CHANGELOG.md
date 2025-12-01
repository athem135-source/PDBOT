# Changelog

All notable changes to PDBOT are documented in this file.

> **Project Started:** October 16, 2025  
> **Developer:** M. Hassan Arif Afridi

---

## [2.3.0] - 2025-12-01

### 🆕 Added

#### Admin Panel
- Hidden admin panel (access code: "nufc")
- Backend status monitoring (Qdrant, Ollama, memory)
- Clear server/local memory functions
- Custom logo URL setting
- Debug information display

#### Mobile Access
- Network IP display on server startup
- Access widget from any device on same network
- Production WSGI server (Waitress)

#### Widget Improvements
- Pakistan emblem logo in header
- Better error handling for server connection
- Improved clear chat functionality

### 🔧 Changed
- Replaced Flask dev server with Waitress (production WSGI)
- Clear chat now clears both server AND local storage
- Updated version to 2.3.0 across all files

### 📦 Dependencies
- Added `waitress>=3.0.0` for production server
- Added `psutil>=5.9.0` for admin status monitoring

---

## [2.2.1] - 2025-12-01

### 📝 Documentation Overhaul
- Complete README rewrite with professional formatting
- Added project roadmap (Oct 16, 2025 - Present)
- Added comprehensive performance metrics section
- Added version accuracy progression chart
- Added developer information and LinkedIn link
- Fixed markdown rendering issues (removed CDATA tags)

### 🔧 Fixed
- Fixed broken README markdown rendering
- Updated SECURITY.md with proper formatting
- Added LICENSE file with MIT License + Disclaimer
- Updated CHANGELOG with correct dates (2025)

---

## [2.2.0] - 2025-12-01

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

## [2.1.0] - 2025-11-12

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

## [2.0.8] - 2025-11-05

### 🐛 Fixed
- Duplicate "✅ Answer:" prefix bug
- Answer sanitization improvements
- Numeric extraction reliability

### 🔧 Changed
- Strict 45-70 word answer limits
- Clean single-line citations
- Improved post-generation cleanup

---

## [2.0.0] - 2025-11-05

### 🆕 Added
- Sentence-level RAG chunking
- Cross-encoder reranking
- Numeric boosting for financial queries
- Streamlit admin interface

---

## [1.1.0] - 2025-10-31

### 🆕 Added
- 12-class query classifier integration
- 78% overall accuracy achieved
- Improved off-scope detection

---

## [1.0.0] - 2025-10-25

### 🆕 Added
- First stable release
- Streamlit UI implementation
- Qdrant vector database integration
- 72% overall accuracy

---

## [0.5.0] - 2025-10-20

### 🆕 Added
- Basic RAG pipeline
- PDF ingestion capability
- Initial retrieval system
- 68% baseline accuracy

---

## [0.1.0] - 2025-10-16

### 🎉 Project Inception
- Initial concept and requirements gathering
- Project structure setup
- Technology stack selection

**Government of Pakistan**
*Ministry of Planning, Development & Special Initiatives*
