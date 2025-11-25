"""
Critical Numeric Constants for PDBot
=====================================
ANTI-HALLUCINATION FIX: Hardcoded approval limits and thresholds
to prevent the bot from inventing incorrect numbers.

These values are sourced from the Manual for Development Projects 2024.
"""

# Approval Limits (Primary Reference)
APPROVAL_LIMITS = {
    "DDWP": {
        "full_name": "District Development Working Party",
        "limit": "Up to Rs. 75 million (Rs. 7.5 crore)",
        "limit_numeric": 75_000_000,
        "description": "District-level approval authority for smaller projects",
    },
    "PDWP": {
        "full_name": "Provincial Development Working Party",
        "limit": "Up to Rs. 2,000 million (Rs. 2 billion)",
        "limit_numeric": 2_000_000_000,
        "description": "Provincial-level approval for medium-scale projects",
    },
    "CDWP": {
        "full_name": "Central Development Working Party",
        "limit": "Rs. 2 billion to Rs. 10 billion",
        "limit_numeric_min": 2_000_000_000,
        "limit_numeric_max": 10_000_000_000,
        "description": "Federal-level approval for large projects",
    },
    "ECNEC": {
        "full_name": "Executive Committee of the National Economic Council",
        "limit": "Above Rs. 10 billion or major policy decisions",
        "limit_numeric_min": 10_000_000_000,
        "description": "Highest approval authority for mega projects and policy matters",
    },
}

# Additional Numeric Rules
NUMERIC_RULES = {
    # PC Document Preparation
    "pc1_preparation_time": {
        "value": "Typically 3-6 months depending on project complexity",
        "keywords": ["pc-1", "pc1", "preparation", "time", "how long"],
    },
    "pc1_validity": {
        "value": "PC-I remains valid until project completion or major revision required",
        "keywords": ["pc-1", "pc1", "validity", "valid", "expire"],
    },
    
    # Consultant Selection
    "consultant_qcbs_ratio": {
        "value": "Quality-Cost Based Selection: 80:20 or 90:10 (quality:cost)",
        "keywords": ["qcbs", "consultant", "selection", "ratio", "quality cost"],
    },
    
    # Procurement Thresholds (indicative - check latest PPRA rules)
    "procurement_open_tender": {
        "value": "Generally above Rs. 2 million requires open competitive bidding",
        "keywords": ["procurement", "tender", "bidding", "threshold"],
    },
    
    # Project Monitoring
    "progress_report_frequency": {
        "value": "Quarterly progress reports during implementation",
        "keywords": ["progress", "report", "frequency", "monitoring"],
    },
    
    # Financial Management
    "advance_payment_limit": {
        "value": "Typically 10-15% advance payment subject to bank guarantee",
        "keywords": ["advance", "payment", "upfront", "mobilization"],
    },
    
    # Land Acquisition
    "land_acquisition_compensation": {
        "value": "As per Land Acquisition Act 1894 (amended) - market value plus 15-25% solatium",
        "keywords": ["land", "compensation", "acquisition", "solatium"],
    },
}

# Numeric Query Keywords (triggers safety check)
NUMERIC_QUERY_KEYWORDS = [
    "limit", "threshold", "ceiling", "maximum", "minimum",
    "cost", "budget", "allocation", "amount",
    "rs", "rupees", "million", "billion", "crore", "lakh",
    "how much", "how many", "percentage", "percent", "%",
    "duration", "time", "period", "validity", "years", "months",
]

def get_approval_authority(amount_rs: float) -> str:
    """
    Determine approval authority based on project cost.
    
    Args:
        amount_rs: Project cost in Pakistani Rupees
        
    Returns:
        Name of approval authority (DDWP, PDWP, CDWP, ECNEC)
    """
    if amount_rs <= APPROVAL_LIMITS["DDWP"]["limit_numeric"]:
        return "DDWP"
    elif amount_rs <= APPROVAL_LIMITS["PDWP"]["limit_numeric"]:
        return "PDWP"
    elif amount_rs <= APPROVAL_LIMITS["CDWP"]["limit_numeric_max"]:
        return "CDWP"
    else:
        return "ECNEC"

def format_approval_limit(authority: str) -> str:
    """
    Format approval limit for display.
    
    Args:
        authority: DDWP, PDWP, CDWP, or ECNEC
        
    Returns:
        Formatted string with full name and limit
    """
    if authority not in APPROVAL_LIMITS:
        return "Unknown authority"
    
    info = APPROVAL_LIMITS[authority]
    return f"{info['full_name']} ({authority}): {info['limit']}"
