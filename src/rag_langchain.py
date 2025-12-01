"""
PDBot RAG Pipeline v3.2.0 (v2.1.0)
Sentence-level chunking, strict reranking, numeric boost.
Multi-class classifier integration for retrieval optimization.
Groq for reranking fallback.
Zero hardcoding. All answers from PDF only.
"""
from __future__ import annotations

import os
import re
import warnings
import logging
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

DEBUG_MODE = os.getenv("PNDBOT_DEBUG", "False").lower() == "true"

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6338")

# Groq API for reranking (NOT for generation)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_RERANK_MODEL = os.getenv("GROQ_RERANK_MODEL", "llama-3.1-8b-instant")

# Imports with type: ignore for optional dependencies
SENTENCE_TRANSFORMERS_AVAILABLE = False
QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    CrossEncoder = None  # type: ignore

try:
    from qdrant_client import QdrantClient  # type: ignore
    from qdrant_client.http.models import Distance, VectorParams, PointStruct  # type: ignore
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None  # type: ignore
    Distance = None  # type: ignore
    VectorParams = None  # type: ignore
    PointStruct = None  # type: ignore

try:
    from pypdf import PdfReader  # type: ignore
except ImportError:
    PdfReader = None  # type: ignore

# Config
COLLECTION = os.getenv("PNDBOT_RAG_COLLECTION", "pnd_manual_v3")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_embedder_cache = None
_reranker_cache = None


def get_embedder():
    """Get or initialize the embedding model."""
    global _embedder_cache
    if _embedder_cache is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            _embedder_cache = SentenceTransformer(EMBED_MODEL)  # type: ignore[misc]
        except Exception:
            pass
    return _embedder_cache


def get_reranker():
    """Get or initialize the cross-encoder reranker."""
    global _reranker_cache
    if _reranker_cache is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            _reranker_cache = CrossEncoder(RERANKER_MODEL)  # type: ignore[misc]
        except Exception:
            pass
    return _reranker_cache


def _read_pdf_pages(pdf_path: str) -> List[str]:
    """Extract text from PDF pages."""
    pages = []
    
    # Try PyMuPDF first
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            pages.append(doc.load_page(i).get_text("text") or "")
        doc.close()
        return pages
    except Exception:
        pass
    
    # Fallback to pypdf
    if PdfReader:
        try:
            reader = PdfReader(pdf_path)
            for pg in reader.pages:
                pages.append(pg.extract_text() or "")
        except Exception:
            pass
    
    return pages


def _clean_text(text: str) -> str:
    """Remove headers, footers, page numbers, garbage."""
    lines = text.split("\n")
    cleaned = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip page headers/footers
        if re.match(r"^(Page\s+)?\d+(\s+of\s+\d+)?$", line, re.IGNORECASE):
            continue
        if re.match(r"^Manual for Development Projects", line, re.IGNORECASE):
            continue
        if re.match(r"^Planning Commission", line, re.IGNORECASE):
            continue
        
        # Skip table/figure/annexure titles
        if re.match(r"^(Table|Figure|Annexure|Appendix)\s+[\d\w\-]+", line, re.IGNORECASE):
            continue
        
        # Skip numeric-only garbage
        if re.match(r"^[\d\s\.,\-\(\)]+$", line):
            continue
        
        cleaned.append(line)
    
    return " ".join(cleaned)


def _split_into_chunks(text: str) -> List[str]:
    """
    Sentence-level chunking: 40-55 words per chunk.
    Never breaks mid-sentence. Uses NLTK tokenizer.
    """
    text = _clean_text(text)
    if not text or len(text) < 20:
        return []
    
    # Sentence tokenization
    try:
        import nltk
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt", quiet=True)
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
    except Exception:
        # Fallback regex
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    
    # Recombine into 40-55 word chunks
    chunks = []
    buffer = []
    word_count = 0
    
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        
        sent_words = len(sent.split())
        
        # If adding this sentence exceeds 55 words and we have content
        if word_count + sent_words > 55 and word_count >= 40:
            chunk_text = " ".join(buffer).strip()
            if chunk_text:
                chunks.append(chunk_text)
            buffer = []
            word_count = 0
        
        buffer.append(sent)
        word_count += sent_words
        
        # If we're in the sweet spot, finalize
        if 40 <= word_count <= 55:
            chunk_text = " ".join(buffer).strip()
            if chunk_text:
                chunks.append(chunk_text)
            buffer = []
            word_count = 0
    
    # Remaining buffer
    if buffer:
        chunk_text = " ".join(buffer).strip()
        if chunk_text and len(chunk_text.split()) >= 5:
            chunks.append(chunk_text)
    
    return chunks


def ingest_pdf_sentence_level(
    pdf_path: str,
    qdrant_url: str = None
) -> int:
    """Ingest PDF with sentence-level chunking."""
    if qdrant_url is None:
        qdrant_url = QDRANT_URL
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(pdf_path)
    
    pages = _read_pdf_pages(pdf_path)
    if not pages:
        return 0
    
    model = get_embedder()
    if model is None:
        raise RuntimeError("Embedding model not available")
    
    dim = model.get_sentence_embedding_dimension() or 384
    client = QdrantClient(url=qdrant_url)  # type: ignore[misc]
    
    # Recreate collection
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    
    client.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE)  # type: ignore[misc]
    )
    
    points = []
    pid = 1
    
    for page_idx, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue
        
        chunks = _split_into_chunks(page_text)
        
        for chunk_text in chunks:
            words = chunk_text.split()
            # Filter: reject <5 or >130 words
            if len(words) < 5 or len(words) > 130:
                continue
            
            vec = model.encode([chunk_text], normalize_embeddings=True)[0]
            
            payload = {
                "text": chunk_text,
                "page": page_idx,
                "word_count": len(words),
            }
            
            points.append(PointStruct(id=pid, vector=vec.tolist(), payload=payload))  # type: ignore[misc]
            pid += 1
    
    if points:
        batch_size = 100
        for i in range(0, len(points), batch_size):
            client.upsert(COLLECTION, points[i:i+batch_size])
    
    if DEBUG_MODE:
        print(f"[DEBUG] Ingested {len(points)} chunks from {len(pages)} pages")
    
    return len(points)


def search_sentences(
    query: str,
    top_k: int = 2,
    qdrant_url: str = None,
    min_score: float = 0.12,
    retrieval_hints: Optional[Dict[str, Any]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    v2.1.0 Retrieval pipeline with classifier hints:
    1. Initial retrieval: 40 chunks from Qdrant
    2. Post-filter: reject <5 or >130 words
    3. Numeric boost: +0.25 for Rs/million/billion/cost/approval/allocation
    4. Query-number boost: +0.15 if query has numbers and chunk has numbers
    5. Classification hints: boost chunks matching query type
    6. Reranker: keep TOP 2 with score >= 0.32
    7. Groq rerank fallback if cross-encoder fails
    8. Fallback: if none survive, use highest vector chunk
    
    Args:
        query: Search query
        top_k: Number of results to return
        qdrant_url: Qdrant server URL
        min_score: Minimum vector similarity score
        retrieval_hints: Optional hints from classifier (boost_numeric, prefer_procedures, etc.)
    """
    if qdrant_url is None:
        qdrant_url = QDRANT_URL
    retrieval_hints = retrieval_hints or {}
    
    model = get_embedder()
    if model is None:
        raise RuntimeError("Embedding model not available")
    
    qvec = model.encode([query], normalize_embeddings=True)[0]
    
    try:
        client = QdrantClient(url=qdrant_url)  # type: ignore[misc]
    except Exception as e:
        raise RuntimeError(f"Cannot connect to Qdrant: {e}")
    
    # Step 1: Initial retrieval (40 candidates)
    try:
        results = client.search(
            collection_name=COLLECTION,
            query_vector=qvec.tolist(),
            limit=40
        )
    except Exception as e:
        raise RuntimeError(f"Qdrant search failed: {e}")
    
    chunks = []
    fallback_chunk = None
    
    # Check if query contains numbers
    query_has_numbers = bool(re.search(r'\d+', query))
    
    for r in results:
        payload = r.payload or {}
        score = float(r.score) if hasattr(r, 'score') else 0.0
        
        text = payload.get("text", "")
        page = payload.get("page", 0)
        word_count = len(text.split())
        
        # Store first result as fallback
        if fallback_chunk is None:
            fallback_chunk = {
                "text": text,
                "page": page,
                "score": score,
                "word_count": word_count,
            }
        
        # Filter by min_score
        if score < min_score:
            continue
        
        # Post-filter: reject <5 or >130 words
        if word_count < 5 or word_count > 130:
            continue
        
        chunks.append({
            "text": text,
            "page": page,
            "score": score,
            "word_count": word_count,
        })
    
    if DEBUG_MODE:
        logging.info(f"[RAG] After initial filter: {len(chunks)} chunks")
    
    # Step 2: Numeric boost (+0.25 for key financial/policy terms)
    numeric_patterns = [
        "rs.", "rs ", "rupees", "million", "billion", "crore", "lakh",
        "approval limit", "allocation", "cost", "expenditure", "release",
        "ceiling", "threshold", "budget", "fund"
    ]
    
    # v2.1.0: Procedure/formula/monitoring patterns for classifier hints
    procedure_patterns = ["step", "process", "procedure", "workflow", "approval", "hierarchy", "submit"]
    formula_patterns = ["formula", "calculation", "estimate", "depreciation", "s-curve", "npv", "irr", "bcr"]
    monitoring_patterns = ["kpi", "monitoring", "evaluation", "indicator", "target", "output", "outcome", "m&e"]
    
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        boost = 0.0
        
        # +0.25 for numeric/policy terms
        if any(p in text_lower for p in numeric_patterns):
            boost += 0.25
            chunk["numeric_boosted"] = True
        
        # +0.15 if query has numbers AND chunk has numbers
        if query_has_numbers and re.search(r'\d+', chunk["text"]):
            boost += 0.15
            chunk["number_match"] = True
        
        # v2.1.0: Apply classifier hints
        if retrieval_hints.get("boost_numeric") and chunk.get("numeric_boosted"):
            boost += 0.10  # Extra boost for numeric queries
        
        if retrieval_hints.get("prefer_procedures"):
            if any(p in text_lower for p in procedure_patterns):
                boost += 0.15
                chunk["procedure_match"] = True
        
        if retrieval_hints.get("prefer_formulas"):
            if any(p in text_lower for p in formula_patterns):
                boost += 0.15
                chunk["formula_match"] = True
        
        if retrieval_hints.get("prefer_monitoring"):
            if any(p in text_lower for p in monitoring_patterns):
                boost += 0.15
                chunk["monitoring_match"] = True
        
        if retrieval_hints.get("multi_sentence"):
            # Prefer longer chunks for procedure/formula queries
            if chunk["word_count"] >= 40:
                boost += 0.10
        
        chunk["score"] = min(1.0, chunk["score"] + boost)
    
    # Step 3: Rerank with cross-encoder (keep TOP 2, threshold 0.32)
    reranker = get_reranker()
    rerank_success = False
    
    if reranker and chunks:
        pairs = [[query, c["text"]] for c in chunks]
        try:
            scores = reranker.predict(pairs)
            for chunk, rscore in zip(chunks, scores):
                chunk["rerank_score"] = float(rscore)
            
            # Sort by rerank score
            chunks = sorted(chunks, key=lambda x: x.get("rerank_score", 0), reverse=True)
            
            # Filter by threshold 0.32 and keep top 2
            filtered = [c for c in chunks if c.get("rerank_score", 0) >= 0.32][:top_k]
            
            if filtered:
                chunks = filtered
                rerank_success = True
            elif chunks:
                # Fallback: take highest rerank score chunk
                chunks = [chunks[0]]
                rerank_success = True
            
            if DEBUG_MODE:
                logging.info(f"[RAG] After reranking: {len(chunks)} chunks")
                for i, c in enumerate(chunks):
                    logging.info(f"  #{i+1} rerank={c.get('rerank_score', 0):.3f} page={c.get('page')}")
        
        except Exception as e:
            if DEBUG_MODE:
                logging.warning(f"[RAG] Cross-encoder reranking failed: {e}")
    
    # Step 4: Groq rerank fallback (if cross-encoder failed)
    if not rerank_success and chunks and GROQ_API_KEY:
        try:
            chunks = _groq_rerank(query, chunks, top_k=top_k)
            if DEBUG_MODE:
                logging.info(f"[RAG] Groq rerank: {len(chunks)} chunks")
        except Exception as e:
            if DEBUG_MODE:
                logging.warning(f"[RAG] Groq rerank failed: {e}")
            chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    elif not rerank_success:
        chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    
    # Step 5: Fallback if none survive
    if not chunks and fallback_chunk:
        chunks = [fallback_chunk]
        if DEBUG_MODE:
            logging.info("[RAG] Using fallback chunk (highest vector score)")
    
    return chunks


def _groq_rerank(query: str, chunks: List[Dict[str, Any]], top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Use Groq to score chunk relevance (reranking ONLY, not generation).
    Returns top chunks sorted by relevance score.
    """
    import requests
    
    if not GROQ_API_KEY or not chunks:
        return chunks[:top_k]
    
    # Build reranking prompt
    chunk_texts = "\n\n".join([f"[{i+1}] {c['text'][:300]}" for i, c in enumerate(chunks[:10])])
    
    prompt = f"""Rate the relevance of each text chunk to the query on a scale of 0-10.
Query: {query}

Chunks:
{chunk_texts}

Return ONLY a JSON array of scores, e.g., [8, 5, 9, 3, 7, 2, 6, 4, 1, 0]
No explanation, just the array:"""
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_RERANK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 100,
    }
    
    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse scores
        import json
        scores = json.loads(content.strip())
        
        # Apply scores
        for i, chunk in enumerate(chunks[:len(scores)]):
            chunk["groq_rerank_score"] = float(scores[i]) / 10.0
        
        # Sort and filter
        chunks = sorted(chunks, key=lambda x: x.get("groq_rerank_score", 0), reverse=True)
        filtered = [c for c in chunks if c.get("groq_rerank_score", 0) >= 0.32][:top_k]
        
        return filtered if filtered else [chunks[0]] if chunks else []
    
    except Exception as e:
        logging.warning(f"[RAG] Groq rerank parse error: {e}")
        return chunks[:top_k]


def dedup_chunks(candidates: List[Dict[str, Any]], min_chars: int = 28) -> List[Dict[str, Any]]:
    """Remove near-duplicate chunks."""
    out = []
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
    """MMR rerank (legacy compatibility)."""
    items = [c for c in candidates or [] if (c.get("text") or "").strip()]
    if not items:
        return []
    
    model = get_embedder()
    if model is None:
        return items[:top_k]
    
    texts = [c["text"] for c in items]
    vecs = model.encode(texts, normalize_embeddings=True)
    
    def cos(a, b):
        return sum(x * y for x, y in zip(a, b))
    
    selected = [0]
    rest = list(range(1, len(items)))
    
    while rest and len(selected) < top_k:
        best_idx = None
        best_val = -1e9
        
        for j in rest:
            sim_q = cos(vecs[j], vecs[0])
            max_sel = max(cos(vecs[j], vecs[s]) for s in selected)
            mmr = lambda_mult * sim_q - (1 - lambda_mult) * max_sel
            if mmr > best_val:
                best_val = mmr
                best_idx = j
        
        if best_idx is None:
            break
        selected.append(best_idx)
        rest.remove(best_idx)
    
    return [items[i] for i in selected]


# =============================================================================
# Error Classes (for app.py compatibility)
# =============================================================================
class RetrievalBackendError(Exception):
    """Raised when vector DB or retrieval backend is unavailable."""
    pass


class EmbeddingModelError(Exception):
    """Raised when embedding model fails to load."""
    pass


# =============================================================================
# Context Building (for app.py compatibility)
# =============================================================================
def build_context(
    hits: List[Dict[str, Any]],
    token_budget: int = 2400
) -> Dict[str, Any]:
    """
    Build context string from search hits.
    Returns {"context": str, "citations": list}.
    """
    if not hits:
        return {"context": "", "citations": []}
    
    items = []
    cits = []
    char_budget = token_budget * 4  # rough chars estimate
    total_chars = 0
    
    for i, h in enumerate(hits):
        text = (h.get("text") or "").strip()
        page = h.get("page", 0)
        
        if not text:
            continue
        
        if total_chars + len(text) > char_budget:
            break
        
        items.append(f"[{i+1}] {text}")
        total_chars += len(text)
        cits.append({"n": i + 1, "page": page})
    
    return {"context": "\n\n".join(items).strip(), "citations": cits}
