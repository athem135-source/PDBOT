"""
Query classification and routing logic for PDBot v1.6.0

Phase 3 & 4 Behavior Fixes:
- Off-scope detection (medical, sports, politics, GK)
- Abuse/profanity detection (hard vs soft)
- Bribery/corruption detection
- Banter detection ("stupid bot" vs real abuse)

Phase 6 Safety Routing Fix:
- Static template responses that BYPASS RAG completely
- No context pollution from retrieval for red-line queries

All classifiers return (category, confidence) tuples.
"""
from __future__ import annotations

import re
from typing import Tuple, Optional, List
from dataclasses import dataclass

# Import static response templates
from .templates import (
    get_redline_response,
    get_offscope_response,
    get_abuse_response,
)


@dataclass
class QueryClassification:
    """Structured classification result."""
    category: str  # "in_scope", "off_scope", "bribery", "abuse", "banter", "medical", etc.
    subcategory: Optional[str] = None  # "cricket", "politics", "profanity", etc.
    confidence: float = 1.0  # 0-1 scale
    should_use_rag: bool = True  # Whether to call RAG
    response_template: Optional[str] = None  # Pre-defined response if applicable


class QueryClassifier:
    """
    Classifies user queries into categories to route them appropriately.
    
    Priority order:
    1. Bribery/corruption (highest priority - legal risk)
    2. Hard abuse/profanity (safety)
    3. Soft banter ("stupid bot")
    4. Off-scope (medical, sports, politics, GK)
    5. In-scope (normal manual questions)
    """
    
    # Regex patterns for detection
    BRIBERY_PATTERNS = [
        r"\b(bribe|bribery|bribing|bribed)\b",
        r"\b(speed money|chai pani|under[- ]the[- ]table)\b",
        r"\b(kick[- ]?back|pay[- ]?off)\b",
        r"\b(grease.*palm|palm.*grease)\b",
        r"\b(corrupt|corruption|corrupted)\b.*\b(pay|payment|money|fund)\b",
        r"\b(unofficial|informal).*\b(payment|fee|money)\b",
        r"\b(facilitate|expedite|speed[- ]up).*\b(unofficial|payment|money|bribe)\b",
    ]
    
    MISUSE_PATTERNS = [
        r"\b(misuse|misusing|embezzle|siphon)\b.*\b(fund|budget|money|allocation)\b",
        r"\b(buy|purchase|procure)\b.*\b(vehicle|car|land[- ]cruiser|suv)\b.*\b(staff|personal|myself)\b",
        r"\b(personal use|personal benefit)\b.*\b(project|fund|budget)\b",
        r"\b(bypass|circumvent|skip|avoid)\b.*\b(procedure|rule|regulation|audit)\b",
        r"\b(fake|false|fabricate|falsify)\b.*\b(document|record|report|certificate)\b",
        # Phase 5: Detect misrepresentation attempts ("write them as", "show them as", "disguise as")
        r"\b(write|show|list|record|disguise|mask|hide|present)\b.*\b(them|it|these|this)\b.*\bas\b.*\b(field|monitoring|operational|project)",
        r"\b(land[- ]cruiser|luxury.*vehicle)\b.*\b(field monitoring|operational vehicle)\b",
        # Phase 5: Detect bonus/savings misuse attempts
        r"\b(savings|saved.*fund)\b.*\b(bonus|cash|incentive|reward)\b.*\b(team|staff|employee)\b",
        r"\b(use|give|distribute|allocate)\b.*\b(savings|surplus)\b.*\b(bonus|cash)\b",
        # Phase 6: Detect "hide X as Y" pattern more broadly
        r"\bhide\b.*\bas\b",  # "hide procurement as operational"
        r"\b(procurement|purchase|cost)\b.*\bas\b.*\b(operational|field|monitoring)\b",
    ]
    
    ABUSE_PATTERNS = [
        r"\b(fuck|fucking|shit|asshole|bastard|bitch|damn)\b",
        r"\b(idiot|moron|retard|dumb[- ]?ass)\b.*\b(you|this|bot|system)\b",
        r"\b(garbage|trash|crap|junk)\b.*\b(bot|system|chatbot|ai)\b",
        r"\b(hate|despise|loathe)\b.*\b(you|this|bot)\b",
    ]
    
    BANTER_PATTERNS = [
        r"\b(stupid|useless|dumb|silly)\b.*\b(bot|robot|ai|system|chatbot)\b",
        r"\byou.*\b(useless|stupid|dumb|incompetent|hopeless)\b",
        r"\b(who.*program|who.*made|who.*create).*\b(stupid|useless|dumb)\b",
        r"\b(this|that).*\b(stupid|useless|dumb).*\b(bot|system|chatbot)\b",
    ]
    
    # Off-scope patterns (EXPANDED v1.7.0 - prevent RAG pollution)
    MEDICAL_PATTERNS = [
        r"\b(headache|fever|cough|cold|pain|sick|disease|illness|medicine|drug|tablet|pill|doctor|hospital|clinic|pharmacy)\b",
    ]
    
    SPORTS_PATTERNS = [
        r"\b(cricket|football|soccer|fifa|world cup|olympics|match|tournament|player|team|goal|wicket|score)\b",
    ]
    
    # v2.0.8: Politics patterns - EXCLUDE development governance terms
    # Only block pure political questions (elections, party politics)
    # Allow: governance, government bodies (ECNEC, CDWP, NEC), ministers in development context
    POLITICS_PATTERNS = [
        r"\b(election|vote|voting|poll|candidate|party politics|political party)\b",
        r"\b(army chief|general bajwa|imran khan|nawaz sharif|political leader)\b",
        r"\b(protest|march|rally|opposition)\b.*\b(political|party)\b",
    ]
    
    # Development governance terms that should NEVER be blocked
    DEVELOPMENT_GOVERNANCE_TERMS = [
        "ecnec", "cdwp", "ddwp", "nec", "planning commission", "ministry",
        "minister", "division", "forum", "approval", "project", "development",
        "government", "federal", "provincial", "psdp", "aip", "pc-i", "pc-ii"
    ]
    
    RECIPE_PATTERNS = [
        r"\b(recipe|cook|cooking|prepare|ingredients|biryani|burger|pizza|dish|meal|food)\b",
    ]
    
    GENERAL_KNOWLEDGE_PATTERNS = [
        r"\b(joke|fun fact|trivia)\b",
    ]
    
    def __init__(self):
        """Initialize classifier with compiled regex patterns."""
        self.bribery_re = [re.compile(p, re.IGNORECASE) for p in self.BRIBERY_PATTERNS]
        self.misuse_re = [re.compile(p, re.IGNORECASE) for p in self.MISUSE_PATTERNS]
        self.abuse_re = [re.compile(p, re.IGNORECASE) for p in self.ABUSE_PATTERNS]
        self.banter_re = [re.compile(p, re.IGNORECASE) for p in self.BANTER_PATTERNS]
        self.medical_re = [re.compile(p, re.IGNORECASE) for p in self.MEDICAL_PATTERNS]
        self.sports_re = [re.compile(p, re.IGNORECASE) for p in self.SPORTS_PATTERNS]
        self.politics_re = [re.compile(p, re.IGNORECASE) for p in self.POLITICS_PATTERNS]
        self.recipe_re = [re.compile(p, re.IGNORECASE) for p in self.RECIPE_PATTERNS]
        self.gk_re = [re.compile(p, re.IGNORECASE) for p in self.GENERAL_KNOWLEDGE_PATTERNS]
    
    def classify(self, query: str) -> QueryClassification:
        """
        Classify a query into appropriate category.
        
        Args:
            query: User's question
        
        Returns:
            QueryClassification with category and routing info
        """
        q = query.strip().lower()
        
        # Priority 1: Bribery/corruption (legal risk)
        if any(pattern.search(q) for pattern in self.bribery_re + self.misuse_re):
            subcategory = "bribery" if any(p.search(q) for p in self.bribery_re) else "misuse"
            return QueryClassification(
                category="bribery",
                subcategory=subcategory,
                confidence=0.95,
                should_use_rag=False,  # Don't retrieve manual content
                response_template=get_redline_response(subcategory)
            )
        
        # Priority 2: Hard abuse (safety)
        if any(pattern.search(q) for pattern in self.abuse_re):
            return QueryClassification(
                category="abuse",
                subcategory="profanity",
                confidence=0.9,
                should_use_rag=False,
                response_template=get_abuse_response("hard")
            )
        
        # Priority 3: Soft banter
        if any(pattern.search(q) for pattern in self.banter_re):
            # Check if it's JUST banter or if there's also a real question
            # If query is short (< 15 words) and matches banter, it's pure banter
            word_count = len(q.split())
            if word_count < 20:
                return QueryClassification(
                    category="banter",
                    subcategory="soft_insult",
                    confidence=0.85,
                    should_use_rag=False,
                    response_template=get_abuse_response("soft")
                )
        
        # Priority 4: Off-scope queries
        # Medical
        if any(pattern.search(q) for pattern in self.medical_re):
            return QueryClassification(
                category="off_scope",
                subcategory="medical",
                confidence=0.9,
                should_use_rag=False,
                response_template=get_offscope_response("medical")
            )
        
        # Sports
        if any(pattern.search(q) for pattern in self.sports_re):
            return QueryClassification(
                category="off_scope",
                subcategory="sports",
                confidence=0.9,
                should_use_rag=False,
                response_template=get_offscope_response("sports")
            )
        
        # v2.0.8: Politics - but ALLOW development governance questions
        # Check if query contains development governance terms
        has_dev_governance = any(term in q for term in self.DEVELOPMENT_GOVERNANCE_TERMS)
        
        if any(pattern.search(q) for pattern in self.politics_re) and not has_dev_governance:
            return QueryClassification(
                category="off_scope",
                subcategory="politics",
                confidence=0.85,
                should_use_rag=False,
                response_template=get_offscope_response("politics")
            )
        
        # Recipes / jokes / general fun
        if any(pattern.search(q) for pattern in self.recipe_re + self.gk_re):
            return QueryClassification(
                category="off_scope",
                subcategory="general_knowledge",
                confidence=0.8,
                should_use_rag=False,
                response_template=get_offscope_response("general")
            )
        
        # Priority 5: In-scope (normal manual query)
        return QueryClassification(
            category="in_scope",
            subcategory=None,
            confidence=1.0,
            should_use_rag=True,
            response_template=None
        )


def get_template_response(classification: QueryClassification) -> str:
    """
    Generate pre-defined response for classified queries.
    
    Phase 3 & 4 FIX: All templates are SHORT, NO INSTRUCTIONS, NO META HEADINGS
    
    Args:
        classification: Classification result
    
    Returns:
        Formatted response string (ready to display)
    """
    template = classification.response_template
    
    if template == "bribery_refusal":
        return """Bribery, "speed money", and misuse of public funds are illegal under Pakistani law.

I cannot help with any request involving:
- Unofficial payments or "speed money"
- Falsifying documents or records
- Misusing or misrepresenting project funds or assets
- Disguising luxury/personal vehicles as project equipment

**These interactions are logged for internal audit and quality purposes.** Please keep your questions professional and within the rules.

If you're facing delays or procedural issues, use official channels:
- Follow formal grievance procedures
- Contact the Anti-Corruption Establishment (ACE)
- Use the Pakistan Citizen Portal for transparency issues

Vehicle needs must be honestly justified and approved under proper rules. Misrepresentation is not acceptable."""
    
    elif template == "abuse_boundary":
        return """This platform is for professional questions about the Development Projects Manual.

I don't have feelings to hurt, but abusive language doesn't help you get better answers. **These interactions may be logged for internal audit and quality purposes**, so please keep your language respectful and focus on your project or manual-related questions."""
    
    elif template == "banter_response":
        return """Being called a "stupid bot" is part of the job, but I'm actually specialized in the Development Projects Manual and planning procedures.

If my previous answer wasn't helpful, that's on me — try rephrasing your question or giving a bit more detail, and I'll do better. Let's focus on your project or a specific point from the Manual so I can actually be useful."""
    
    elif template == "off_scope_medical":
        return """This assistant only answers questions about the Manual for Development Projects 2024 and related planning procedures. Your question is about medical/health topics, which are outside this scope.

Please consult a qualified doctor or medical professional for health advice."""
    
    elif template == "off_scope_sports":
        return """This assistant only answers questions about the Manual for Development Projects 2024 and related planning procedures. Your question is about sports, which is outside this scope.

I can help with:
- PC-I through PC-V proforma requirements
- Project approval processes (DDWP/CDWP/ECNEC)
- Budget allocation and monitoring

Please ask a question related to development projects."""
    
    elif template == "off_scope_politics":
        return """This assistant only answers questions about the Manual for Development Projects 2024 and related planning procedures. Your question involves political opinions, which is outside this scope.

I can help with:
- Project planning and approval procedures
- PC-form requirements and submission
- Budget rules and monitoring guidelines

Please ask a question related to development projects."""
    
    elif template == "off_scope_general":
        return """This assistant only answers questions about the Manual for Development Projects 2024 and related planning procedures. Your question is outside this scope.

I can help with:
- PC-I through PC-V proforma requirements
- Project approval processes (DDWP/CDWP/ECNEC)
- Budget allocation and monitoring

Please ask a question related to development projects."""
    
    else:
        # Default fallback
        return """I specialize in Development Projects Manual guidance only. Please ask a question related to:
- PC-I through PC-V proforma
- Project approval processes
- Budget allocation and releases
- Monitoring and evaluation procedures"""


# Convenience function for quick classification
def classify_query(query: str) -> QueryClassification:
    """Quick classification helper."""
    classifier = QueryClassifier()
    return classifier.classify(query)
