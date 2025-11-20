"""
Answer Generation Logic for PDBOT v0.9.0
=========================================

Handles both Generative and Exact Search answer modes.
"""
from __future__ import annotations

import re
import logging
from typing import Optional

import streamlit as st

# Import RAG functions
try:
    from src.rag_langchain import (
        search_sentences as search,
        dedup_chunks,
        mmr_rerank,
        build_context,
    )
    _RAG_OK = True
except Exception:
    search = None
    def dedup_chunks(candidates):  # type: ignore
        return list(candidates or [])
    def mmr_rerank(candidates, top_k: int = 6, lambda_mult: float = 0.5):  # type: ignore
        try:
            k = int(top_k)
        except Exception:
            k = 6
        return list(candidates or [])[:max(0, k)]
    def build_context(hits, token_budget: int = 2400):  # type: ignore
        items = []
        cits = []
        for i, h in enumerate(list(hits or [])):
            txt = str((h.get("text") if isinstance(h, dict) else "") or "").strip()
            items.append(f"[{i+1}] {txt}")
            try:
                cits.append({"n": i+1, "page": (h.get("page") if isinstance(h, dict) else None)})
            except Exception:
                cits.append({"n": i+1, "page": None})
        return {"context": "\n\n".join(items).strip(), "citations": cits}
    _RAG_OK = False

from src.utils.text_utils import find_exact_locations

# Constants
RAG_COLLECTION = "pnd_manual_sentences"


def _truncate_text(text: str, max_chars: int = 6000) -> str:
    """Truncate text to max_chars."""
    try:
        return text if len(text) <= max_chars else (text[: max_chars - 3] + "...")
    except Exception:
        return text


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    try:
        return [s.strip() for s in re.split(r"(?<=[\.\?\!])\s+", text) if s.strip()]
    except Exception:
        return [text]


_STOPWORDS = set(
    """the a an and or of for to in on with without by as from at into over under between among about across during before after than then 
    is are was were be being been have has had do does did can could should would may might must this that these those it its they them their we our you your i me my mine ours yours his her hers him he she what which who whom whose where when why how not no nor only also if else than within per each such more most less least including include includes etc versus vs v 
    annual plan describe role translate translating national priorities priority government strategic policy policies program programme programs programmes project projects development sector sectors federal provincial division divisions commission planning economic technical finance economic affairs
    """.split()
)


def _keyword_fallback_hits(question: str, pages: list[str], max_pages: int = 3, max_sents: int = 8) -> list[dict]:
    """Keyword-based fallback for finding relevant passages."""
    try:
        ql = (question or "").lower()
        words = [w.strip(".,:;()[]{}!?") for w in re.split(r"\s+", ql) if len(w.strip(".,:;()[]{}!?").strip()) >= 4]
        kws = [w for w in words if w not in _STOPWORDS]
        
        bigrams = []
        toks = [t for t in re.split(r"\s+", ql) if t]
        for i in range(len(toks) - 1):
            bg = f"{toks[i]} {toks[i+1]}".strip()
            if len(bg) >= 7 and all(x not in _STOPWORDS for x in toks[i:i+2]):
                bigrams.append(bg)
        
        seen = set()
        terms: list[str] = []
        for t in (bigrams + kws):
            if t not in seen:
                seen.add(t)
                terms.append(t)
            if len(terms) >= 12:
                break
        
        if not terms:
            return []
        
        scores = []
        for idx, pg in enumerate(pages or [], start=1):
            low = (pg or "").lower()
            sc = sum(low.count(t) for t in terms)
            if sc > 0:
                scores.append((sc, idx, pg))
        scores.sort(reverse=True)
        picked = scores[:max_pages]
        
        hits: list[dict] = []
        for _sc, idx, pg in picked:
            sents = _split_sentences(pg)
            for s in sents:
                sl = s.lower()
                if any(t in sl for t in terms):
                    hits.append({
                        "text": s,
                        "page": idx,
                        "score": None,
                        "source": RAG_COLLECTION,
                    })
                    if len(hits) >= max_sents:
                        break
            if len(hits) >= max_sents:
                break
        return hits
    except Exception:
        return []


def expand_query_aggressively(question: str) -> list[str]:
    """Generate multiple query variants for comprehensive retrieval."""
    variants = [question]
    
    acronym_map = {
        "PC-I": ["PC-I", "Planning Commission Proforma I", "Planning Commission Form 1"],
        "PC-II": ["PC-II", "Planning Commission Proforma II", "feasibility study"],
        "PC-III": ["PC-III", "monitoring report", "progress report"],
        "PC-IV": ["PC-IV", "completion report", "project closure"],
        "PC-V": ["PC-V", "evaluation report"],
        "DDWP": ["DDWP", "Divisional Development Working Party"],
        "CDWP": ["CDWP", "Central Development Working Party"],
        "ECNEC": ["ECNEC", "Executive Committee National Economic Council"],
        "PDWP": ["PDWP", "Provincial Development Working Party"],
        "CHIRA": ["CHIRA", "Climate Hazard Initial Risk Assessment"],
        "VGF": ["VGF", "Viability Gap Fund"],
        "PPP": ["PPP", "Public Private Partnership"],
        "PAO": ["PAO", "Principal Accounting Officer"],
    }
    
    for abbr, expansions in acronym_map.items():
        if abbr in question:
            for exp in expansions[:2]:
                variants.append(question.replace(abbr, exp))
    
    words = re.findall(r'\b[A-Za-z]{4,}\b', question)
    if len(words) >= 3:
        variants.append(" ".join(words[:10]))
    
    q_clean = re.sub(r'^(what|when|where|who|why|how|explain|describe|list)\s+', 
                     '', question.lower(), flags=re.IGNORECASE)
    if q_clean != question.lower():
        variants.append(q_clean)
    
    return list(set(variants))[:5]


def detect_question_category(question: str) -> str:
    """Classify question into PC-form or topic category."""
    lower = question.lower()
    
    if any(term in lower for term in ["pc-i", "pc i", "pc 1", "proforma i", "proforma 1"]):
        return "PC-I"
    if any(term in lower for term in ["pc-ii", "pc ii", "pc 2", "proforma ii", "proforma 2"]):
        return "PC-II"
    if any(term in lower for term in ["pc-iii", "pc iii", "pc 3", "proforma iii", "proforma 3"]):
        return "PC-III"
    if any(term in lower for term in ["pc-iv", "pc iv", "pc 4", "proforma iv", "proforma 4"]):
        return "PC-IV"
    if any(term in lower for term in ["pc-v", "pc v", "pc 5", "proforma v", "proforma 5"]):
        return "PC-V"
    
    if any(term in lower for term in ["monitor", "progress report", "tracking", "implementation"]):
        return "Monitoring"
    if any(term in lower for term in ["pfm act", "public finance", "finance management", "fiscal"]):
        return "PFM Act"
    if any(term in lower for term in ["budget", "allocation", "funding", "appropriation"]):
        return "Budget"
    if any(term in lower for term in ["ecnec", "cdwp", "ddwp", "approval", "scrutiny"]):
        return "Approval Process"
    
    return "General"


def decompose_question(question: str) -> list[str]:
    """Split compound questions into sub-questions."""
    lower = question.lower()
    
    if " and " not in lower:
        return [question]
    
    idx = lower.index(" and ")
    after_and = question[idx+5:].strip()
    
    question_starters = ["what", "which", "how", "explain", "describe", "list", "who", "when", "where", "why", "define"]
    if any(after_and.lower().startswith(w) for w in question_starters):
        part1 = question[:idx].strip()
        if not part1.endswith("?"):
            part1 += "?"
        
        part2 = after_and.strip()
        if not part2.endswith("?"):
            part2 += "?"
        
        return [part1, part2]
    
    return [question]


def _qdrant_url() -> str:
    """Get Qdrant URL from session state or default."""
    return st.session_state.get("qdrant_url", "http://localhost:6333")


def generate_answer_generative(question: str) -> str:
    """Generate answer using full RAG pipeline with cross-encoder reranking."""
    try:
        if not (st.session_state.get("raw_pages") or []) and int(st.session_state.get("last_index_count") or 0) == 0:
            pass  # Manual load handled by sidebar
    except Exception:
        pass
    
    question_category = detect_question_category(question)
    query_variants = expand_query_aggressively(question)
    sub_questions = decompose_question(question)
    
    all_hits: list[dict] = []
    use_qdrant = bool(st.session_state.get("indexed_ok") or int(st.session_state.get("last_index_count") or 0) > 0)
    
    for variant in query_variants:
        for sq in sub_questions:
            combined = f"{variant} {sq}"
            sq_hits: list[dict] = []
            if use_qdrant and _RAG_OK and search is not None:
                try:
                    sq_hits = search(combined, top_k=60, qdrant_url=_qdrant_url(), mmr=True, lambda_mult=0.7, min_score=0.05)  # type: ignore
                except TypeError:
                    sq_hits = search(combined, top_k=60, qdrant_url=_qdrant_url())  # type: ignore
                except Exception:
                    sq_hits = []
            
            if question_category in ["PC-I", "PC-II", "PC-III", "PC-IV", "PC-V"]:
                category_hits = []
                for h in sq_hits:
                    text_lower = h.get("text", "").lower()
                    if question_category.lower() in text_lower or "proforma" not in text_lower:
                        category_hits.append(h)
                sq_hits = category_hits if category_hits else sq_hits
            
            all_hits.extend(sq_hits)
    
    hits = all_hits

    if (not hits) and (st.session_state.get("raw_pages") or []):
        try:
            pages_full = st.session_state.get("raw_pages") or []
            locs_fb = find_exact_locations(question, pages_full, max_results=40)
            for it in (locs_fb or []):
                hits.append({
                    "text": (it.get("sentence") or "").strip(),
                    "page": it.get("page"),
                    "score": None,
                    "source": RAG_COLLECTION,
                })
        except Exception:
            pass

    hits = dedup_chunks(hits)
    hits = mmr_rerank(hits, top_k=15, lambda_mult=0.7)
    
    if hits:
        scores = [h.get("score", 0) for h in hits if h.get("score") is not None]
        if scores and max(scores) < 0.5:
            words = re.findall(r'\b[A-Z]{2,}\b|\b[a-z]{4,}\b', question)
            key_terms = " ".join(set(words[:5]))
            
            expanded_query = f"{question} {key_terms}"
            retry_hits: list[dict] = []
            
            if use_qdrant and _RAG_OK and search is not None:
                try:
                    retry_hits = search(expanded_query, top_k=60, qdrant_url=_qdrant_url(), mmr=True, lambda_mult=0.7, min_score=0.05)  # type: ignore
                except Exception:
                    retry_hits = []
            
            if retry_hits:
                hits.extend(retry_hits)
                hits = dedup_chunks(hits)
                hits = mmr_rerank(hits, top_k=15, lambda_mult=0.7)

    ctx_pack = build_context(hits, token_budget=6000)
    context_text = (ctx_pack.get("context") or "").strip()
    
    if not context_text and hits:
        try:
            context_text = ("\n\n".join([str(h.get("text", "")).strip() for h in hits if h.get("text")])[:4000]).strip()
        except Exception:
            context_text = ""
    
    citations = ctx_pack.get("citations") or []
    
    try:
        st.session_state["last_hits"] = hits
        st.session_state["last_context"] = context_text
        st.session_state["last_question"] = question
    except Exception:
        pass

    if not context_text:
        pages_full = st.session_state.get("raw_pages") or []
        if pages_full:
            kw_hits = _keyword_fallback_hits(question, pages_full, max_pages=3, max_sents=8)
            if kw_hits:
                hits = kw_hits
                ctx_pack = build_context(hits, token_budget=6000)
                context_text = (ctx_pack.get("context") or "").strip()
                citations = ctx_pack.get("citations") or []

    if not context_text:
        return "Not available in the provided document."

    # Generate answer using LLM
    try:
        from src.models.pretrained_model import PretrainedModel
        gen = PretrainedModel(
            entrypoint=st.session_state.get("pretrained_entry") or "",
            model_path=st.session_state.get("pretrained_path") or ""
        )
        answer = gen.predict(
            question=question,
            context=context_text,
            chunks=[h.get("text", "") for h in hits],
            raw_pages=st.session_state.get("raw_pages") or []
        ) or "Not available in the provided document."
    except Exception as e:
        logging.exception("LLM generation failed")
        answer = f"Error generating answer: {e}"
    
    # Add citations
    if citations:
        answer += "\n\n**References:**\n"
        for cit in citations[:5]:
            answer += f"- [{cit.get('n')}] Page {cit.get('page', '?')}\n"
    
    return answer


def generate_answer(question: str) -> tuple[str, list[str]]:
    """Main answer generation entry point. Returns (answer_html, citations)."""
    mode = st.session_state.get("answer_mode", "Generative")
    is_exact = str(mode).lower().startswith("exact")
    
    if is_exact:
        return generate_answer_exact(question)
    else:
        answer = generate_answer_generative(question)
        return (answer, [])


def generate_answer_exact(question: str) -> tuple[str, list[str]]:
    """Exact search mode - returns grounded passages only."""
    top_k_local = int(min(8, max(1, int(st.session_state.get("top_k", 6)))))
    eff_top_k = min(8, 3)
    
    pages = st.session_state.get("raw_pages") or []
    locs = find_exact_locations(question, pages, max_results=max(25, eff_top_k * 5)) if pages else []
    
    if locs:
        norm = []
        seen = set()
        for it in locs:
            pg = it.get('page')
            try:
                if pg is not None:
                    pg = int(pg)
                    pg = pg if pg >= 1 else (pg + 1)
            except Exception:
                pass
            para = it.get('paragraph')
            line = it.get('line')
            sent = (it.get('sentence') or '').strip()
            key = (pg, para, line, sent)
            if key in seen:
                continue
            seen.add(key)
            norm.append({"page": pg, "paragraph": para, "line": line, "text": sent})
        
        lines = [f"Pg {n.get('page','?')}, Para {n.get('paragraph','?')}, Line {n.get('line','?')}: \"{n.get('text','')}\"" for n in norm]
        answer = "\n\n".join(lines) if lines else "No grounded passages found. Please rephrase or narrow the scope."
        
        hits = [{
            "text": n.get("text"),
            "page": n.get("page"),
            "score": None,
            "source": RAG_COLLECTION,
            "paragraph": n.get("paragraph"),
            "line": n.get("line"),
        } for n in norm]
        
        try:
            st.session_state["last_hits"] = hits
        except Exception:
            pass
        
        return (answer, [])
    else:
        return ("No grounded passages found. Please rephrase or narrow the scope.", [])
