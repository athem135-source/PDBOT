# 🚀 Release v1.7.0: Ultra-Strict Dynamic RAG System

**Release Date**: November 26, 2025  
**Previous Version**: v1.6.1  
**Status**: ✅ Production Ready

---

## 🎯 Critical Problems Fixed

### 1. ✅ Eliminated Over-Answering
**Problem**: Bot gave correct 1-sentence answer, then added 6-15 paragraphs of irrelevant content (ECNEC composition tables, climate change annexures, iPAS system descriptions, notification codes, annexure listings)

**Solution**:
- Added 10-rule post-filter in `rag_langchain.py`
- Filters out: tables, figures, annexures, notifications, iPAS chunks, climate tables, headers/footers
- Reduced max chunks from 3 → **2**
- Increased relevance threshold from 0.35 → **0.40**

### 2. ✅ Fixed Citation Spam
**Problem**: Answers showed 10-15 citations at the bottom

**Solution**:
- Removed internal citation line from `compose_answer()`
- Limited external citations to top **3 sources only**

### 3. ✅ Removed ALL Hardcoded Numeric Values
**Problem**: System used hardcoded approval limits from `approval_limits.py`, preventing multi-PDF support

**Solution**:
- Created NEW `src/core/numeric_safety_dynamic.py`
- Removed hardcoded constants check
- **ALL values now retrieved dynamically from RAG**
- Works with ANY PDF version (2024, 2025, 2026, etc.)

### 4. ✅ Enhanced System Prompts
**Solution**:
- Updated prompts: "Manual for Development Projects **(all versions)**"
- Added **12 hard rules** including anti-hallucination, anti-hardcoding
- Multi-PDF version awareness

---

## 📊 What Changed

### New Files
- `src/core/numeric_safety_dynamic.py` - Dynamic validation module (200 lines)
- `REFACTOR_v1.7.0_SUMMARY.md` - Comprehensive documentation
- `test_v1.7.0.py` - 18-query test suite

### Modified Files
- `src/rag_langchain.py` - Added `post_filter_garbage_chunks()` (118 lines), updated thresholds
- `src/app.py` - Removed internal citations, limited to 3 sources, switched to dynamic safety
- `src/models/local_model.py` - Updated system prompt to v1.7.0
- `src/core/classification.py` - Enhanced off-scope patterns

### Configuration Changes
- `MIN_RELEVANCE_SCORE`: 0.35 → **0.40**
- `MAX_FINAL_CHUNKS`: 3 → **2**
- `initial_k`: 20 → **15**

---

## 📈 Improvements

| Metric | Before (v1.6.1) | After (v1.7.0) |
|--------|-----------------|----------------|
| Answer Length | 100-300 words | **≤80 words** |
| Citations | 10-15 sources | **≤3 sources** |
| Hardcoded Values | Yes | **❌ None (fully dynamic)** |
| Garbage Chunks | High | **Zero (10-rule filter)** |
| Multi-PDF Ready | No | **✅ Yes** |
| Relevance Threshold | 0.35 | **0.40** |
| Max Chunks | 3 | **2** |

---

## ⚠️ Breaking Changes

1. **Hardcoded approval limits removed**: System no longer uses `approval_limits.py` constants
2. **All queries require RAG**: No more instant responses for numeric queries (slight latency increase)
3. **Stricter filtering**: Some edge-case queries may return "Not found" if context quality is low

---

## 🧪 Testing

Run the included test suite:
```bash
python test_v1.7.0.py
```

**18 test queries** covering:
- Over-answering fixed (4 queries)
- Citation spam fixed (3 queries)
- Dynamic retrieval (3 queries)
- Garbage filtering (2 queries)
- Classification regression (6 queries)

---

## 🚀 Deployment

### Installation
```bash
git clone https://github.com/athem135-source/PDBOT.git
cd PDBOT
git checkout v1.7.0
pip install -r requirements.txt
```

### Running
```bash
streamlit run src/app.py
```

### Vector DB
No rebuild required - existing `pnd_manual_v2` collection works with v1.7.0.

---

## 📚 Documentation

See [REFACTOR_v1.7.0_SUMMARY.md](./REFACTOR_v1.7.0_SUMMARY.md) for:
- Complete implementation details
- File-by-file changes
- Testing requirements
- Future enhancements (v1.8.0)

---

## ⏳ Deferred to v1.8.0

1. **Chat Memory**: Compressed session memory system
2. **Version-Aware Metadata**: Multi-PDF version filtering

Both features are **prepared for** (prompts updated), just need implementation.

---

## 🙏 Acknowledgments

This release addresses critical issues identified in production testing with 60+ real-world queries. Special thanks to the testing team for comprehensive feedback.

---

## 📝 Full Changelog

**Features:**
- ✨ Ultra-strict 80-word answer limit
- ✨ 10-rule garbage chunk filter
- ✨ Dynamic numeric validation (no hardcoding)
- ✨ Multi-PDF version awareness
- ✨ Citation limit (≤3 sources)

**Improvements:**
- ⚡ Higher precision (threshold 0.35 → 0.40)
- ⚡ Reduced chunk explosion (3 → 2 max)
- ⚡ Better context quality checks

**Bug Fixes:**
- 🐛 Fixed over-answering (6-15 paragraph spam)
- 🐛 Fixed citation spam (10-15 sources)
- 🐛 Fixed RAG pollution (tables/annexures/iPAS)
- 🐛 Fixed numeric contradictions

**Documentation:**
- 📝 Added REFACTOR_v1.7.0_SUMMARY.md
- 📝 Added test_v1.7.0.py test suite
- 📝 Updated system prompts with anti-hallucination rules

---

## 🔗 Links

- **Documentation**: [REFACTOR_v1.7.0_SUMMARY.md](./REFACTOR_v1.7.0_SUMMARY.md)
- **Previous Release**: [v1.6.1](https://github.com/athem135-source/PDBOT/releases/tag/v1.6.1)
- **Issues**: [Report a bug](https://github.com/athem135-source/PDBOT/issues)

---

**Commit**: `a688a27`  
**Tag**: `v1.7.0`  
**Date**: November 26, 2025
