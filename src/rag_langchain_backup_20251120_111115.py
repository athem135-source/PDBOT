"""
Lightweight RAG helpers for sentence-level PDF ingestion and search using
Sentence-Transformers + Qdrant. Minimal dependencies so the app loads reliably.

Requirements (installed in the project venv):
- sentence-transformers
- qdrant-client
- pypdf (optional; used here for PDF page text extraction)
"""
from __future__ import annotations

import os
import re
import warnings
from typing import List, Dict, Any

# Suppress Keras compatibility warnings from sentence-transformers
warnings.filterwarnings("ignore", message=".*Keras.*")
warnings.filterwarnings("ignore", message=".*keras.*")

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"sentence-transformers missing: {e}")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"qdrant-client missing: {e}")

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None  # type: ignore

# Public constants used by the app
COLLECTION = os.getenv("PNDBOT_RAG_COLLECTION", "pnd_manual_sentences")
EMBED_MODEL = os.getenv("PNDBOT_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def _read_pdf_pages(pdf_path: str) -> List[str]:
    pages: List[str] = []
    if PdfReader is not None:
        reader = PdfReader(pdf_path)
        for pg in reader.pages:
            try:
                txt = pg.extract_text() or ""
            except Exception:
                txt = ""
            pages.append(txt)
    # else: leave pages empty; the app also has its own loader for Exact mode
    return pages


def _split_sentences(text: str) -> List[str]:
    # Lightweight split to avoid NLTK dependency here (the app can use NLTK separately)
    text = text.replace("\r", " ").replace("\n", " ")
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s and len(s.strip()) > 0]


def _connect_qdrant(url: str) -> QdrantClient:
    return QdrantClient(url=url)


def detect_proforma_type(text: str) -> str | None:
    """Detect which PC proforma this text relates to.
    
    CRITICAL FIX #6: Tag chunks with proforma metadata for better retrieval accuracy.
    Returns proforma identifier (PC-I, PC-II, etc.) or None.
    """
    text_lower = text.lower()
    
    # Check for PC-I variants
    if any(term in text_lower for term in ["pc-i ", "pc-1 ", "pc i ", "pc1 ", "pc-i:", "pc-i.", "pc-i,"]):
        return "PC-I"
    
    # Check for PC-II variants
    if any(term in text_lower for term in ["pc-ii ", "pc-2 ", "pc ii ", "pc2 ", "pc-ii:", "pc-ii.", "pc-ii,"]):
        return "PC-II"
    
    # Check for PC-III variants
    if any(term in text_lower for term in ["pc-iii ", "pc-3 ", "pc iii ", "pc3 ", "pc-iii:", "pc-iii.", "pc-iii,"]):
        return "PC-III"
    
    # Check for PC-IV variants
    if any(term in text_lower for term in ["pc-iv ", "pc-4 ", "pc iv ", "pc4 ", "pc-iv:", "pc-iv.", "pc-iv,"]):
        return "PC-IV"
    
    # Check for PC-V variants
    if any(term in text_lower for term in ["pc-v ", "pc-5 ", "pc v ", "pc5 ", "pc-v:", "pc-v.", "pc-v,"]):
        return "PC-V"
    
    return None


def ingest_pdf_sentence_level(pdf_path: str, qdrant_url: str = "http://localhost:6338") -> int:
    """Ingest a PDF into Qdrant as sentence-level chunks.

    Returns the number of inserted points.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(pdf_path)

    pages = _read_pdf_pages(pdf_path)
    if not pages:
        # Nothing to index; let the app still work with Exact mode
        return 0

    model = SentenceTransformer(EMBED_MODEL)
    dim_v = model.get_sentence_embedding_dimension()
    dim = int(dim_v or 384)
    client = _connect_qdrant(qdrant_url)

    # Ensure collection exists
    try:
        client.get_collection(COLLECTION)
    except Exception:
        client.recreate_collection(COLLECTION, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

    points: List[PointStruct] = []
    pid = 1
    for page_idx, page_text in enumerate(pages, start=1):
        sents = _split_sentences(page_text)
        if not sents:
            continue
        vecs = model.encode(sents, normalize_embeddings=True)
        for s, v in zip(sents, vecs):
            # CRITICAL FIX #6: Add proforma metadata to payload
            proforma = detect_proforma_type(s)
            payload = {"text": s, "page": page_idx, "proforma": proforma}
            points.append(PointStruct(id=pid, vector=v.tolist(), payload=payload))
            pid += 1

    if points:
        client.upsert(COLLECTION, points)
    return len(points)


def filter_acronym_pages(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove pages that are mostly acronym definitions or proforma title pages.
    
    CRITICAL FIX #1: Prevents acronym list pollution (e.g., Q13 returning acronym page instead of content).
    """
    filtered = []
    for h in hits:
        text = h.get("text", "")
        if not text:
            continue
        
        words = text.split()
        if not words:
            continue
        
        # Count uppercase words >2 chars (likely acronyms like "CDWP", "PC-I")
        upper_count = sum(1 for w in words if len(w) > 2 and w.isupper())
        acronym_ratio = upper_count / len(words) if words else 0.0
        
        # Skip if >30% acronyms (acronym list page)
        if acronym_ratio >= 0.3:
            continue
        
        # Skip proforma title pages (e.g., "Planning Commission Proforma I - 2024")
        text_lower = text.lower()
        if "proforma i - 2024" in text_lower or "proforma ii - 2024" in text_lower:
            continue
        if "proforma iii - 2024" in text_lower or "proforma iv - 2024" in text_lower:
            continue
        if "proforma v - 2024" in text_lower:
            continue
        
        filtered.append(h)
    
    return filtered


def search_sentences(
    query: str,
    top_k: int = 6,
    qdrant_url: str = "http://localhost:6338",
    mmr: bool | None = None,  # kept for API compatibility; not used in this minimal impl
    lambda_mult: float | None = None,  # kept for API compatibility
    min_score: float | None = None,
) -> List[Dict[str, Any]]:
    """Search top sentences for a query. Returns list of dicts with text/page/score.

    Note: Qdrant returns distance; we convert to cosine similarity score = 1 - distance.
    """
    model = SentenceTransformer(EMBED_MODEL)
    qvec = model.encode([query], normalize_embeddings=True)[0]
    client = _connect_qdrant(qdrant_url)

    res = client.search(collection_name=COLLECTION, query_vector=qvec.tolist(), limit=int(top_k or 6))
    out: List[Dict[str, Any]] = []
    for r in res:
        payload = r.payload or {}
        text = payload.get("text", "")
        page = payload.get("page")
        # qdrant-client v1 uses 'score', older uses 'distance'
        dist = getattr(r, "distance", None)
        if dist is None:
            dist = float(1.0 - float(getattr(r, "score", 0.0)))  # invert if only score present
            score = 1.0 - dist
        else:
            score = 1.0 - float(dist)
        if (min_score is None) or (score >= float(min_score)):
            out.append({"text": text, "page": page, "score": score, "source": COLLECTION})
    
    # CRITICAL FIX #1: Filter acronym pages before returning
    out = filter_acronym_pages(out)
    return out


# --- Generative Mode helpers: diversity + context budgeting ---
def _embed_texts(texts: List[str]) -> List[List[float]]:
    model = SentenceTransformer(EMBED_MODEL)
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def dedup_chunks(candidates: List[Dict[str, Any]], min_chars: int = 28) -> List[Dict[str, Any]]:
    """Remove near-duplicate chunks by normalized text key; keep first occurrence.

    Accepts items with at least keys: text, page.
    """
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


def mmr_rerank(candidates: List[Dict[str, Any]], top_k: int = 6, lambda_mult: float = 0.5) -> List[Dict[str, Any]]:
    """Maximal Marginal Relevance rerank over initial semantic candidates.

    - Selects diverse set of up to top_k items.
    - Uses cosine similarity on sentence-transformer embeddings.
    """
    items = [c for c in candidates or [] if (c.get("text") or "").strip()]
    if not items:
        return []
    texts = [c.get("text", "") for c in items]
    vecs = _embed_texts(texts)
    import math
    def cos(a, b):
        # assume normalized by encode(normalize_embeddings=True)
        return sum(x*y for x, y in zip(a, b))
    # Use first N as query proxies by initial score, otherwise first item
    # For simplicity, treat the first item as the most relevant seed.
    selected = []
    rest = list(range(len(items)))
    if not rest:
        return []
    selected.append(rest.pop(0))
    while rest and len(selected) < max(1, int(top_k)):
        best_idx = None
        best_val = -1e9
        for j in rest:
            sim_to_query = 0.0
            # proxy: similarity to the first selected (seed)
            sim_to_query = cos(vecs[j], vecs[selected[0]])
            max_sim_sel = max(cos(vecs[j], vecs[s]) for s in selected) if selected else 0.0
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
    """Build a single context string from ranked hits within a token budget.

    Returns dict { context: str, citations: List[Dict] } where citations are
    [{n: 1, page: 12, title: None, text: '...'}]. Each chunk is tagged with [n].
    """
    def est_tokens(s: str) -> int:
        # crude: ~4 chars per token or 0.75 words
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
        citations.append({"n": n, "page": h.get("page"), "title": h.get("title"), "text": t})
        used += extra
        n += 1
    return {"context": "\n\n".join(context_parts), "citations": citations}

