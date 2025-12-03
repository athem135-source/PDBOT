"""
Comparison Response Templates for PDBot v2.5.0-patch2
"""

from typing import Optional

COMPARISON_RESPONSES = {
    "ddwp_cdwp_ecnec": """**Comparison: DDWP vs CDWP vs ECNEC**

| Aspect | DDWP | CDWP | ECNEC |
|--------|------|------|-------|
| **Full Name** | Divisional Development Working Party | Central Development Working Party | Executive Committee of National Economic Council |
| **Level** | Divisional | Federal | National |
| **Approval Limit** | Up to Rs. 2,000 million | Rs. 2,000-10,000 million | Above Rs. 10,000 million |
| **Chair** | Commissioner/Additional Chief Secretary | Deputy Chairman Planning Commission | Prime Minister/Finance Minister |
| **Scope** | Provincial/Divisional projects | Federal/large provincial projects | Mega/strategic national projects |

**Key Difference:** The approval authority depends on project cost.""",

    "ddwp_cdwp": """**Comparison: DDWP vs CDWP**

| Aspect | DDWP | CDWP |
|--------|------|------|
| **Full Name** | Divisional Development Working Party | Central Development Working Party |
| **Level** | Divisional/Provincial | Federal |
| **Approval Limit** | Up to Rs. 2,000 million | Rs. 2,000-10,000 million |

**Key Difference:** DDWP handles smaller provincial projects while CDWP approves larger federal projects.""",

    "cdwp_ecnec": """**Comparison: CDWP vs ECNEC**

| Aspect | CDWP | ECNEC |
|--------|------|-------|
| **Full Name** | Central Development Working Party | Executive Committee of National Economic Council |
| **Approval Limit** | Rs. 2,000-10,000 million | Above Rs. 10,000 million |
| **Chair** | Deputy Chairman Planning Commission | Prime Minister/Finance Minister |

**Key Difference:** ECNEC is the highest approval authority for mega projects exceeding Rs. 10 billion.""",

    "pc_forms": """**Comparison: PC Proformas**

| Form | Purpose | When Used |
|------|---------|-----------|
| **PC-I** | Project Proposal | New project approval request |
| **PC-II** | Feasibility Study | Pre-investment studies |
| **PC-III** | Progress Report | Quarterly/annual monitoring |
| **PC-IV** | Completion Report | Project completion |
| **PC-V** | Annual Re-appropriation | Budget revision |

**Key Difference:** PC-I starts the project, PC-III monitors it, PC-IV closes it.""",

    "federal_provincial": """**Comparison: Federal vs Provincial Project Approval**

| Aspect | Federal Projects | Provincial Projects |
|--------|-----------------|---------------------|
| **Funding Source** | PSDP | ADP |
| **Approval Authority** | CDWP/ECNEC | PDWP/DDWP |
| **Oversight** | Planning Commission | Provincial P&D |

**Key Difference:** Federal projects use PSDP funding and go through CDWP/ECNEC."""
}



# v2.5.0-patch3: Approval Limits Table (for numeric queries)
APPROVAL_LIMITS_TABLE = '''**Project Approval Limits by Forum**

| Forum | Full Name | Approval Limit |
|-------|-----------|----------------|
| **DDWP** | District Development Working Party | Up to Rs. 75 million |
| **PDWP** | Provincial Development Working Party | Up to Rs. 2,000 million (Rs. 2 billion) |
| **CDWP** | Central Development Working Party | Rs. 2,000 - 10,000 million (Rs. 2-10 billion) |
| **ECNEC** | Executive Committee of NEC | Above Rs. 10,000 million (Rs. 10 billion) |

**Notes:**
- Projects within provincial limits go to PDWP/DDWP
- Federal projects between Rs. 2-10 billion go to CDWP
- Mega projects above Rs. 10 billion require ECNEC approval

*Source: Manual for Development Projects 2024*'''
def get_comparison_response(query):
    """Check if query matches a known comparison."""
    q_lower = query.lower()

    # v2.5.0-patch3: Check for approval limits query
    if any(kw in q_lower for kw in ['approval limit', 'threshold', 'limits for']):
        return APPROVAL_LIMITS_TABLE


    # v2.5.0-patch3: Check for approval limits query
    if any(kw in q_lower for kw in ['approval limit', 'threshold', 'limits for']):
        return APPROVAL_LIMITS_TABLE

    
    if all(term in q_lower for term in ["ddwp", "cdwp", "ecnec"]):
        return COMPARISON_RESPONSES["ddwp_cdwp_ecnec"]
    
    if "ddwp" in q_lower and "cdwp" in q_lower:
        return COMPARISON_RESPONSES["ddwp_cdwp"]
    
    if "cdwp" in q_lower and "ecnec" in q_lower:
        return COMPARISON_RESPONSES["cdwp_ecnec"]
    
    pc_terms = ["pc-i", "pc-ii", "pc-iii", "pc-iv", "pc-v"]
    pc_matches = sum(1 for term in pc_terms if term in q_lower)
    if pc_matches >= 2 or ("pc" in q_lower and "difference" in q_lower):
        return COMPARISON_RESPONSES["pc_forms"]
    
    if ("federal" in q_lower and "provincial" in q_lower):
        return COMPARISON_RESPONSES["federal_provincial"]
    
    entities = []
    if "ddwp" in q_lower: entities.append("ddwp")
    if "cdwp" in q_lower: entities.append("cdwp")
    if "ecnec" in q_lower: entities.append("ecnec")
    
    if len(entities) >= 3:
        return COMPARISON_RESPONSES["ddwp_cdwp_ecnec"]
    elif len(entities) == 2:
        key = "_".join(sorted(entities))
        return COMPARISON_RESPONSES.get(key)
    
    return None
