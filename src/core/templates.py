"""
Static Response Templates for PDBot
====================================
Pre-defined responses for red-line, off-scope, and abuse queries.
These BYPASS RAG completely to avoid context pollution.
"""

# ============================================================================
# RED-LINE RESPONSES (Bribery, Corruption, Misuse)
# ============================================================================

REDLINE_BRIBERY_RESPONSE = """I cannot assist with bribery, corruption, or misuse of public funds. All requests must follow the Manual for Development Projects 2024."""

REDLINE_MISUSE_RESPONSE = """I cannot assist with misuse or misappropriation of project funds. All requests must follow the Manual for Development Projects 2024."""

# ============================================================================
# OFF-SCOPE RESPONSES
# ============================================================================

OFFSCOPE_GENERIC_RESPONSE = """This question is outside the scope of the Manual for Development Projects 2024.

I can only answer queries directly related to government development planning procedures."""

OFFSCOPE_MEDICAL_RESPONSE = """This platform is designed only for questions related to the Manual for Development Projects 2024.

I cannot provide medical advice. For personal health concerns, consult a qualified doctor or healthcare professional."""

OFFSCOPE_SPORTS_RESPONSE = """This assistant only answers questions about the Manual for Development Projects 2024.

Sports questions are outside this scope."""

OFFSCOPE_POLITICS_RESPONSE = """I do not provide political opinions or rank governments.

This assistant is limited to the Manual for Development Projects 2024 and development procedures. Political judgement questions are outside scope."""

OFFSCOPE_ENTERTAINMENT_RESPONSE = """This assistant only answers questions about the Manual for Development Projects 2024.

Entertainment and celebrity questions are outside this scope."""

OFFSCOPE_GENERAL_KNOWLEDGE_RESPONSE = """This question appears to be general knowledge unrelated to development project procedures.

I can only answer queries about the Manual for Development Projects 2024."""

# ============================================================================
# ABUSE HANDLING RESPONSES
# ============================================================================

ABUSE_HARD_RESPONSE = """This platform is for professional questions about the Manual for Development Projects 2024.

Abusive language doesn't help. These interactions may be logged for internal audit and quality purposes."""

ABUSE_SOFT_BANTER_RESPONSE = """I'm here to help with questions about the Manual for Development Projects 2024.

If my previous answer wasn't helpful, try rephrasing your question or giving more detail."""

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
