# Test Files

Test scripts for validating PDBot functionality and debugging.

## Test Files

- **test_imports.py** - Verify all Python imports work correctly
- **test_refactor.py** - Test core refactoring functionality
- **test_retrieval_fixes.py** - Validate RAG retrieval improvements
- **test_failing_queries.py** - Debug failing query scenarios
- **test_v1.7.0.py** - Legacy v1.7.0 tests
- **test_v181_diagnosis.py** - Diagnostic tests for v1.8.1 numeric bug

## Running Tests

```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Run all tests
pytest tests/ -v

# Run specific test file
python tests/test_imports.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Categories

### Import Tests
- Verify all dependencies are installed
- Check module imports work

### Retrieval Tests
- Validate semantic search accuracy
- Test cross-encoder reranking
- Verify numeric value boosting

### Diagnostic Tests
- Debug specific failing queries
- Analyze chunking issues
- Validate numeric preservation

## Notes

- Tests assume Qdrant is running on localhost:6333
- Tests require Ollama with mistral model installed
- Some tests may modify `src/data/chat_single.json` (test data)
