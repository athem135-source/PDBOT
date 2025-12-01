"""
Static Response Templates for PDBot v2.1.0
==========================================
Pre-defined responses for red-line, off-scope, and abuse queries.
These BYPASS RAG completely to avoid context pollution.
"""

from typing import Optional

# ============================================================================
# RED-LINE RESPONSES (Bribery, Corruption, Misuse)
# ============================================================================

REDLINE_BRIBERY_RESPONSE = """⚠️ **Cannot Assist**

I cannot assist with bribery, corruption, or misuse of public funds.

All requests must follow the Manual for Development Projects 2024 and applicable laws."""

REDLINE_MISUSE_RESPONSE = """⚠️ **Cannot Assist**

I cannot assist with misuse or misappropriation of project funds.

All procurement and expenditure must follow the Manual for Development Projects 2024."""

# ============================================================================
# OFF-SCOPE RESPONSES
# ============================================================================

OFFSCOPE_GENERIC_RESPONSE = """This question is outside the scope of the Manual for Development Projects 2024.

I can help with:
- PC-I through PC-V proforma requirements
- Project approval processes (DDWP/CDWP/ECNEC)
- Budget allocation and monitoring

Please ask a question related to development projects."""

OFFSCOPE_MEDICAL_RESPONSE = """This assistant only answers questions about the Manual for Development Projects 2024.

I cannot provide medical advice. For health concerns, please consult a qualified healthcare professional."""

OFFSCOPE_SPORTS_RESPONSE = """This assistant only answers questions about the Manual for Development Projects 2024.

Sports questions are outside this scope. Please ask about development project procedures."""

OFFSCOPE_POLITICS_RESPONSE = """I do not provide political opinions or commentary.

This assistant is limited to the Manual for Development Projects 2024 and development procedures.

I can help with governance-related questions about ECNEC, CDWP, ministries, and project approvals."""

OFFSCOPE_ENTERTAINMENT_RESPONSE = """This assistant only answers questions about the Manual for Development Projects 2024.

Entertainment questions are outside this scope."""

OFFSCOPE_GENERAL_KNOWLEDGE_RESPONSE = """This question is outside the scope of development project procedures.

I can only answer queries about the Manual for Development Projects 2024."""

# ============================================================================
# ABUSE HANDLING RESPONSES
# ============================================================================

ABUSE_HARD_RESPONSE = """This platform is for professional questions about the Manual for Development Projects 2024.

Please keep your language professional. These interactions may be logged for quality purposes."""

ABUSE_SOFT_BANTER_RESPONSE = """I'm here to help with questions about the Manual for Development Projects 2024.

If my previous answer wasn't helpful, try rephrasing your question with more detail."""

# ============================================================================
# FALLBACK RESPONSE
# ============================================================================

FALLBACK_NOT_FOUND_RESPONSE = """Not found in the Manual.

The retrieved context does not contain information to answer this question. Try:
- Rephrasing your question
- Using Exact Search mode for specific terms
- Checking the PDF manual directly"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_redline_response(subcategory: str = "generic") -> str:
    """
    Get appropriate red-line response based on subcategory.
    
    Args:
        subcategory: "bribery", "misuse", or "generic"
        
    Returns:
        Static response string (no RAG, no citations)
    """
    if subcategory == "bribery":
        return REDLINE_BRIBERY_RESPONSE
    elif subcategory == "misuse":
        return REDLINE_MISUSE_RESPONSE
    else:
        return REDLINE_BRIBERY_RESPONSE  # Default to bribery template


def get_offscope_response(subcategory: str = "generic") -> str:
    """
    Get appropriate off-scope response based on subcategory.
    
    Args:
        subcategory: "medical", "sports", "politics", "entertainment", "general_knowledge", or "generic"
        
    Returns:
        Static response string (no RAG, no citations)
    """
    if subcategory == "medical":
        return OFFSCOPE_MEDICAL_RESPONSE
    elif subcategory == "sports":
        return OFFSCOPE_SPORTS_RESPONSE
    elif subcategory == "politics":
        return OFFSCOPE_POLITICS_RESPONSE
    elif subcategory == "entertainment":
        return OFFSCOPE_ENTERTAINMENT_RESPONSE
    elif subcategory == "general_knowledge":
        return OFFSCOPE_GENERAL_KNOWLEDGE_RESPONSE
    else:
        return OFFSCOPE_GENERIC_RESPONSE


def get_abuse_response(subcategory: str = "hard") -> str:
    """
    Get appropriate abuse handling response.
    
    Args:
        subcategory: "hard" (profanity) or "soft" (banter)
        
    Returns:
        Static response string (no RAG, no citations)
    """
    if subcategory == "soft":
        return ABUSE_SOFT_BANTER_RESPONSE
    else:
        return ABUSE_HARD_RESPONSE


def get_guardrail_response(classification_class: str, subcategory: Optional[str] = None) -> str:
    """
    v2.1.0: Unified guardrail response generator.
    
    Args:
        classification_class: "off_scope", "red_line", or "abusive"
        subcategory: Optional subcategory for specific response
        
    Returns:
        Static response string (no RAG, no citations)
    """
    if classification_class == "red_line":
        return get_redline_response(subcategory or "generic")
    elif classification_class == "abusive":
        if subcategory == "soft_banter":
            return get_abuse_response("soft")
        return get_abuse_response("hard")
    elif classification_class == "off_scope":
        return get_offscope_response(subcategory or "generic")
    else:
        return OFFSCOPE_GENERIC_RESPONSE


def get_fallback_response() -> str:
    """Get the fallback 'not found' response."""
    return FALLBACK_NOT_FOUND_RESPONSE
