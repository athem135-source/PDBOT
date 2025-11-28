"""
PDBot RAG Pipeline v3.0.0
Sentence-level chunking, strict reranking, numeric boost.
Zero hardcoding. All answers from PDF only.
"""
from __future__ import annotations

import os
import re
import warnings
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

DEBUG_MODE = os.getenv("PNDBOT_DEBUG", "False").lower() == "true"

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
    qdrant_url: str = "http://localhost:6333"
) -> int:
    """Ingest PDF with sentence-level chunking."""
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
    qdrant_url: str = "http://localhost:6333",
    min_score: float = 0.12,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Retrieval pipeline:
    1. Initial retrieval: 40 chunks from Qdrant
    2. Post-filter: reject <5 or >130 words
    3. Numeric boost: +0.25 for Rs/million/billion/cost/approval
    4. Reranker: keep TOP 2 with score >= 0.30
    5. Fallback: if none survive, use highest vector chunk
    """
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
        print(f"[DEBUG] After initial filter: {len(chunks)} chunks")
    
    # Step 2: Numeric boost (+0.25 for Rs/million/billion/cost/approval)
    numeric_patterns = ["rs.", "rs ", "rupees", "million", "billion", "crore", "lakh", "cost", "approval"]
    
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        if any(p in text_lower for p in numeric_patterns):
            chunk["score"] = min(1.0, chunk["score"] + 0.25)
            chunk["numeric_boosted"] = True
    
    # Step 3: Rerank with cross-encoder (keep TOP 2, threshold 0.30)
    reranker = get_reranker()
    
    if reranker and chunks:
        pairs = [[query, c["text"]] for c in chunks]
        try:
            scores = reranker.predict(pairs)
            for chunk, rscore in zip(chunks, scores):
                chunk["rerank_score"] = float(rscore)
            
            # Sort by rerank score
            chunks = sorted(chunks, key=lambda x: x.get("rerank_score", 0), reverse=True)
            
            # Filter by threshold 0.30 and keep top 2
            filtered = [c for c in chunks if c.get("rerank_score", 0) >= 0.30][:top_k]
            
            if filtered:
                chunks = filtered
            elif chunks:
                # Fallback: take highest rerank score chunk
                chunks = [chunks[0]]
            
            if DEBUG_MODE:
                print(f"[DEBUG] After reranking: {len(chunks)} chunks")
                for i, c in enumerate(chunks):
                    print(f"  #{i+1} rerank={c.get('rerank_score', 0):.3f} page={c.get('page')}")
        
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Reranking failed: {e}")
            chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    else:
        chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    
    # Step 4: Fallback if none survive
    if not chunks and fallback_chunk:
        chunks = [fallback_chunk]
        if DEBUG_MODE:
            print("[DEBUG] Using fallback chunk (highest vector score)")
    
    return chunks


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

