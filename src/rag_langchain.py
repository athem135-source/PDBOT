"""
Enterprise-Grade RAG Pipeline for PDBOT v0.9.0
===============================================

CRITICAL FIXES IMPLEMENTED:
1. ✅ Chunk Classification & Tagging (main_manual, annexure, checklist, table, appendix)
2. ✅ Cross-Encoder Semantic Reranker (reranks top 20 → final 3 chunks)
3. ✅ Reduced chunk explosion (60 → 3 final chunks for LLM)
4. ✅ Post-generation guardrails (filters annexure/checklist leakage)
5. ✅ Advanced metadata (section_title, is_annexure, is_table, is_checklist)
6. ✅ Improved chunking (600 chars with 100 overlap)
7. ✅ Diagnostic logging for debugging

Requirements:
- sentence-transformers (embeddings + cross-encoder)
- qdrant-client (vector DB)
- pypdf (PDF parsing)
"""
from __future__ import annotations

import os
import re
import warnings
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Suppress compatibility warnings
warnings.filterwarnings("ignore", category=Warning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Import dependencies with graceful fallback
SENTENCE_TRANSFORMERS_AVAILABLE = False
QDRANT_AVAILABLE = False
PYPDF_AVAILABLE = False

# Suppress torch warnings that interfere with imports
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except ImportError:
        SentenceTransformer = None  # type: ignore
        CrossEncoder = None  # type: ignore
    except Exception:
        SentenceTransformer = None  # type: ignore
        CrossEncoder = None  # type: ignore

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None  # type: ignore
    Distance = None  # type: ignore
    VectorParams = None  # type: ignore
    PointStruct = None  # type: ignore
except Exception:
    QdrantClient = None  # type: ignore
    Distance = None  # type: ignore
    VectorParams = None  # type: ignore
    PointStruct = None  # type: ignore

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
except Exception:
    PdfReader = None

# ============================================================================
# CONFIGURATION
# ============================================================================

COLLECTION = os.getenv("PNDBOT_RAG_COLLECTION", "pnd_manual_sentences")
EMBED_MODEL = os.getenv("PNDBOT_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# CRITICAL: Cross-encoder for semantic reranking
RERANKER_MODEL = os.getenv("PNDBOT_RERANKER", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# Debug mode (set PNDBOT_DEBUG=True in environment to enable)
DEBUG_MODE = os.getenv("PNDBOT_DEBUG", "False").lower() == "true"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ChunkMetadata:
    """Metadata for each chunk with classification tags."""
    text: str
    page: int
    chunk_type: str  # main_manual, annexure, checklist, table, appendix, misc
    proforma: Optional[str]  # PC-I, PC-II, PC-III, PC-IV, PC-V or None
    section_title: Optional[str]
    is_annexure: bool
    is_table: bool
    is_checklist: bool
    chapter: Optional[str]


# ============================================================================
# CHUNK CLASSIFICATION (FIX #1 - CRITICAL)
# ============================================================================

def classify_chunk_type(text: str, page_num: int) -> str:
    """Classify chunk into: main_manual, annexure, checklist, table, appendix, misc.
    
    CRITICAL FIX #1: Prevents annexure/checklist contamination in conceptual answers.
    
    Rules:
    - Annexure: Contains "Annexure", "Annex", "Appendix" keywords
    - Checklist: Contains "N/A Yes No", "Inclusion of", "S. No.", etc.
    - Table: High density of numbers, pipe delimiters, column headers
    - Appendix: "Appendix" keyword and page > 80
    - Main Manual: Everything else (default)
    """
    text_lower = text.lower()
    text_stripped = text.strip()
    
    # === ANNEXURE DETECTION ===
    annexure_patterns = [
        r'\bannexure[- ][a-z0-9]+\b',
        r'\bannex[- ][a-z0-9]+\b',
        r'\bappendix[- ][a-z0-9]+\b',
        r'annexure to proforma',
        r'attached as annexure',
    ]
    if any(re.search(pat, text_lower) for pat in annexure_patterns):
        return "annexure"
    
    # === CHECKLIST DETECTION ===
    checklist_indicators = [
        "n/a yes no",
        "yes/no checklist",
        "inspection checklist",
        "inclusion of",
        "s. no.",
        "sr. no.",
        "item checked",
        "✓ checked",
        "checklist item",
    ]
    if any(indicator in text_lower for indicator in checklist_indicators):
        return "checklist"
    
    # Check for repetitive row patterns (Annexure tables often have this)
    if re.search(r'(\d+\.\s+.{10,50}\s*){5,}', text_stripped):
        return "checklist"
    
    # === TABLE DETECTION ===
    words = text_stripped.split()
    if len(words) > 10:
        number_count = len(re.findall(r'\b\d+\b', text_stripped))
        
        # High number density
        if number_count > 10 and len(words) < 100:
            return "table"
        
        # Pipe/tab delimiters
        if text_stripped.count('|') > 5 or text_stripped.count('\t') > 3:
            return "table"
        
        # Column headers + numbers
        if re.search(r'(s\.?\s*no\.?|sr\.?\s*no\.?|item|description|amount|cost)', text_lower):
            if number_count > 5:
                return "table"
    
    # === APPENDIX DETECTION ===
    if 'appendix' in text_lower and page_num > 80:
        return "appendix"
    
    # === MAIN MANUAL (DEFAULT) ===
    return "main_manual"


def detect_proforma_type(text: str) -> Optional[str]:
    """Detect which PC proforma this text relates to.
    
    Returns: "PC-I", "PC-II", "PC-III", "PC-IV", "PC-V", or None
    """
    text_lower = text.lower()
    
    proforma_patterns = {
        "PC-I": [r'\bpc-?i\b', r'\bpc-?1\b', r'\bproforma-?i\b', r'\bproforma-?1\b'],
        "PC-II": [r'\bpc-?ii\b', r'\bpc-?2\b', r'\bproforma-?ii\b', r'\bproforma-?2\b'],
        "PC-III": [r'\bpc-?iii\b', r'\bpc-?3\b', r'\bproforma-?iii\b', r'\bproforma-?3\b'],
        "PC-IV": [r'\bpc-?iv\b', r'\bpc-?4\b', r'\bproforma-?iv\b', r'\bproforma-?4\b'],
        "PC-V": [r'\bpc-?v\b', r'\bpc-?5\b', r'\bproforma-?v\b', r'\bproforma-?5\b'],
    }
    
    for proforma, patterns in proforma_patterns.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            return proforma
    
    return None


def extract_section_title(text: str) -> Optional[str]:
    """Extract section/chapter title if present at start of text."""
    lines = text.split('\n')
    if not lines:
        return None
    
    first_line = lines[0].strip()
    
    # Check if first line looks like a heading
    if len(first_line) < 100 and (
        first_line.isupper() or 
        re.match(r'^\d+\.', first_line) or
        re.match(r'^(chapter|section|article)\s+\d+', first_line.lower())
    ):
        return first_line
    
    return None


def create_chunk_metadata(text: str, page: int) -> ChunkMetadata:
    """Create comprehensive metadata for a chunk.
    
    FIX: Adds all metadata needed for intelligent filtering.
    """
    chunk_type = classify_chunk_type(text, page)
    proforma = detect_proforma_type(text)
    section_title = extract_section_title(text)
    
    return ChunkMetadata(
        text=text,
        page=page,
        chunk_type=chunk_type,
        proforma=proforma,
        section_title=section_title,
        is_annexure=(chunk_type in ["annexure", "appendix"]),
        is_table=(chunk_type == "table"),
        is_checklist=(chunk_type == "checklist"),
        chapter=None,
    )


# ============================================================================
# PDF INGESTION WITH ENHANCED CHUNKING (FIX #2)
# ============================================================================

def _read_pdf_pages(pdf_path: str) -> List[str]:
    """Extract text from PDF pages."""
    pages: List[str] = []
    if PdfReader is not None:
        reader = PdfReader(pdf_path)
        for pg in reader.pages:
            try:
                txt = pg.extract_text() or ""
            except Exception:
                txt = ""
            pages.append(txt)
    return pages


def _split_into_chunks(text: str, chunk_size: int = 600, chunk_overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks for better context preservation.
    
    FIX #2: Improved chunking strategy (600 chars with 100 overlap).
    Previous: Simple sentence splitting
    Now: Sentence-aware overlapping chunks
    """
    if not text or len(text) < chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings within last 100 chars
            search_zone = text[max(start, end - 100):end + 50]
            sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', search_zone)]
            
            if sentence_endings:
                # Use last sentence ending
                end = max(start, end - 100) + sentence_endings[-1]
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 30:  # Skip tiny chunks
            chunks.append(chunk)
        
        # Move start forward with overlap
        start = end - chunk_overlap
        
        # Prevent infinite loop
        if start <= 0 or start >= len(text):
            break
    
    return chunks


def _connect_qdrant(url: str):
    """Connect to Qdrant instance."""
    return QdrantClient(url=url)  # type: ignore[misc]


def ingest_pdf_sentence_level(
    pdf_path: str, 
    qdrant_url: str = "http://localhost:6333"
) -> int:
    """Ingest PDF with enhanced chunking and metadata tagging.
    
    CRITICAL IMPROVEMENTS:
    - Chunk classification (main_manual vs annexure vs checklist)
    - Metadata tagging (proforma, section_title, chunk_type)
    - Improved chunking (600 chars with 100 overlap)
    - Filtering of tiny chunks (<30 chars)
    
    Returns: Number of chunks inserted
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(pdf_path)

    pages = _read_pdf_pages(pdf_path)
    if not pages:
        return 0

    # Check dependencies are actually loaded
    if SentenceTransformer is None:
        raise RuntimeError("SentenceTransformer not loaded - sentence-transformers import failed")
    if QdrantClient is None:
        raise RuntimeError("QdrantClient not loaded - qdrant-client import failed")
    if VectorParams is None or Distance is None or PointStruct is None:
        raise RuntimeError("Qdrant models not loaded - qdrant-client.http.models import failed")

    # Initialize models
    model = SentenceTransformer(EMBED_MODEL)
    dim = int(model.get_sentence_embedding_dimension() or 384)
    client = _connect_qdrant(qdrant_url)

    # Ensure collection exists
    try:
        client.get_collection(COLLECTION)
    except Exception:
        client.recreate_collection(
            COLLECTION, 
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
        )

    points: List[PointStruct] = []  # type: ignore[valid-type]
    pid = 1
    
    for page_idx, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue
        
        # Split page into overlapping chunks
        chunks = _split_into_chunks(page_text, chunk_size=600, chunk_overlap=100)
        
        for chunk_text in chunks:
            if len(chunk_text) < 30:  # Skip tiny chunks
                continue
            
            # Create metadata
            metadata = create_chunk_metadata(chunk_text, page_idx)
            
            # Encode chunk
            vec = model.encode([chunk_text], normalize_embeddings=True)[0]
            
            # Prepare payload with ALL metadata
            payload = {
                "text": chunk_text,
                "page": page_idx,
                "chunk_type": metadata.chunk_type,
                "proforma": metadata.proforma,
                "section_title": metadata.section_title,
                "is_annexure": metadata.is_annexure,
                "is_table": metadata.is_table,
                "is_checklist": metadata.is_checklist,
            }
            
            points.append(PointStruct(id=pid, vector=vec.tolist(), payload=payload))
            pid += 1

    if points:
        client.upsert(COLLECTION, points)
    
    if DEBUG_MODE:
        # Show distribution of chunk types
        type_counts: Dict[str, int] = {}
        for p in points:
            payload = p.payload or {}
            chunk_type = payload.get("chunk_type", "unknown")
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        print(f"[DEBUG] Ingested {len(points)} chunks: {type_counts}")
    
    return len(points)


# ============================================================================
# INTELLIGENT RETRIEVAL WITH FILTERING (FIX #3)
# ============================================================================

def should_exclude_chunk(chunk: Dict[str, Any], question: str) -> Tuple[bool, str]:
    """Determine if chunk should be excluded based on question type.
    
    CRITICAL FIX #3: Prevents annexure/checklist contamination.
    
    Returns: (should_exclude: bool, reason: str)
    """
    chunk_type = chunk.get("chunk_type", "main_manual")
    text = chunk.get("text", "").lower()
    question_lower = question.lower()
    
    # === QUESTION ANALYSIS ===
    is_conceptual = any(word in question_lower for word in [
        "what is", "explain", "describe", "define", "how does",
        "process", "procedure", "difference between", "concept",
        "purpose", "objective", "meaning", "required", "mandatory"
    ])
    
    is_specific_query = any(word in question_lower for word in [
        "form", "format", "template", "annexure", "checklist", "table",
        "attachment", "appendix"
    ])
    
    # === EXCLUSION LOGIC ===
    
    # Rule 1: ALWAYS exclude checklists for conceptual questions
    if is_conceptual and chunk.get("is_checklist"):
        return (True, "Checklist excluded for conceptual question")
    
    # Rule 2: ALWAYS exclude annexures for conceptual questions
    if is_conceptual and chunk.get("is_annexure"):
        return (True, "Annexure excluded for conceptual question")
    
    # Rule 3: Exclude tables unless specifically asked
    if chunk.get("is_table") and not is_specific_query:
        if not any(word in question_lower for word in ["table", "limit", "threshold", "amount", "cost"]):
            return (True, "Table excluded (not requested)")
    
    # Rule 4: Detect repetitive checklist patterns
    checklist_patterns = [
        "n/a yes no",
        "inclusion of",
        "s. no.",
        "item checked",
        "✓",
        "inspection item",
    ]
    if any(pattern in text for pattern in checklist_patterns):
        if is_conceptual:
            return (True, "Checklist pattern detected in conceptual query")
    
    # Rule 5: Exclude if chunk is mostly numbers/acronyms (likely table/annexure)
    words = chunk.get("text", "").split()
    if len(words) > 10:
        upper_count = sum(1 for w in words if len(w) > 2 and w.isupper())
        number_count = sum(1 for w in words if w.isdigit())
        
        if (upper_count / len(words)) > 0.3:
            return (True, "Too many acronyms (likely acronym list)")
        
        if (number_count / len(words)) > 0.3:
            return (True, "Too many numbers (likely table)")
    
    return (False, "Passed all filters")


def filter_chunks_by_rules(
    chunks: List[Dict[str, Any]], 
    question: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filter chunks using exclusion rules.
    
    Returns: (filtered_chunks, excluded_chunks_with_reasons)
    """
    filtered = []
    excluded = []
    
    for chunk in chunks:
        should_exclude, reason = should_exclude_chunk(chunk, question)
        
        if should_exclude:
            chunk_copy = chunk.copy()
            chunk_copy["exclusion_reason"] = reason
            excluded.append(chunk_copy)
        else:
            filtered.append(chunk)
    
    if DEBUG_MODE:
        print(f"[DEBUG] Filtered {len(chunks)} → {len(filtered)} chunks ({len(excluded)} excluded)")
        if excluded:
            for ex in excluded[:3]:
                print(f"  - Excluded: {ex['exclusion_reason']} | Type: {ex.get('chunk_type')}")
    
    return filtered, excluded


# ============================================================================
# CROSS-ENCODER SEMANTIC RERANKING (FIX #4 - GAME CHANGER)
# ============================================================================

_reranker_cache = None

def get_reranker() -> Optional[CrossEncoder]:  # type: ignore[valid-type]
    """Get or initialize the cross-encoder reranker model."""
    global _reranker_cache
    if _reranker_cache is None:
        try:
            _reranker_cache = CrossEncoder(RERANKER_MODEL)  # type: ignore[misc]
            if DEBUG_MODE:
                print(f"[DEBUG] Loaded reranker: {RERANKER_MODEL}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Failed to load reranker: {e}")
            # Fallback: return None and skip reranking
            return None
    return _reranker_cache


def rerank_with_cross_encoder(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Rerank chunks using cross-encoder for superior relevance.
    
    CRITICAL FIX #4: Semantic reranking drastically improves precision.
    Input: 20-60 chunks → Output: Top 3 most relevant
    
    Cross-encoder evaluates (query, chunk) pairs together, giving much better
    relevance scores than embedding-only retrieval.
    """
    if not chunks:
        return []
    
    reranker = get_reranker()
    if reranker is None:
        # Fallback: use embedding scores
        return sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    
    # Prepare pairs for cross-encoder
    pairs = [[query, chunk.get("text", "")] for chunk in chunks]
    
    # Get reranker scores
    try:
        scores = reranker.predict(pairs)
        
        # Attach scores to chunks
        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score) if score is not None else 0.0
        
        # Sort by rerank score (descending)
        ranked = sorted(chunks, key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        if DEBUG_MODE:
            print(f"[DEBUG] Reranked {len(chunks)} chunks → top {top_k}")
            for i, chunk in enumerate(ranked[:top_k], 1):
                print(f"  #{i} Score: {chunk['rerank_score']:.3f} | Page: {chunk.get('page')} | Type: {chunk.get('chunk_type')}")
        
        return ranked[:top_k]
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Reranking failed: {e}, falling back to embedding scores")
        # Fallback
        return sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]


# ============================================================================
# MAIN SEARCH FUNCTION (FIX #5 - ORCHESTRATION)
# ============================================================================

def search_sentences(
    query: str,
    top_k: int = 3,  # REDUCED from 60 to 3 (after reranking)
    qdrant_url: str = "http://localhost:6333",
    mmr: bool = False,
    lambda_mult: float = 0.7,
    min_score: float = 0.05,
    enable_reranking: bool = True,
    enable_filtering: bool = True,
) -> List[Dict[str, Any]]:
    """Enterprise-grade search with filtering and reranking.
    
    CRITICAL FLOW:
    1. Initial retrieval: Get 20 chunks from Qdrant
    2. Filter: Remove annexure/checklist if conceptual question
    3. Rerank: Use cross-encoder to get top 3 most relevant
    4. Return: Final 3 chunks for LLM
    
    Args:
        query: User question
        top_k: Final number of chunks to return (default 3)
        enable_reranking: Use cross-encoder (recommended: True)
        enable_filtering: Apply exclusion rules (recommended: True)
    """
    # Check dependencies are actually loaded
    if SentenceTransformer is None or QdrantClient is None:
        raise RuntimeError("RAG dependencies not properly loaded. Please restart the application.")
    
    # Step 1: Initial retrieval (get 20 candidates)
    initial_k = 20  # Cast wider net initially
    
    model = SentenceTransformer(EMBED_MODEL)
    qvec = model.encode([query], normalize_embeddings=True)[0]
    client = _connect_qdrant(qdrant_url)

    try:
        results = client.search(
            collection_name=COLLECTION,
            query_vector=qvec.tolist(),
            limit=initial_k
        )
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Qdrant search failed: {e}")
        return []
    
    # Convert to dict format
    chunks: List[Dict[str, Any]] = []
    for r in results:
        payload = r.payload or {}
        
        # Calculate score (convert distance to similarity)
        dist = getattr(r, "distance", None)
        if dist is None:
            dist = 1.0 - float(getattr(r, "score", 0.0))
        score = 1.0 - float(dist)
        
        if score < min_score:
            continue
        
        chunk = {
            "text": payload.get("text", ""),
            "page": payload.get("page"),
            "score": score,
            "chunk_type": payload.get("chunk_type", "main_manual"),
            "proforma": payload.get("proforma"),
            "is_annexure": payload.get("is_annexure", False),
            "is_table": payload.get("is_table", False),
            "is_checklist": payload.get("is_checklist", False),
            "section_title": payload.get("section_title"),
            "source": COLLECTION,
        }
        chunks.append(chunk)
    
    if DEBUG_MODE:
        print(f"[DEBUG] Initial retrieval: {len(chunks)} chunks")
    
    # Step 2: Filter annexure/checklist if needed
    if enable_filtering:
        chunks, excluded = filter_chunks_by_rules(chunks, query)
    
    # Step 3: Rerank with cross-encoder
    if enable_reranking and chunks:
        chunks = rerank_with_cross_encoder(query, chunks, top_k=top_k)
    else:
        # Fallback: just take top_k by embedding score
        chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    
    return chunks


# ============================================================================
# POST-GENERATION GUARDRAILS (FIX #6)
# ============================================================================

def detect_annexure_leakage(answer: str) -> Tuple[bool, List[str]]:
    """Detect if LLM output contains annexure/checklist contamination.
    
    CRITICAL FIX #6: Last line of defense against leakage.
    
    Returns: (has_leakage: bool, detected_patterns: List[str])
    """
    patterns = {
        "checklist_markers": [r"N/A\s+Yes\s+No", r"✓\s*checked", r"Item\s+\d+:", r"S\.\s*No\."],
        "annexure_refs": [r"Annexure-?[A-Z0-9]+", r"Annex-?[A-Z0-9]+", r"Appendix-?[A-Z0-9]+"],
        "table_rows": [r"(\d+\.\s+.{10,50}\s*){4,}"],  # Repetitive numbered rows
        "inspection_items": [r"Inclusion of.{20,80}(Yes|No|N/A)", r"inspection item \d+"],
    }
    
    detected = []
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, answer, re.IGNORECASE):
                detected.append(f"{category}: {pattern}")
    
    return (len(detected) > 0, detected)


def apply_guardrails(answer: str, original_question: str) -> Tuple[str, bool]:
    """Apply post-generation guardrails to filter annexure leakage.
    
    Returns: (cleaned_answer: str, needs_regeneration: bool)
    """
    has_leakage, patterns = detect_annexure_leakage(answer)
    
    if has_leakage:
        if DEBUG_MODE:
            print(f"[DEBUG] GUARDRAIL TRIGGERED! Detected patterns: {patterns}")
        
        # Return flag to trigger regeneration
        return (answer, True)
    
    return (answer, False)


# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

def dedup_chunks(candidates: List[Dict[str, Any]], min_chars: int = 28) -> List[Dict[str, Any]]:
    """Remove near-duplicate chunks by normalized text key."""
    out: List[Dict[str, Any]] = []
    seen = set()
    for c in candidates or []:
        t = (c.get("text") or "").strip()
        if not t or len(t) < min_chars:
            continue
        key = " ".join(t.lower().split())
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def mmr_rerank(
    candidates: List[Dict[str, Any]], 
    top_k: int = 6, 
    lambda_mult: float = 0.5
) -> List[Dict[str, Any]]:
    """Maximal Marginal Relevance rerank (legacy compatibility).
    
    NOTE: Cross-encoder reranking is now preferred (see rerank_with_cross_encoder).
    """
    items = [c for c in candidates or [] if (c.get("text") or "").strip()]
    if not items:
        return []
    
    texts = [c.get("text", "") for c in items]
    model = SentenceTransformer(EMBED_MODEL)  # type: ignore[misc]
    vecs = model.encode(texts, normalize_embeddings=True)
    
    def cos(a, b):
        return sum(x*y for x, y in zip(a, b))
    
    selected = []
    rest = list(range(len(items)))
    
    if rest:
        selected.append(rest.pop(0))
    
    while rest and len(selected) < max(1, int(top_k)):
        best_idx = None
        best_val = -1e9
        
        for j in rest:
            sim_to_query = cos(vecs[j], vecs[selected[0]])
            max_sim_sel = max(cos(vecs[j], vecs[s]) for s in selected)
            mmr = lambda_mult * sim_to_query - (1 - lambda_mult) * max_sim_sel
            
            if mmr > best_val:
                best_val = mmr
                best_idx = j
        
        if best_idx is None:
            break
        
        selected.append(best_idx)
        rest.remove(best_idx)
    
    return [items[i] for i in selected]


def build_context(hits: List[Dict[str, Any]], token_budget: int = 2400) -> Dict[str, Any]:
    """Build context string from ranked hits within token budget.
    
    Returns: {"context": str, "citations": List[Dict]}
    """
    def est_tokens(s: str) -> int:
        if not s:
            return 0
        return max(len(s) // 4, int(len(s.split()) * 0.75))

    context_parts: List[str] = []
    citations: List[Dict[str, Any]] = []
    used = 0
    n = 1
    
    for h in hits or []:
        t = (h.get("text") or "").strip()
        if not t:
            continue
        
        extra = est_tokens(t) + 4
        if used + extra > token_budget:
            break
        
        context_parts.append(f"[{n}] {t}")
        citations.append({
            "n": n,
            "page": h.get("page"),
            "title": h.get("title"),
            "text": t,
            "chunk_type": h.get("chunk_type"),
        })
        used += extra
        n += 1
    
    return {"context": "\n\n".join(context_parts), "citations": citations}


def filter_acronym_pages(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy filter for acronym pages (now handled by chunk classification)."""
    # This is now redundant due to classify_chunk_type, but kept for compatibility
    filtered = []
    for h in hits:
        text = h.get("text", "")
        if not text:
            continue
        
        words = text.split()
        if not words:
            continue
        
        upper_count = sum(1 for w in words if len(w) > 2 and w.isupper())
        acronym_ratio = upper_count / len(words) if words else 0.0
        
        if acronym_ratio >= 0.3:
            continue
        
        filtered.append(h)
    
    return filtered


# ============================================================================
# DIAGNOSTIC UTILITIES
# ============================================================================

def diagnose_retrieval(
    query: str,
    qdrant_url: str = "http://localhost:6333"
) -> Dict[str, Any]:
    """Diagnostic tool to inspect retrieval pipeline.
    
    Usage:
        from src.rag_langchain import diagnose_retrieval
        results = diagnose_retrieval("What is CHIRA?")
        print(results)
    """
    print(f"\n{'='*70}")
    print(f"RETRIEVAL DIAGNOSTIC FOR: {query}")
    print(f"{'='*70}\n")
    
    # Get chunks with all metadata
    chunks = search_sentences(query, top_k=5, qdrant_url=qdrant_url)
    
    print(f"📊 Retrieved {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Chunk #{i} ---")
        print(f"  Page: {chunk.get('page')}")
        print(f"  Type: {chunk.get('chunk_type')}")
        print(f"  Score: {chunk.get('score', 0):.3f}")
        print(f"  Rerank: {chunk.get('rerank_score', 0):.3f}")
        print(f"  Proforma: {chunk.get('proforma', 'N/A')}")
        print(f"  Is Annexure: {chunk.get('is_annexure')}")
        print(f"  Is Checklist: {chunk.get('is_checklist')}")
        print(f"  Text: {chunk.get('text', '')[:150]}...")
        print()
    
    return {"query": query, "chunks": chunks, "count": len(chunks)}


if __name__ == "__main__":
    # Quick test
    print("✅ Enterprise RAG Pipeline Loaded Successfully!")
    print(f"📦 Embedding Model: {EMBED_MODEL}")
    print(f"🔁 Reranker Model: {RERANKER_MODEL}")
    print(f"💾 Collection: {COLLECTION}")
    print(f"🐛 Debug Mode: {DEBUG_MODE}")

