"""
Static Response Templates for PDBot v2.5.0
==========================================
Pre-defined responses for red-line, off-scope, abuse, greeting, and ambiguous queries.
These BYPASS RAG completely to avoid context pollution.
"""

from typing import Optional
import random

# ============================================================================
# GREETING RESPONSES (No RAG, no citations)
# ============================================================================

GREETING_RESPONSES = [
    "Assalam-o-Alaikum! I'm PDBOT, your assistant for the Manual for Development Projects 2024. How can I help you today?",
    "Hello! I'm here to help with questions about Pakistan's development project procedures. What would you like to know?",
    "Hi there! Ask me anything about PC-I, approval processes, or the Manual for Development Projects 2024.",
    "Welcome! I specialize in Pakistan's planning and development procedures. What can I assist you with?",
]

THANKS_RESPONSES = [
    "You're welcome! Feel free to ask if you have more questions about development projects.",
    "Happy to help! Let me know if you need anything else.",
    "Anytime! Is there anything else about the Manual you'd like to know?",
]

GOODBYE_RESPONSES = [
    "Goodbye! Come back if you have more questions about development projects. Allah Hafiz!",
    "Take care! Feel free to return anytime for assistance. Khuda Hafiz!",
]

# ============================================================================
# CLARIFICATION RESPONSES (Vague queries - need more detail)
# ============================================================================

CLARIFICATION_RESPONSES = [
    """I'd be happy to help, but I need a bit more detail about your question.

Could you please specify what you'd like to know? For example:
• **PC-I requirements** - "What documents are needed for PC-I?"
• **Approval limits** - "What is the DDWP approval limit?"
• **Processes** - "How does project revision work?"
• **Definitions** - "What is ECNEC?"

What specifically would you like to know?""",

    """Your question is a bit vague. To give you accurate information, could you clarify:

• Are you asking about a **specific proforma** (PC-I, II, III, IV, V)?
• Do you need information about **approval limits** or **processes**?
• Are you looking for a **definition** or **procedure**?

Please provide more details so I can assist you better.""",

    """I want to make sure I answer correctly! Could you be more specific?

Try asking something like:
• "What is the purpose of PC-I?"
• "What is the ECNEC approval threshold?"
• "How do I submit a project for CDWP approval?"

What exactly would you like to know?"""
]

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

OFFSCOPE_INAPPROPRIATE_RESPONSE = """⚠️ **Inappropriate Request**

This is a professional assistant for Pakistan's Ministry of Planning, Development & Special Initiatives.

I only answer questions about the Manual for Development Projects 2024, including:
- PC-I through PC-V proforma requirements
- Project approval processes (DDWP/CDWP/ECNEC)
- Budget allocation and monitoring

Please keep interactions professional and relevant."""

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
        subcategory: "medical", "sports", "politics", "entertainment", "inappropriate", "general_knowledge", or "generic"
        
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
    elif subcategory == "inappropriate":
        return OFFSCOPE_INAPPROPRIATE_RESPONSE
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


def get_greeting_response(query: str = "") -> str:
    """
    Get appropriate greeting response.
    
    Args:
        query: Original query to detect thanks/goodbye
        
    Returns:
        Random greeting response (no RAG, no citations)
    """
    q_lower = query.lower()
    if any(w in q_lower for w in ["thank", "thx", "ty"]):
        return random.choice(THANKS_RESPONSES)
    elif any(w in q_lower for w in ["bye", "goodbye", "see you", "take care"]):
        return random.choice(GOODBYE_RESPONSES)
    else:
        return random.choice(GREETING_RESPONSES)


def get_clarification_response() -> str:
    """
    Get a response asking for clarification on vague queries.
    
    Returns:
        Random clarification prompt (no RAG, no citations)
    """
    return random.choice(CLARIFICATION_RESPONSES)


def get_guardrail_response(classification_class: str, subcategory: Optional[str] = None, query: str = "") -> str:
    """
    v2.5.0: Unified guardrail response generator.
    
    Args:
        classification_class: "off_scope", "red_line", "abusive", "greeting", or "ambiguous"
        subcategory: Optional subcategory for specific response
        query: Original query (used for greeting detection)
        
    Returns:
        Static response string (no RAG, no citations)
    """
    if classification_class == "greeting":
        return get_greeting_response(query)
    elif classification_class == "ambiguous":
        return get_clarification_response()
    elif classification_class == "red_line":
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
