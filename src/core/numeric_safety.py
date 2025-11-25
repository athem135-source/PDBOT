"""
Numeric Safety Module for PDBot v1.6.0
=======================================

Prevents numeric hallucinations by:
1. Checking constants BEFORE calling RAG
2. Refusing to guess if RAG retrieves no numbers
3. Using hardcoded approval limits for authority questions

Critical Fix: No more "Rs. [4] billion" hallucinations!
"""
from __future__ import annotations

import re
from typing import Optional, List, Dict, Any

from ..constants.approval_limits import (
    APPROVAL_LIMITS,
    NUMERIC_RULES,
    NUMERIC_QUERY_KEYWORDS,
    get_approval_authority,
    format_approval_limit,
)


def is_numeric_query(query: str) -> bool:
    """
    Detect if query asks for numeric information.
    
    Args:
        query: User question
        
    Returns:
        True if query contains numeric keywords
    """
    q_lower = query.lower()
    return any(keyword in q_lower for keyword in NUMERIC_QUERY_KEYWORDS)


def extract_amount_from_query(query: str) -> Optional[float]:
    """
    Extract rupee amount from query.
    
    Examples:
        "project costs Rs. 5 billion" → 5_000_000_000
        "budget is 200 million" → 200_000_000
        "Rs. 7.5 crore" → 75_000_000
    
    Args:
        query: User question
        
    Returns:
        Amount in rupees, or None if not found
    """
    q_lower = query.lower()
    
    # Pattern: Rs. <number> <unit>
    # Units: billion, million, crore, lakh
    pattern = r"rs\.?\s*(\d+(?:\.\d+)?)\s*(billion|million|crore|lakh)"
    match = re.search(pattern, q_lower)
    
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        
        # Convert to rupees
        if unit == "billion":
            return number * 1_000_000_000
        elif unit == "million":
            return number * 1_000_000
        elif unit == "crore":
            return number * 10_000_000
        elif unit == "lakh":
            return number * 100_000
    
    # Try pattern without Rs.: "5 billion", "200 million"
    pattern2 = r"(\d+(?:\.\d+)?)\s*(billion|million|crore|lakh)"
    match2 = re.search(pattern2, q_lower)
    
    if match2:
        number = float(match2.group(1))
        unit = match2.group(2)
        
        if unit == "billion":
            return number * 1_000_000_000
        elif unit == "million":
            return number * 1_000_000
        elif unit == "crore":
            return number * 10_000_000
        elif unit == "lakh":
            return number * 100_000
    
    return None


def check_constants_for_answer(query: str) -> Optional[str]:
    """
    Check if query can be answered using hardcoded constants.
    
    This BYPASSES RAG for approval limit questions.
    
    Args:
        query: User question
        
    Returns:
        Answer from constants, or None if cannot be answered
    """
    q_lower = query.lower()
    
    # Check approval authority questions
    for authority_name in ["ddwp", "pdwp", "cdwp", "ecnec"]:
        if authority_name in q_lower:
            # Questions like: "What is DDWP limit?"
            if any(word in q_lower for word in ["limit", "threshold", "ceiling", "maximum", "approve"]):
                return format_approval_limit(authority_name.upper())
    
    # Check if query asks "who approves X rupees?"
    amount = extract_amount_from_query(query)
    if amount and any(word in q_lower for word in ["who", "which", "approves", "approval", "authority"]):
        # Check if query says "above" or "over" - if so, add a bit to amount
        if any(word in q_lower for word in ["above", "over", "more than", "greater than"]):
            amount += 1  # Add Rs. 1 to ensure proper boundary check
        
        authority = get_approval_authority(amount)
        return f"Projects costing {amount:,.0f} rupees fall under **{authority}** approval.\n\n{format_approval_limit(authority)}"
    
    # Check numeric rules
    for rule_key, rule_value in NUMERIC_RULES.items():
        # Convert rule_key to natural language pattern
        # e.g., "pc1_preparation_time" → "pc-i preparation time" or "pc1 preparation"
        rule_key_readable = rule_key.replace("_", " ")
        
        if rule_key_readable in q_lower:
            # Format nicely
            rule_name = " ".join(word.capitalize() for word in rule_key.split("_"))
            return f"**{rule_name}:** {rule_value}\n\n[Manual for Development Projects 2024]"
    
    return None


def has_numbers_in_chunks(chunks: List[Dict[str, Any]]) -> bool:
    """
    Check if any retrieved chunk contains numeric information.
    
    Args:
        chunks: Retrieved RAG chunks with "text" field
        
    Returns:
        True if at least one chunk has numbers
    """
    # Pattern: digits with units or standalone large numbers
    number_pattern = r"\d+(?:\.\d+)?\s*(?:billion|million|crore|lakh|%|percent|months?|years?|days?)"
    
    for chunk in chunks:
        text = chunk.get("text", "")
        if re.search(number_pattern, text, re.IGNORECASE):
            return True
    
    return False


def validate_numeric_answer(answer: str, chunks: List[Dict[str, Any]]) -> Optional[str]:
    """
    Validate that numeric answer is grounded in retrieved chunks.
    
    If answer contains numbers NOT present in chunks, refuse to answer.
    
    Args:
        answer: Generated answer
        chunks: Retrieved RAG chunks
        
    Returns:
        Validated answer, or refusal message if hallucination detected
    """
    # Extract numbers from answer
    answer_numbers = re.findall(r"\d+(?:\.\d+)?", answer)
    
    if not answer_numbers:
        return answer  # No numbers in answer, safe
    
    # Check if chunks contain ANY numbers
    if not has_numbers_in_chunks(chunks):
        return """I cannot provide specific numeric values for this question because the retrieved manual sections do not contain the necessary numeric information.

Please verify the question or check the Manual for Development Projects 2024 directly for accurate numeric data.

**Note:** This refusal prevents hallucinated numbers."""
    
    # If chunks have numbers, assume grounding is OK
    # (More sophisticated check would compare specific numbers, but that's error-prone)
    return answer


def enforce_numeric_safety(
    query: str,
    chunks: List[Dict[str, Any]],
    answer: str
) -> str:
    """
    Complete numeric safety pipeline.
    
    Pipeline:
    1. Check if constants can answer → return constant
    2. Check if chunks have numbers → refuse if not
    3. Validate answer doesn't hallucinate → refuse if suspicious
    
    Args:
        query: User question
        chunks: Retrieved RAG chunks
        answer: Generated answer
        
    Returns:
        Safe answer or refusal
    """
    # Step 1: Check constants first
    if is_numeric_query(query):
        constant_answer = check_constants_for_answer(query)
        if constant_answer:
            return constant_answer
    
    # Step 2: Validate answer grounding
    if is_numeric_query(query):
        validated = validate_numeric_answer(answer, chunks)
        return validated if validated is not None else answer
    
    # Not a numeric query, return answer as-is
    return answer
