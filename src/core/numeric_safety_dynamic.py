"""
DYNAMIC Numeric Safety Module for PDBot v1.7.0
================================================

CRITICAL CHANGE from v1.6.0:
- NO HARDCODED APPROVAL LIMITS
- ALL values retrieved dynamically from RAG
- System works with ANY PDF (2024, 2025, 2026, etc.)
- Version-aware retrieval support

This module ONLY validates that:
1. Numbers in context match numbers in answer (prevents hallucination)
2. Answer doesn't invent numbers not present in retrieved chunks
3. OCR artifacts are removed (Rs. [4] → Rs.)

It does NOT provide hardcoded values.
"""

import re
from typing import Optional, List, Dict, Any


def clean_ocr_numbers(text: str) -> str:
    """
    Remove OCR artifacts from numbers.
    
    Examples:
        Rs. [4] billion → Rs. billion
        [X] → (removed)
        
    Args:
        text: Raw text with potential OCR artifacts
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove bracket numbers: [4], [X], etc.
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[X\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[p\.\s*X[^\]]*\]', '', text, flags=re.IGNORECASE)
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_numbers_from_text(text: str) -> List[str]:
    """
    Extract all numbers from text (with units).
    
    Examples:
        "Rs. 75 million" → ["75", "million"]
        "10 billion" → ["10", "billion"]
        
    Args:
        text: Text to analyze
        
    Returns:
        List of number strings found
    """
    if not text:
        return []
    
    # Pattern: number (with optional decimal/comma) + optional unit
    pattern = r'\b(\d+(?:[,\.]\d+)*)\s*(million|billion|crore|lakh|rupees?|rs\.?)?\b'
    matches = re.findall(pattern, text.lower())
    
    numbers = []
    for num, unit in matches:
        if num:
            numbers.append(num)
        if unit:
            numbers.append(unit)
    
    return numbers


def validate_numeric_answer(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    answer: str
) -> tuple[bool, Optional[str]]:
    """
    Validate that answer doesn't hallucinate numbers.
    
    Rules:
    1. If answer contains numbers, they must appear in retrieved chunks
    2. If no relevant numbers in chunks, answer should say "not found"
    3. OCR artifacts should be cleaned
    
    Args:
        question: User question
        retrieved_chunks: RAG chunks
        answer: Generated answer
        
    Returns:
        (is_valid, error_message)
    """
    if not answer:
        return True, None
    
    # Extract numbers from answer
    answer_numbers = extract_numbers_from_text(answer)
    
    if not answer_numbers:
        # No numbers in answer - safe
        return True, None
    
    # Extract numbers from all retrieved chunks
    context_numbers = []
    for chunk in retrieved_chunks:
        chunk_text = chunk.get("text", "")
        context_numbers.extend(extract_numbers_from_text(chunk_text))
    
    if not context_numbers:
        # Answer has numbers but context doesn't - potential hallucination
        return False, "Numbers mentioned but not found in retrieved context"
    
    # Check if all answer numbers appear in context
    for num in answer_numbers:
        if num not in context_numbers:
            # Allow small variations (75 vs 75.0, etc.)
            try:
                num_float = float(num.replace(',', ''))
                found = any(abs(float(c.replace(',', '')) - num_float) < 0.01 for c in context_numbers if c.replace('.', '').replace(',', '').isdigit())
                if not found:
                    return False, f"Number '{num}' not found in retrieved context"
            except (ValueError, AttributeError):
                # Unit word like "million" - check if it exists
                if num not in context_numbers:
                    return False, f"Term '{num}' not found in retrieved context"
    
    return True, None


def enforce_numeric_safety(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    answer: str
) -> str:
    """
    Enforce numeric safety on answer (v1.7.0 DYNAMIC VERSION).
    
    Changes from v1.6.0:
    - NO hardcoded values used
    - Only validates numbers against retrieved context
    - Cleans OCR artifacts
    - Returns generic message if validation fails
    
    Args:
        question: User question
        retrieved_chunks: RAG chunks
        answer: Generated answer
        
    Returns:
        Validated answer or error message
    """
    if not answer:
        return answer
    
    # Clean OCR artifacts first
    answer = clean_ocr_numbers(answer)
    
    # Validate numbers
    is_valid, error_msg = validate_numeric_answer(question, retrieved_chunks, answer)
    
    if not is_valid:
        # Return generic message instead of hallucinated answer
        return "The manual does not provide a specific numeric value for this query in the retrieved context."
    
    return answer


def is_numeric_query(query: str) -> bool:
    """
    Detect if query asks for numeric information.
    
    Args:
        query: User question
        
    Returns:
        True if query contains numeric keywords
    """
    q_lower = query.lower()
    
    numeric_keywords = [
        "limit", "threshold", "ceiling", "maximum", "minimum",
        "cost", "budget", "allocation", "amount",
        "rs", "rupees", "million", "billion", "crore", "lakh",
        "how much", "how many", "percentage", "percent", "%",
        "duration", "time", "period", "validity", "years", "months",
    ]
    
    return any(keyword in q_lower for keyword in numeric_keywords)
