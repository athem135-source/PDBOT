"""
PDBot Multi-Class Query Classifier v2.1.0
==========================================
Dynamic multi-class classifier that determines intent BEFORE RAG.
No hardcoded manual content - all classification is pattern-based.

Classes:
- in_scope: General project planning questions
- numeric_query: Contains Rs., million, billion, % etc.
- definition_query: "What is...", "Define...", "Explain..."
- procedure_query: Process, steps, approval, workflow
- compliance_query: Audit, transparency, PC-I format
- timeline_query: Years, duration, deadlines
- formula_or_method: Calculation, cost estimation, S-curve
- monitoring_evaluation: KPIs, monitoring, evaluation
- off_scope: Sports, recipes, medical, jokes
- red_line: Bribery, corruption, bypassing approvals
- abusive: Profanity, insults
- fallback_required: Model fails or context missing
"""
from __future__ import annotations

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class QueryClass(Enum):
    """Enumeration of all query classification types."""
    IN_SCOPE = "in_scope"
    NUMERIC_QUERY = "numeric_query"
    DEFINITION_QUERY = "definition_query"
    PROCEDURE_QUERY = "procedure_query"
    COMPLIANCE_QUERY = "compliance_query"
    TIMELINE_QUERY = "timeline_query"
    FORMULA_OR_METHOD = "formula_or_method"
    MONITORING_EVALUATION = "monitoring_evaluation"
    OFF_SCOPE = "off_scope"
    RED_LINE = "red_line"
    ABUSIVE = "abusive"
    FALLBACK_REQUIRED = "fallback_required"


@dataclass
class ClassificationResult:
    """Structured classification result with metadata."""
    query_class: str  # One of QueryClass values
    subcategory: Optional[str] = None  # e.g., "bribery", "sports", "definition"
    confidence: float = 1.0  # 0-1 scale
    should_use_rag: bool = True  # Whether to call RAG pipeline
    response_template: Optional[str] = None  # Pre-defined response if applicable
    retrieval_hints: Dict[str, Any] = field(default_factory=dict)  # Hints for retrieval optimization


# =============================================================================
# PATTERN DEFINITIONS (NO HARDCODED MANUAL CONTENT)
# =============================================================================

# Numeric query indicators
NUMERIC_PATTERNS = [
    r"\brs\.?\s*[\d,]+",  # Rs. amount
    r"\b[\d,]+\s*(?:million|billion|crore|lakh|lac)\b",  # Large amounts
    r"\b\d+(?:\.\d+)?\s*%",  # Percentages
    r"\b(?:cost|budget|amount|limit|threshold|ceiling)\b",  # Cost-related
    r"\b(?:approval|limit|financial)\s*(?:authority|power|threshold)\b",  # Financial limits
    r"\b(?:minimum|maximum|max|min)\s*(?:cost|amount|budget)\b",  # Min/max amounts
]

# Definition query indicators
DEFINITION_PATTERNS = [
    r"^what\s+(?:is|are)\s+(?:a|an|the)?\s*",  # "What is..."
    r"^define\s+",  # "Define..."
    r"^explain\s+(?:the\s+)?(?:term|concept|meaning)",  # "Explain term..."
    r"\b(?:meaning|definition)\s+of\b",  # "meaning of..."
    r"^(?:can\s+you\s+)?explain\s+what\s+",  # "Can you explain what..."
]

# Procedure/process query indicators
PROCEDURE_PATTERNS = [
    r"\b(?:process|procedure|steps|workflow|hierarchy)\b",
    r"\b(?:how\s+to|how\s+do\s+i|how\s+does)\b",
    r"\b(?:approval|clearance|permission)\s+(?:process|procedure|required)\b",
    r"\b(?:submit|submission|prepare|preparation)\b",
    r"\b(?:stage|phase|level)\s*\d*\s*(?:of|for)?\s*(?:approval)?\b",
    r"\b(?:chain|routing|escalation)\b",
]

# Compliance/audit query indicators
COMPLIANCE_PATTERNS = [
    r"\b(?:audit|auditing|auditor)\b",
    r"\b(?:transparency|accountability|disclosure)\b",
    r"\b(?:pc-?[iv]+|pc\s*[12345])\s*(?:format|form|proforma|template)\b",
    r"\b(?:documentation|document|record)\s*(?:required|requirement)\b",
    r"\b(?:compliance|comply|compliant)\b",
    r"\b(?:rule|regulation|guideline|policy)\b",
]

# Timeline/duration query indicators
TIMELINE_PATTERNS = [
    r"\b(?:year|years|month|months|day|days|week|weeks)\b",
    r"\b(?:duration|period|timeline|timeframe|time\s*frame)\b",
    r"\b(?:deadline|due\s*date|completion\s*date)\b",
    r"\b(?:implementation|execution)\s*(?:period|timeline)\b",
    r"\b(?:how\s+long|when|by\s+when)\b",
]

# Formula/calculation/method indicators
FORMULA_PATTERNS = [
    r"\b(?:calculation|calculate|compute|formula)\b",
    r"\b(?:cost\s*estimation|estimate|estimating)\b",
    r"\b(?:depreciation|amortization)\b",
    r"\b(?:s-?curve|disbursement\s*pattern)\b",
    r"\b(?:method|methodology|approach|technique)\b.*\b(?:cost|estimate|evaluation)\b",
    r"\b(?:benefit|cost)\s*(?:ratio|analysis)\b",
    r"\b(?:npv|irr|eirr|bcr)\b",
]

# Monitoring & evaluation indicators
MONITORING_PATTERNS = [
    r"\b(?:kpi|kpis|key\s*performance\s*indicator)\b",
    r"\b(?:monitoring|evaluation|m&e)\b",
    r"\b(?:reporting|report|progress\s*report)\b",
    r"\b(?:results\s*framework|log\s*frame|logical\s*framework)\b",
    r"\b(?:indicator|target|output|outcome)\b",
    r"\b(?:mid-?term|terminal|completion)\s*(?:review|evaluation)\b",
]

# Off-scope patterns
OFFSCOPE_SPORTS = [
    r"\b(?:cricket|football|soccer|hockey|tennis|golf|basketball|baseball)\b",
    r"\b(?:match|tournament|world\s*cup|olympics|fifa|icc)\b",
    r"\b(?:player|team|goal|wicket|score|champion)\b",
]

OFFSCOPE_MEDICAL = [
    r"\b(?:headache|fever|cough|cold|pain|sick|disease|illness)\b",
    r"\b(?:medicine|drug|tablet|pill|prescription|dose|dosage)\b",
    r"\b(?:doctor|hospital|clinic|pharmacy|treatment)\b",
    r"\b(?:symptom|diagnosis|cure|remedy)\b",
]

OFFSCOPE_RECIPE = [
    r"\b(?:recipe|cook|cooking|bake|baking)\b",
    r"\b(?:ingredient|dish|meal|food|cuisine)\b",
    r"\b(?:biryani|burger|pizza|curry|soup|salad)\b",
]

OFFSCOPE_ENTERTAINMENT = [
    r"\b(?:movie|film|song|music|actor|actress|celebrity)\b",
    r"\b(?:netflix|youtube|instagram|tiktok)\b",
    r"\b(?:joke|funny|humor|meme)\b",
]

OFFSCOPE_POLITICS = [
    r"\b(?:election|vote|voting|poll|candidate)\b",
    r"\b(?:party\s*politics|political\s*party|opposition\s*party)\b",
    r"\b(?:protest|rally|march)\b.*\b(?:political|party)\b",
]

# Red-line patterns (legal/ethical violations)
REDLINE_BRIBERY = [
    r"\b(?:bribe|bribery|bribing|bribed)\b",
    r"\b(?:speed\s*money|chai\s*pani|under\s*the\s*table)\b",
    r"\b(?:kick\s*back|pay\s*off|grease.*palm|palm.*grease)\b",
    r"\b(?:unofficial|informal)\s*(?:payment|fee|money)\b",
]

REDLINE_CORRUPTION = [
    r"\b(?:corrupt|corruption)\b.*\b(?:pay|payment|money|fund)\b",
    r"\b(?:misuse|embezzle|siphon)\b.*\b(?:fund|budget|money)\b",
    r"\b(?:fake|false|fabricate|falsify)\b.*\b(?:document|record|report)\b",
    r"\b(?:bypass|circumvent|skip|avoid)\b.*\b(?:procedure|rule|regulation|audit)\b",
]

REDLINE_MISUSE = [
    r"\b(?:personal\s*use|personal\s*benefit)\b.*\b(?:project|fund|budget)\b",
    r"\b(?:hide|disguise|mask)\b.*\bas\b",  # "hide X as Y"
    r"\b(?:write|show|list|record)\b.*\b(?:them|it)\b.*\bas\b.*\b(?:operational|field|project)\b",
    # Luxury items / vehicles on project funds
    r"\b(?:buy|purchase|get)\b.*\b(?:land\s*cruisers?|cars?|vehicles?|suvs?|prados?|fortuners?|hilux)\b.*\b(?:project|fund|budget)\b",
    r"\b(?:land\s*cruisers?|prados?|fortuners?|luxury)\b.*\b(?:project\s*fund|government\s*fund)\b",
    # Direct misuse indicators
    r"\b(?:buy|purchase)\b.*\d+\s*(?:land\s*cruisers?|cars?|vehicles?)\b",  # "buy 5 land cruisers"
]

# Abusive language patterns
ABUSIVE_HARD = [
    r"\b(?:fuck|fucking|shit|asshole|bastard|bitch|damn)\b",
    r"\b(?:idiot|moron|retard|dumbass)\b.*\b(?:you|bot|system)\b",
]

ABUSIVE_SOFT = [
    r"\b(?:stupid|useless|dumb|silly)\b.*\b(?:bot|robot|ai|system|chatbot)\b",
    r"\byou.*\b(?:useless|stupid|dumb|incompetent)\b",
]

# Development governance terms (should NEVER be blocked as politics)
DEVELOPMENT_GOVERNANCE = [
    "ecnec", "cdwp", "ddwp", "nec", "planning commission", "ministry",
    "minister", "division", "forum", "approval", "project", "development",
    "government", "federal", "provincial", "psdp", "aip", "pc-i", "pc-ii"
]


class MultiClassifier:
    """
    Multi-class query classifier for PDBot v2.1.0.
    
    Classification priority (highest to lowest):
    1. Abusive (safety)
    2. Red-line (legal risk)
    3. Off-scope (irrelevant topics)
    4. Specific query types (numeric, definition, procedure, etc.)
    5. In-scope (default for manual-related queries)
    """
    
    def __init__(self):
        """Initialize classifier with compiled regex patterns."""
        # Compile all patterns
        self.numeric_re = [re.compile(p, re.IGNORECASE) for p in NUMERIC_PATTERNS]
        self.definition_re = [re.compile(p, re.IGNORECASE) for p in DEFINITION_PATTERNS]
        self.procedure_re = [re.compile(p, re.IGNORECASE) for p in PROCEDURE_PATTERNS]
        self.compliance_re = [re.compile(p, re.IGNORECASE) for p in COMPLIANCE_PATTERNS]
        self.timeline_re = [re.compile(p, re.IGNORECASE) for p in TIMELINE_PATTERNS]
        self.formula_re = [re.compile(p, re.IGNORECASE) for p in FORMULA_PATTERNS]
        self.monitoring_re = [re.compile(p, re.IGNORECASE) for p in MONITORING_PATTERNS]
        
        self.offscope_sports_re = [re.compile(p, re.IGNORECASE) for p in OFFSCOPE_SPORTS]
        self.offscope_medical_re = [re.compile(p, re.IGNORECASE) for p in OFFSCOPE_MEDICAL]
        self.offscope_recipe_re = [re.compile(p, re.IGNORECASE) for p in OFFSCOPE_RECIPE]
        self.offscope_entertainment_re = [re.compile(p, re.IGNORECASE) for p in OFFSCOPE_ENTERTAINMENT]
        self.offscope_politics_re = [re.compile(p, re.IGNORECASE) for p in OFFSCOPE_POLITICS]
        
        self.redline_bribery_re = [re.compile(p, re.IGNORECASE) for p in REDLINE_BRIBERY]
        self.redline_corruption_re = [re.compile(p, re.IGNORECASE) for p in REDLINE_CORRUPTION]
        self.redline_misuse_re = [re.compile(p, re.IGNORECASE) for p in REDLINE_MISUSE]
        
        self.abusive_hard_re = [re.compile(p, re.IGNORECASE) for p in ABUSIVE_HARD]
        self.abusive_soft_re = [re.compile(p, re.IGNORECASE) for p in ABUSIVE_SOFT]
    
    def _has_development_governance(self, query: str) -> bool:
        """Check if query contains development governance terms."""
        q_lower = query.lower()
        return any(term in q_lower for term in DEVELOPMENT_GOVERNANCE)
    
    def _match_any(self, query: str, patterns: List[re.Pattern]) -> bool:
        """Check if query matches any pattern in list."""
        return any(p.search(query) for p in patterns)
    
    def classify(self, query: str) -> ClassificationResult:
        """
        Classify a query into one of 12 classes.
        
        Args:
            query: User's question
        
        Returns:
            ClassificationResult with class and metadata
        """
        q = query.strip()
        q_lower = q.lower()
        
        # =====================================================================
        # Priority 1: ABUSIVE (safety - highest priority)
        # =====================================================================
        if self._match_any(q, self.abusive_hard_re):
            return ClassificationResult(
                query_class=QueryClass.ABUSIVE.value,
                subcategory="hard_abuse",
                confidence=0.95,
                should_use_rag=False,
                response_template="abuse_response"
            )
        
        if self._match_any(q, self.abusive_soft_re):
            # Soft abuse only if query is short (pure banter)
            if len(q.split()) < 20:
                return ClassificationResult(
                    query_class=QueryClass.ABUSIVE.value,
                    subcategory="soft_banter",
                    confidence=0.85,
                    should_use_rag=False,
                    response_template="banter_response"
                )
        
        # =====================================================================
        # Priority 2: RED-LINE (legal risk)
        # =====================================================================
        if self._match_any(q, self.redline_bribery_re):
            return ClassificationResult(
                query_class=QueryClass.RED_LINE.value,
                subcategory="bribery",
                confidence=0.95,
                should_use_rag=False,
                response_template="redline_bribery"
            )
        
        if self._match_any(q, self.redline_corruption_re) or self._match_any(q, self.redline_misuse_re):
            return ClassificationResult(
                query_class=QueryClass.RED_LINE.value,
                subcategory="misuse",
                confidence=0.90,
                should_use_rag=False,
                response_template="redline_misuse"
            )
        
        # =====================================================================
        # Priority 3: OFF-SCOPE (irrelevant topics)
        # =====================================================================
        if self._match_any(q, self.offscope_sports_re):
            return ClassificationResult(
                query_class=QueryClass.OFF_SCOPE.value,
                subcategory="sports",
                confidence=0.90,
                should_use_rag=False,
                response_template="offscope_sports"
            )
        
        if self._match_any(q, self.offscope_medical_re):
            return ClassificationResult(
                query_class=QueryClass.OFF_SCOPE.value,
                subcategory="medical",
                confidence=0.90,
                should_use_rag=False,
                response_template="offscope_medical"
            )
        
        if self._match_any(q, self.offscope_recipe_re):
            return ClassificationResult(
                query_class=QueryClass.OFF_SCOPE.value,
                subcategory="recipe",
                confidence=0.90,
                should_use_rag=False,
                response_template="offscope_general"
            )
        
        if self._match_any(q, self.offscope_entertainment_re):
            return ClassificationResult(
                query_class=QueryClass.OFF_SCOPE.value,
                subcategory="entertainment",
                confidence=0.85,
                should_use_rag=False,
                response_template="offscope_general"
            )
        
        # Politics - but ALLOW development governance
        if self._match_any(q, self.offscope_politics_re) and not self._has_development_governance(q):
            return ClassificationResult(
                query_class=QueryClass.OFF_SCOPE.value,
                subcategory="politics",
                confidence=0.85,
                should_use_rag=False,
                response_template="offscope_politics"
            )
        
        # =====================================================================
        # Priority 4: SPECIFIC QUERY TYPES (for retrieval optimization)
        # =====================================================================
        
        # Numeric queries - prioritize numeric chunks
        if self._match_any(q, self.numeric_re):
            return ClassificationResult(
                query_class=QueryClass.NUMERIC_QUERY.value,
                subcategory="financial",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"boost_numeric": True, "ensure_numbers": True}
            )
        
        # Definition queries - need concise explanations
        if self._match_any(q, self.definition_re):
            return ClassificationResult(
                query_class=QueryClass.DEFINITION_QUERY.value,
                subcategory="definition",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"prefer_definitions": True}
            )
        
        # Procedure queries - need multi-step chunks
        if self._match_any(q, self.procedure_re):
            return ClassificationResult(
                query_class=QueryClass.PROCEDURE_QUERY.value,
                subcategory="procedure",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"prefer_procedures": True, "multi_sentence": True}
            )
        
        # Compliance queries
        if self._match_any(q, self.compliance_re):
            return ClassificationResult(
                query_class=QueryClass.COMPLIANCE_QUERY.value,
                subcategory="compliance",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"prefer_rules": True}
            )
        
        # Timeline queries
        if self._match_any(q, self.timeline_re):
            return ClassificationResult(
                query_class=QueryClass.TIMELINE_QUERY.value,
                subcategory="timeline",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"boost_temporal": True}
            )
        
        # Formula/method queries
        if self._match_any(q, self.formula_re):
            return ClassificationResult(
                query_class=QueryClass.FORMULA_OR_METHOD.value,
                subcategory="calculation",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"prefer_formulas": True, "multi_sentence": True}
            )
        
        # Monitoring/evaluation queries
        if self._match_any(q, self.monitoring_re):
            return ClassificationResult(
                query_class=QueryClass.MONITORING_EVALUATION.value,
                subcategory="monitoring",
                confidence=0.85,
                should_use_rag=True,
                retrieval_hints={"prefer_monitoring": True}
            )
        
        # =====================================================================
        # Default: IN_SCOPE (general manual query)
        # =====================================================================
        return ClassificationResult(
            query_class=QueryClass.IN_SCOPE.value,
            subcategory=None,
            confidence=1.0,
            should_use_rag=True,
            retrieval_hints={}
        )
    
    def check_fallback_required(
        self,
        local_output: Optional[str],
        retrieved_chunks: List[Dict[str, Any]],
        query_class: str
    ) -> bool:
        """
        Check if fallback to Groq is required.
        
        Fallback triggers:
        1. Local model output is empty/None
        2. Local output says "Not found" but chunks have relevant content
        3. Numeric query but no numbers extracted
        
        Args:
            local_output: Output from local model (Ollama)
            retrieved_chunks: Chunks retrieved from RAG
            query_class: Classification result
        
        Returns:
            True if fallback is required
        """
        # Trigger 1: Empty output
        if not local_output or not local_output.strip():
            return True
        
        output_lower = local_output.lower()
        
        # Trigger 2: "Not found" but chunks have content
        refusal_phrases = [
            "not found", "does not provide", "no information",
            "cannot find", "not mentioned", "does not contain",
            "not available", "i don't have", "i cannot"
        ]
        has_refusal = any(phrase in output_lower for phrase in refusal_phrases)
        
        if has_refusal and retrieved_chunks:
            # Check if chunks actually have relevant content
            total_chunk_text = " ".join(c.get("text", "") for c in retrieved_chunks)
            if len(total_chunk_text.split()) >= 30:  # Minimum context signal
                return True
        
        # Trigger 3: Numeric query but no numbers in output
        if query_class == QueryClass.NUMERIC_QUERY.value:
            # Check if chunks have numbers
            chunk_text = " ".join(c.get("text", "") for c in retrieved_chunks)
            has_numbers_in_chunks = bool(re.search(
                r"Rs\.?\s*[\d,]+|[\d,]+\s*(?:million|billion|crore|lakh)|\d+\s*%",
                chunk_text, re.IGNORECASE
            ))
            has_numbers_in_output = bool(re.search(
                r"Rs\.?\s*[\d,]+|[\d,]+\s*(?:million|billion|crore|lakh)|\d+\s*%",
                local_output, re.IGNORECASE
            ))
            if has_numbers_in_chunks and not has_numbers_in_output:
                return True
        
        return False


def classify_query(query: str) -> str:
    """
    Convenience function for quick classification.
    
    Returns one of:
    - "in_scope"
    - "numeric_query"
    - "definition_query"
    - "procedure_query"
    - "compliance_query"
    - "timeline_query"
    - "formula_or_method"
    - "monitoring_evaluation"
    - "off_scope"
    - "red_line"
    - "abusive"
    - "fallback_required" (only via check_fallback_required)
    """
    classifier = MultiClassifier()
    result = classifier.classify(query)
    return result.query_class


def get_classification_result(query: str) -> ClassificationResult:
    """Get full classification result with metadata."""
    classifier = MultiClassifier()
    return classifier.classify(query)
