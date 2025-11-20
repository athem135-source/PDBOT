# Changelog

All notable changes to PDBOT will be documented in this file.

## [v0.8.5] - 2025-11-20

### Reverted
- **ROLLBACK: Modular Architecture (v0.9.0)** - Reverted to monolithic architecture
  - Removed modular file structure (src/logic/, src/ui/, src/utils/pdf_renderer.py)
  - Restored original single-file app.py (3,094 lines)
  - **Reason**: Modular refactoring caused UI inconsistencies and removed critical features
    - Missing backend status checks (Ollama, Qdrant connectivity)
    - Removed settings controls (New Chat, Clear All buttons)
    - Changed UI layout that users were familiar with
    - Simplified structure proved more reliable for this application

### Preserved
- ✅ Enterprise RAG pipeline with cross-encoder reranking
- ✅ 7-way chunk classification (policy/definition/table/checklist/annexure/commentary/other)
- ✅ All backend functionality (Ollama, Pretrained models, Qdrant)
- ✅ Admin mode features
- ✅ Feedback system

### Technical Notes
- Modular architecture attempted to split 3,088 lines across 7 files
- While cleaner in theory, it fragmented critical UI components
- Original monolithic structure better suited for Streamlit's reactive model
- Future refactoring will focus on backend modules only, keeping UI unified

---

## [v0.9.0] - 2025-11-18 (DEPRECATED)

### Added
- ❌ Modular architecture with separated components (REVERTED)
- ❌ PDF page rendering for "View Source" feature (REVERTED)
- ❌ PyMuPDF integration (REMOVED)

### Changed
- ❌ Split app.py into 7 modular files (REVERTED)
- ❌ Redesigned UI layout (REVERTED)

---

## [v0.8.0] - 2025-11-15

### Added
- ✅ Enterprise RAG pipeline with advanced retrieval
- ✅ Cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
- ✅ 7-way semantic chunk classification
- ✅ MMR diversity control (lambda_mult=0.7)
- ✅ Anti-hallucination filters for annexures and checklists

### Fixed
- ✅ Eliminated annexure table leakage in answers
- ✅ Removed N/A Yes/No checklist fragments from responses
- ✅ Improved answer quality with better context filtering

### Technical
- sentence-transformers 5.1.2 with all-MiniLM-L6-v2 embeddings
- Qdrant vector database integration
- LangChain text splitting and processing
- tf-keras 2.20.1 for Keras 3 compatibility

---

## Earlier Versions

### [v0.7.x] - Initial RAG Implementation
- Basic retrieval-augmented generation
- Ollama LLM integration
- Manual PDF processing
- Simple keyword search

### [v0.6.x] - Core Features
- Streamlit UI foundation
- Chat history persistence
- User feedback system
- Admin mode controls
