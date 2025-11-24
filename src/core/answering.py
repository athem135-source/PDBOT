"""
Core answer generation and composition logic for PDBot.

Extracted from app.py to improve maintainability and testability.
Handles LLM integration, context quality checks, and answer formatting.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class AnswerResult:
    """Structured result from answer generation."""
    answer: str
    citations: List[str]
    context_used: str
    chunks_retrieved: int
    quality_score: float  # 0-1 scale
    refusal_reason: Optional[str] = None  # Set if answer was refused
    backend_error: Optional[str] = None  # Set if retrieval failed


def check_context_quality(context: str, question: str, min_words: int = 15) -> Tuple[bool, Optional[str]]:
    """
    Check if retrieved context is sufficient for answering.
    
    Args:
        context: Retrieved text from manual
        question: User's question
        min_words: Minimum context words required
    
    Returns:
        (is_sufficient, refusal_reason)
    """
    if not context or not context.strip():
        return False, "No relevant context found in manual"
    
    words = context.split()
    if len(words) < min_words:
        return False, f"Insufficient context ({len(words)} words, need {min_words}+)"
    
    # Check for meaningful content (not just stopwords)
    meaningful_words = [w for w in words if len(w) > 3 and not w.lower() in {'the', 'and', 'for', 'that', 'this', 'with'}]
    if len(meaningful_words) < min_words // 2:
        return False, "Context lacks meaningful content"
    
    return True, None


def format_citations(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Extract and format page citations from retrieved chunks.
    
    Args:
        chunks: List of chunk dicts with 'page' field
    
    Returns:
        List of formatted citation strings like "[1] Manual p.42"
    """
    citations = []
    seen_pages = set()
    
    for chunk in chunks:
        page = chunk.get('page')
        if page and page not in seen_pages:
            seen_pages.add(page)
            source = chunk.get('source', 'Manual')
            citations.append(f"[{len(citations)+1}] {source}, p.{page}")
    
    return citations


def build_llm_prompt(question: str, context: str, mode: str = "generative") -> str:
    """
    Build the prompt for the LLM based on mode.
    
    Args:
        question: User's question
        context: Retrieved context from manual
        mode: "generative" or "exact"
    
    Returns:
        Formatted prompt string
    """
    if mode.lower() == "exact":
        # Exact mode: Just return passages
        return f"Find relevant passages for: {question}\n\nContext:\n{context}"
    
    # Generative mode: Full answer with citations
    return f"""Answer the following question using ONLY the provided context from the Planning & Development Manual.

Question: {question}

Context from Manual:
{context}

Instructions:
1. Answer in 2-3 clear paragraphs
2. Use citations [p.X] at the end of relevant sentences
3. If context is insufficient, say so explicitly
4. Do not add information not in the context
5. Maintain professional bureaucratic tone"""


def clean_llm_output(raw_output: str) -> str:
    """
    Clean up LLM output (remove meta-talk, fix formatting).
    
    Args:
        raw_output: Raw text from LLM
    
    Returns:
        Cleaned text
    """
    # Remove common LLM meta-phrases
    meta_phrases = [
        r"^(Based on the (context|manual|document)(,| provided,?)? ?)",
        r"^(According to the (context|manual|document)(,| provided,?)? ?)",
        r"^(The context (states|mentions|indicates) that ?)",
        r"^(Here('s| is) (the answer|what|my response):? ?)",
    ]
    
    text = raw_output
    for pattern in meta_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Fix common OCR errors
    ocr_fixes = {
        "PC-l": "PC-I",
        "PC-ll": "PC-II", 
        "PC-lll": "PC-III",
        "Rs.lOOM": "Rs.100M",
        "Rs.lM": "Rs.1M",
        "Rs.lB": "Rs.1B",
    }
    for wrong, right in ocr_fixes.items():
        text = text.replace(wrong, right)
    
    return text.strip()


def compose_answer_with_context_check(
    question: str,
    context: str,
    chunks: List[Dict[str, Any]],
    llm_generator,
    mode: str = "generative",
    min_context_words: int = 15
) -> AnswerResult:
    """
    Main answer composition function with quality checks.
    
    Args:
        question: User's question
        context: Retrieved context
        chunks: Retrieved chunks for citations
        llm_generator: LLM model instance (LocalModel or similar)
        mode: Answer mode ("generative" or "exact")
        min_context_words: Minimum required context words
    
    Returns:
        AnswerResult with answer and metadata
    """
    # Check context quality first
    is_sufficient, refusal_reason = check_context_quality(context, question, min_context_words)
    
    if not is_sufficient:
        # Return refusal with explanation
        answer = f"""⚠️ **{refusal_reason}**

Try rephrasing your question or use Exact Search mode to locate precise passages.

**Tips:**
- Be more specific (e.g., "PC-I approval process" vs "projects")
- Use exact terms from the manual
- Check spelling of technical terms"""
        
        citations = format_citations(chunks) if chunks else []
        
        return AnswerResult(
            answer=answer,
            citations=citations,
            context_used=context,
            chunks_retrieved=len(chunks),
            quality_score=0.0,
            refusal_reason=refusal_reason
        )
    
    # Generate answer with LLM
    prompt = build_llm_prompt(question, context, mode)
    
    try:
        raw_answer = llm_generator.generate_response(
            prompt=prompt,
            context=context,
            question=question
        )
        
        # Clean output
        answer = clean_llm_output(raw_answer)
        
        # Format citations
        citations = format_citations(chunks)
        
        # Calculate quality score based on answer length and citations
        quality_score = min(1.0, len(answer.split()) / 100.0)  # 0-1 scale
        if citations:
            quality_score = min(1.0, quality_score + 0.2)  # Bonus for citations
        
        return AnswerResult(
            answer=answer,
            citations=citations,
            context_used=context,
            chunks_retrieved=len(chunks),
            quality_score=quality_score,
            refusal_reason=None
        )
    
    except Exception as e:
        # LLM generation failed
        error_answer = f"⚠️ **Answer generation failed:** {str(e)}\n\nPlease try again or contact support."
        
        return AnswerResult(
            answer=error_answer,
            citations=[],
            context_used=context,
            chunks_retrieved=len(chunks),
            quality_score=0.0,
            refusal_reason=f"LLM error: {e}"
        )
