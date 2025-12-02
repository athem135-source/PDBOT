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
    # Common symptoms
    r"\b(?:headache|fever|cough|cold|pain|sick|disease|illness)\b",
    r"\b(?:nausea|vomiting|diarrhea|constipation|fatigue)\b",
    r"\b(?:infection|inflammation|swelling|bleeding)\b",
    r"\b(?:allergy|allergic|rash|itching|itch)\b",
    
    # Medications
    r"\b(?:medicine|drug|tablet|pill|prescription|dose|dosage)\b",
    r"\b(?:antibiotic|painkiller|aspirin|paracetamol|ibuprofen)\b",
    r"\b(?:injection|vaccine|vaccination|immunization)\b",
    
    # Medical professionals/places
    r"\b(?:doctor|physician|surgeon|nurse|specialist)\b",
    r"\b(?:hospital|clinic|pharmacy|dispensary|emergency\s*room)\b",
    
    # Medical conditions/procedures
    r"\b(?:symptom|diagnosis|cure|remedy|treatment|therapy)\b",
    r"\b(?:surgery|operation|transplant|biopsy)\b",
    r"\b(?:cancer|diabetes|hypertension|heart\s*disease)\b",
    r"\b(?:pregnancy|pregnant|abortion|miscarriage)\b",
    r"\b(?:mental\s*health|depression|anxiety|stress)\b.*(?:treatment|help|advice)",
    r"\b(?:std|sti|hiv|aids)\b.*(?:treatment|test|symptom)",
    
    # Body parts in medical context
    r"\b(?:stomach|liver|kidney|lung|heart)\b.*\b(?:problem|pain|issue|disease)\b",
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

# Sexual/inappropriate content patterns
OFFSCOPE_SEXUAL = [
    r"\b(?:sex|sexy|sexual|sexually)\b",
    r"\b(?:have\s+sex|having\s+sex)\b",
    r"\b(?:talk\s+sexy|talk\s+dirty|dirty\s+talk)\b",
    r"\b(?:sexbot|sex\s*bot|porn|pornography|nude|naked)\b",
    r"\b(?:hot\s+girl|hot\s+guy|hookup|hook\s*up|one\s+night\s+stand)\b",
    r"\b(?:flirt|flirting|seduction|seduce)\b",
    r"\b(?:kiss|kissing|make\s+out|making\s+out)\b.*\b(?:you|me|with)\b",
    r"\b(?:dirty\s+stuff|naughty|intimate)\b.*\b(?:talk|tell|say)\b",
    r"\b(?:erotic|sensual|foreplay)\b",
    r"\b(?:dating|date\s+me|go\s+out\s+with\s+me)\b",
    r"\b(?:be\s+my\s+(?:boyfriend|girlfriend|lover))\b",
    r"\b(?:become\s+my\s+(?:boyfriend|girlfriend|lover))\b",
    r"\b(?:love\s+me|marry\s+me|i\s+love\s+you)\b",
    r"\b(?:you'?re?\s+(?:hot|cute|beautiful|handsome|attractive))\b",
    r"\b(?:send\s+(?:nudes|pics|photos))\b",
    # Additional explicit terms
    r"\b(?:cum|cumming|orgasm|masturbat|horny|aroused)\b",
    r"\b(?:boobs?|tits?|ass|penis|vagina|dick|cock)\b",
    r"\b(?:strip|stripper|prostitut|escort|hooker)\b",
    r"\b(?:xxx|adult\s*content|nsfw|18\+)\b",
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

# Abusive language patterns - English (comprehensive)
ABUSIVE_HARD = [
    # F-word variants
    r"\b(?:fuck|fucking|fucked|fucker|fck|f\*ck|f\*\*k|fuk|fuq|phuck|fack|fuk|effing)\b",
    r"\b(?:motherfucker|mf|mofo|m\*therf\*cker|motherfucking|muthafucka)\b",
    r"\b(?:wtf|stfu|gtfo|lmfao|ffs|af)\b",
    r"\b(?:fuckoff|fuck\s*off|fuckface|fuckhead|fuckwit|fuckboy|fuckgirl)\b",
    r"\b(?:clusterfuck|mindfuck|brainfuck|skullfuck)\b",
    
    # S-word variants
    r"\b(?:shit|shitty|shitting|bullshit|bs|sh\*t|sht|shite|shitstorm)\b",
    r"\b(?:shithead|shitface|shithole|shitstain|shitbag|dipshit|horseshit)\b",
    r"\b(?:apeshit|batshit|chickenshit|dogshit|ratshit)\b",
    
    # A-word variants
    r"\b(?:asshole|a\*\*hole|arsehole|ass|arse|a\*\*|azz)\b",
    r"\b(?:dumbass|dumb\s*ass|jackass|jack\s*ass|smartass|fatass|lardass)\b",
    r"\b(?:asshat|asswipe|assclown|assmunch|assface|asskisser)\b",
    r"\b(?:badass|kickass|hardass)\b.*\b(?:insult|you|bot)\b",
    
    # B-word variants
    r"\b(?:bastard|bast\*rd|b\*stard|bastad)\b",
    r"\b(?:bitch|b\*tch|btch|biatch|biotch|beeyotch|biznatch)\b",
    r"\b(?:bitchy|bitchass|sonofabitch|son\s*of\s*a\s*bitch)\b",
    r"\b(?:bellend|bollocks|bollock|bugger|buggered|bloody\s*hell)\b",
    
    # C-word variants
    r"\b(?:cunt|c\*nt|c\*\*t|twat|tw\*t|cnt)\b",
    r"\b(?:cunty|cuntface|thundercunt|douchecunt)\b",
    r"\b(?:crap|crappy|craptastic|crapton)\b",
    r"\b(?:coward|chickenshit)\b.*\b(?:you|bot)\b",
    
    # D-word variants
    r"\b(?:damn|dammit|goddamn|god\s*damn|damnit|dangit)\b",
    r"\b(?:dick|d\*ck|dck|cock|c\*ck|dik|dikk)\b",
    r"\b(?:dickhead|dickwad|dickface|dickless|dickweed|dickbag)\b",
    r"\b(?:douche|douchebag|douchenozzle|douchcanoe)\b",
    r"\b(?:dildo|dong|schlong|wiener|wanker|wank)\b",
    
    # Intelligence insults (when directed)
    r"\b(?:idiot|moron|retard|dumbass|dumb\s*ass)\b.*\b(?:you|bot|system)\b",
    r"\b(?:imbecile|cretin|nitwit|dimwit|halfwit|twit)\b.*\b(?:you|bot|system)\b",
    r"\b(?:simpleton|dunce|doofus|dolt|numbskull|bonehead)\b.*\b(?:you|bot)\b",
    r"\b(?:airhead|blockhead|knucklehead|pinhead|meathead)\b.*\b(?:you|bot)\b",
    r"\b(?:birdbrain|peabrain|scatterbrain|lamebrain)\b.*\b(?:you|bot)\b",
    
    # Prostitution/sex worker slurs
    r"\b(?:whore|wh\*re|slut|sl\*t|skank|hoe|ho|hoebag)\b",
    r"\b(?:hooker|prostitute|escort|callgirl|streetwalker)\b",
    r"\b(?:slutty|whorish|skanky|trampy|sleazy)\b",
    r"\b(?:pimp|gigolo|jezebel|harlot|trollop|strumpet)\b",
    
    # Racial slurs - comprehensive
    r"\b(?:nigger|n\*gger|n\*\*\*er|nigga|n\*gga|nigg3r|n1gger|n1gga)\b",
    r"\b(?:negro|negroid|darkie|darky|coon|jigaboo|sambo)\b",
    r"\b(?:spook|jungle\s*bunny|porch\s*monkey|tar\s*baby)\b",
    r"\b(?:chink|ch\*nk|chinky|ching\s*chong|gook|g\*\*k|slant|slanteye)\b",
    r"\b(?:jap|nip|zipperhead|dink|slope|yellowskin)\b",
    r"\b(?:spic|sp\*c|wetback|beaner|border\s*bunny|taco\s*bender)\b",
    r"\b(?:greaser|greaseball|dago|wop|guido|guinea|ginzo)\b",
    r"\b(?:kike|k\*ke|hymie|heeb|yid|sheeny)\b",
    r"\b(?:paki|p\*ki|currymuncher|dothead|camel\s*jockey)\b(?!\s*stan)",
    r"\b(?:towelhead|raghead|sand\s*n\*gger|hajji|haji|durka)\b",
    r"\b(?:cracker|honky|honkey|redneck|hillbilly|white\s*trash)\b",
    r"\b(?:polack|kraut|jerry|fritz|hun|limey|frog|froggy)\b",
    r"\b(?:mick|paddy|bog\s*trotter|fenian)\b",
    r"\b(?:abo|boong|coon|gin)\b",  # Australian slurs
    r"\b(?:redskin|injun|squaw|prairie\s*n\*gger)\b",
    
    # Homophobic slurs
    r"\b(?:faggot|fag|f\*g|f\*ggot|faggy|fagging|fgt)\b",
    r"\b(?:homo|h\*mo|queer|queero|queen)\b(?:.*insult|.*offensive|\b)",
    r"\b(?:dyke|d\*ke|lesbo|lezzie|lezzy|lez|carpet\s*muncher)\b",
    r"\b(?:tranny|shemale|she-male|heshe|he-she|ladyboy)\b",
    r"\b(?:fairy|pansy|poof|poofter|pooftah|nancy\s*boy)\b",
    r"\b(?:sissy|sissified|limp\s*wrist|light\s*in\s*loafers)\b",
    r"\b(?:butt\s*pirate|pillow\s*biter|fudge\s*packer|turd\s*burglar)\b",
    r"\b(?:cock\s*sucker|cocksucker|c\*cksucker|knob\s*jockey)\b",
    r"\b(?:sodomite|sodomizer|bugger|bummer)\b",
    
    # Disability slurs
    r"\b(?:retard|r\*tard|retarded|tard|ritard|re-re)\b",
    r"\b(?:spaz|spazz|spastic|spazzy|spasticated)\b",
    r"\b(?:cripple|crip|gimp|gimpy|lame|lamer)\b",
    r"\b(?:psycho|psychotic|lunatic|nutjob|nutcase|mental)\b.*\b(?:you|bot)\b",
    r"\b(?:schizo|autist|autistic)\b.*\b(?:insult|you|idiot)\b",
    r"\b(?:mong|mongoloid|window\s*licker|drooler)\b",
    r"\b(?:vegetable|braindead|brain\s*dead)\b.*\b(?:you|bot)\b",
    
    # Religious slurs
    r"\b(?:kaffir|kafir|infidel)\b(?:.*insult|.*offensive)",
    r"\b(?:christ\s*killer|heathen|heretic)\b.*\b(?:insult|you)\b",
    r"\b(?:bible\s*basher|bible\s*thumper|god\s*botherer)\b",
    r"\b(?:islamophobe|antisemite|jew\s*hater)\b",
    
    # Death/violence wishes
    r"\b(?:kill\s*yourself|kys|die|go\s*die|neck\s*yourself)\b",
    r"\b(?:hope\s*you\s*die|wish\s*you\s*were\s*dead|drop\s*dead)\b",
    r"\b(?:kill\s*you|murder\s*you|end\s*you|destroy\s*you)\b",
    r"\b(?:hang\s*yourself|shoot\s*yourself|slit\s*your\s*wrists)\b",
    r"\b(?:get\s*cancer|hope\s*you\s*get\s*cancer|cancer\s*patient)\b.*\b(?:insult)\b",
    r"\b(?:rot\s*in\s*hell|burn\s*in\s*hell|go\s*to\s*hell)\b",
    
    # Body shaming
    r"\b(?:fatass|fatty|fatso|lardass|tubby|porky|piggy|whale)\b",
    r"\b(?:anorexic|bulimic|skeleton|stick\s*figure)\b.*\b(?:insult|you)\b",
    r"\b(?:ugly|fugly|hideous|grotesque|disgusting)\b.*\b(?:you|bot|face)\b",
    
    # Misc vulgar
    r"\b(?:piss|pissed|pissing|pisser|pisshead|pissant)\b",
    r"\b(?:turd|turds|turdface|turdball|dingleberry)\b",
    r"\b(?:fart|farting|fartface|farthead|queef)\b.*\b(?:insult|you)\b",
    r"\b(?:skidmark|crusty|scum|scumbag|scumball|lowlife)\b",
    r"\b(?:trash|garbage|filth|vermin|parasite|leech)\b.*\b(?:you|bot|human)\b",
    r"\b(?:loser|failure|waste\s*of\s*space|worthless|pathetic)\b.*\b(?:you|bot)\b",
]

# Urdu/Hindi abuse patterns (romanized) - comprehensive list
ABUSIVE_URDU = [
    # Mother-related slurs (most offensive)
    r"\b(?:bhenchod|benchod|bc|b\.c\.|bhen\s*chod|bhenchot|bhnchod)\b",
    r"\b(?:madarchod|motherchod|mc|m\.c\.|madar\s*chod|mamachod|maderchod)\b",
    r"\b(?:teri\s*(?:maa|maaki?|maki?|ammi?|amma?|ma|maan))\b",
    r"\b(?:maa\s*ki\s*(?:chut|chu+t|ch\*t|phudi|p\*\*di|aankh))\b",
    r"\b(?:maaki\s*(?:chut|chu+t|ch\*t|phudi|kirkiri))\b",
    r"\b(?:teri.*(?:chut|phudi|gand|gaand))\b",
    r"\b(?:ma\s*chod|maa\s*chod|maachod|maa\s*ki)\b",
    r"\b(?:amma\s*ki|ammi\s*ki|mummy\s*ki)\b.*\b(?:chut|gand)\b",
    
    # Sister-related slurs
    r"\b(?:behan\s*chod|behen\s*chod|bahen\s*chod)\b",
    r"\b(?:teri\s*(?:behan|behen|bhen|bahen))\b",
    r"\b(?:behen\s*ki|behan\s*ki|bhen\s*ki)\b.*\b(?:chut|gand)\b",
    
    # Female genitalia slurs
    r"\b(?:chutiya|chootiya|chutia|chu+tiya|ch\*tiya|chutiye|chutiyon)\b",
    r"\b(?:chut|chu+t|ch\*t|phudi|phu+di|p\*\*di|choot)\b",
    r"\b(?:bhosdi|bhosdike|bhosad|bhosdiwale?|bhosadpappu)\b",
    r"\b(?:bhosdika|bhosdiki|bhosadchod)\b",
    r"\b(?:phuddu|phuddi|fuddu|fuddi|fudi|fudu)\b",
    
    # Male genitalia slurs  
    r"\b(?:lund|lauda|laude|l\*nd|l\*uda|lora|loray|lawda|lawde)\b",
    r"\b(?:lund\s*fakir|lauda\s*lassan|lund\s*ka\s*baal)\b",
    r"\b(?:tatte|tatti|tattay|andey|anda|golay)\b",
    r"\b(?:nunnu|nunu|lulla|luli|susu)\b",
    
    # Buttocks/anal slurs
    r"\b(?:gaandu|gandu|gand|g\*nd|g\*ndu|gaand|gaaand)\b",
    r"\b(?:gand\s*mara|gand\s*marao|gand\s*phad|gand\s*tod)\b",
    r"\b(?:gand\s*me\s*danda|gand\s*me\s*ungli)\b",
    r"\b(?:chootad|chootar|chutar)\b",
    
    # Prostitution/sexual slurs
    r"\b(?:randi|randwa|rundi|randi\s*ka|randiyaan|randibaaz)\b",
    r"\b(?:randi\s*ki\s*aulad|randi\s*ka\s*bacha)\b",
    r"\b(?:chodu|chodna|chod|choday|chodoo|chodampatti)\b",
    r"\b(?:dalla|dallay|dalal|dallah|dalali)\b",
    r"\b(?:bharwa|bharway|bharwi|bharwa|bharwapan)\b",
    r"\b(?:gashti|gashtiyan|pataka|patakha)\b",
    r"\b(?:raand|raandi|tawaif|kothewali|kothebaaz)\b",
    r"\b(?:call\s*girl|escort)\b.*\b(?:urdu|hindi|desi)\b",
    
    # Illegitimacy slurs
    r"\b(?:harami|haramzada|haramzadi|haraam\s*zada|haraami)\b",
    r"\b(?:haram\s*ka|haramkhor|haraamkhor)\b",
    r"\b(?:najaiz|najaayaz|najayaz\s*aulad)\b",
    r"\b(?:kanjar|kanjarkhana|kanjari|kanjaron)\b",
    r"\b(?:haram\s*ki\s*aulad|harami\s*bacha)\b",
    
    # Animal insults
    r"\b(?:kutiya|kutti|kutta|kutay|kuttay|kuttey|kuttia)\b",
    r"\b(?:kutte\s*ki\s*aulad|kutte\s*ka\s*bacha)\b",
    r"\b(?:suar|soor|suwar|suor|suar\s*ki\s*aulad)\b",
    r"\b(?:gadha|gadhe|gadhi|gadhay|ullu|ullu\s*ka\s*patha)\b",
    r"\b(?:bandar|bandri|bander|langoor|langur)\b",
    r"\b(?:gidhar|geedhar|lomri|lomdi|nevla)\b",
    r"\b(?:saanp|saamp|keeda|keera|makhi|makkhi)\b",
    r"\b(?:bakra|bakri|bakray|bhed|bhedia)\b",
    r"\b(?:chuha|chooha|chuhe|billu|billi|kauwa)\b",
    r"\b(?:khota|khotay|khotey|kachhua|kabutar)\b",
    
    # General Urdu insults
    r"\b(?:sala|saala|saali|sali|s\*la|saaley|saalo)\b",
    r"\b(?:kamina|kameena|kameeni|kaminay|kameeno)\b",
    r"\b(?:badtameez|be\s*ghairat|be-ghairat|beghairat)\b",
    r"\b(?:zaleel|zalil|ghatiya|wahiyat|ganda|gandi)\b",
    r"\b(?:bakwas|bakwaas|bakwass|fazool|faltu|faaltu)\b",
    r"\b(?:tatti|potty|gobar|goo|ghuu|jhant)\b",
    r"\b(?:jhant\s*ke\s*baal|jhant\s*ka|jhaant)\b",
    r"\b(?:bewakoof|beywaqoof|bevkoof|bevakoof)\b",
    r"\b(?:pagal|paagal|pagla|pagli|paglay)\b",
    r"\b(?:nalayak|nikamma|nikammi|nikamme|nalaik)\b",
    r"\b(?:chakka|chakkay|chakke|meetha|namard)\b",
    r"\b(?:hijra|hijray|hijron|khusra|khusray|khassi)\b",
    r"\b(?:lanati|lanaat|lanat|laanti|laanat)\b",
    r"\b(?:manhoos|manhos|badnaseeb|kambakht)\b",
    r"\b(?:shaitan|shaitaan|iblees|bhoot|jinn)\b",
    r"\b(?:murdaar|murdar|najis|paleed|napak)\b",
    r"\b(?:ghatiya|neech|kamzarf|razeel|razil)\b",
    r"\b(?:makkar|makkaar|daghabaaz|dhokhebaaz|farebi)\b",
    r"\b(?:chor|chori|daku|dakait|badmaash|badmash)\b",
    r"\b(?:lutera|lootera|lootere|haraami)\b",
    r"\b(?:gandagi|gandgi|kachra|kachre|kooda)\b",
    r"\b(?:surti|sutli|tharki|hawasi|haiwaan)\b",
    
    # Punjabi/regional abuse
    r"\b(?:pencho|paincho|panchod|painchod|penchod)\b",
    r"\b(?:bhund|phund|bund|bnd|phundd)\b",
    r"\b(?:chod|chodan|choddi|choddiyan)\b",
    r"\b(?:phuddoo|phuddee|fuddoo|phuddian)\b",
    r"\b(?:khotay|khotey|khota|khoti|khotian)\b",
    r"\b(?:vaddi|vaddiyan|vadda|vadday|wadday)\b.*\b(?:gand|lun)\b",
    r"\b(?:tharkee|tharak|tharkan|tharki)\b",
    r"\b(?:haram\s*da|harami\s*da|kanjra)\b",
    
    # Common misspellings/variants
    r"\b(?:teri\s*bhn|teri\s*behen|behan\s*chod|bhnchod)\b",
    r"\b(?:ma\s*ka\s*bhosda|maa\s*ka\s*bhosda|maa\s*ka\s*bhos)\b",
    r"\b(?:bnd\s*mara|bnd\s*maray|bnd\s*mein)\b",
    r"\b(?:lode|lodey|laudey|lawday|lundey)\b",
    r"\b(?:tatto|tatta|tattey|tatton)\b",
    r"\b(?:mundi|loda\s*le|le\s*mera)\b",
    r"\b(?:choos|choosna|choos\s*le|choos\s*mera)\b",
    r"\b(?:mut|moot|mutra|peshaab)\b.*\b(?:pi|pee|pila)\b",
    
    # Internet/SMS slang Urdu
    r"\b(?:mc|bc|bkl|bhkl|bsdwl|bsdk|bsdka)\b",
    r"\b(?:tmkc|tmkb|teri\s*mkc|teri\s*mkb)\b",
    r"\b(?:gf|lf|tf|chd|chod)\b.*\b(?:tu|teri)\b",
    
    # Pashto abuse
    r"\b(?:kos|khaza|khar|ghul|ghal)\b",
    r"\b(?:peghla|peghlay|spin|tor)\b.*\b(?:insult|gali)\b",
    
    # Sindhi abuse
    r"\b(?:bhadwa|bhadwi|bhadwe|randwa)\b",
    r"\b(?:kanjar|kanjri|bhang|bhangi)\b",
    
    # Kashmiri abuse
    r"\b(?:haakh|haekh|yakh|yakhe)\b.*\b(?:insult|gali)\b",
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
        self.offscope_sexual_re = [re.compile(p, re.IGNORECASE) for p in OFFSCOPE_SEXUAL]
        
        self.redline_bribery_re = [re.compile(p, re.IGNORECASE) for p in REDLINE_BRIBERY]
        self.redline_corruption_re = [re.compile(p, re.IGNORECASE) for p in REDLINE_CORRUPTION]
        self.redline_misuse_re = [re.compile(p, re.IGNORECASE) for p in REDLINE_MISUSE]
        
        self.abusive_hard_re = [re.compile(p, re.IGNORECASE) for p in ABUSIVE_HARD]
        self.abusive_urdu_re = [re.compile(p, re.IGNORECASE) for p in ABUSIVE_URDU]
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
        
        # Urdu/Hindi abuse - highest priority
        if self._match_any(q, self.abusive_urdu_re):
            return ClassificationResult(
                query_class=QueryClass.ABUSIVE.value,
                subcategory="urdu_abuse",
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
        
        # Sexual/inappropriate content - highest confidence block
        if self._match_any(q, self.offscope_sexual_re):
            return ClassificationResult(
                query_class=QueryClass.OFF_SCOPE.value,
                subcategory="inappropriate",
                confidence=0.95,
                should_use_rag=False,
                response_template="offscope_inappropriate"
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
