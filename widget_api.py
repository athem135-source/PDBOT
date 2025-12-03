"""
PDBOT Widget API Server v2.5.0
==============================

A lightweight Flask API that bridges the React widget to the PDBOT RAG pipeline.
This is the primary frontend API (Streamlit is now legacy).

Features:
  - Contextual memory (session-based chat history)
  - RAG-powered responses from Manual for Development Projects 2024
  - Multi-class query classification (greeting, ambiguous, off-scope, red-line, abusive)
  - Suggested follow-up questions (ChatGPT-style)
  - Clarification prompts for vague queries
  - Source and passage tracking
  - Feedback collection
  - Admin status endpoint
  - Statistics dashboard endpoint
  - Production WSGI server (waitress)
  - Localtunnel for mobile access

Endpoints:
  POST /chat - Send a query and get a response
  POST /feedback/answer - Submit answer feedback
  POST /feedback/session - Submit session feedback
  POST /memory/clear - Clear session memory
  GET  /health - Health check
  GET  /admin/status - Backend status for admin panel
  GET  /admin/statistics - Detailed usage statistics

@author M. Hassan Arif Afridi
@version 2.5.0
"""

import os
import sys
import json
import socket
from datetime import datetime
from typing import Dict, List
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import PDBOT modules
from rag_langchain import search_sentences
from models.local_model import LocalModel
from utils.text_utils import find_exact_locations

# Import classifier and templates for off-scope/red-line detection
from core.multi_classifier import MultiClassifier
from core.templates import get_guardrail_response

# Groq API support (optional)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("[Widget API] Groq not installed - Groq mode disabled")

# PDF path for exact mode
PDF_PATH = os.path.join(os.path.dirname(__file__), 'data', 'uploads', 'Manual-for-Development-Project-2024.pdf')
RAW_PAGES_CACHE = None

def load_pdf_pages():
    """Load PDF pages for exact mode search."""
    global RAW_PAGES_CACHE
    if RAW_PAGES_CACHE is not None:
        return RAW_PAGES_CACHE
    
    pages = []
    try:
        import fitz  # PyMuPDF
        if os.path.exists(PDF_PATH):
            doc = fitz.open(PDF_PATH)
            for i in range(len(doc)):
                pages.append(doc.load_page(i).get_text("text") or "")
            doc.close()
            print(f"[Widget API] Loaded {len(pages)} PDF pages for exact mode")
    except Exception as e:
        print(f"[Widget API] Could not load PDF: {e}")
    
    RAW_PAGES_CACHE = pages
    return pages

app = Flask(__name__)
CORS(app)  # Enable CORS for widget requests

# Serve mobile page at root for Cloudflare tunnel
@app.route('/')
def serve_mobile():
    """Serve mobile-friendly chat page"""
    try:
        with open('mobile.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({"error": "Mobile page not found", "status": "ok", "api": "/chat"}), 200

# Initialize model and classifier
model = None
groq_client = None
classifier = None

# Session memory store (in-memory, per-session chat history)
# Format: { session_id: [ { "role": "user/bot", "content": "...", "timestamp": "..." }, ... ] }
session_memory: Dict[str, List[Dict]] = {}

# Maximum messages to keep in memory per session
MAX_MEMORY_MESSAGES = 20

def get_classifier():
    """Lazy load the classifier"""
    global classifier
    if classifier is None:
        classifier = MultiClassifier()
    return classifier

def get_model():
    """Lazy load the model"""
    global model
    if model is None:
        model = LocalModel()
    return model

def get_groq_client():
    """Lazy load Groq client"""
    global groq_client
    if groq_client is None and GROQ_AVAILABLE:
        api_key = os.environ.get('GROQ_API_KEY')
        if api_key:
            groq_client = Groq(api_key=api_key)
        else:
            print("[Widget API] Warning: GROQ_API_KEY not set")
    return groq_client

def generate_groq_response(query: str, context: str) -> str:
    """Generate response using Groq API"""
    client = get_groq_client()
    if not client:
        return "⚠️ Groq API not available. Please set GROQ_API_KEY environment variable."
    
    try:
        system_prompt = """You are PDBOT, an AI assistant for Pakistan's Planning & Development Division.
Answer questions based ONLY on the provided context from the Manual for Development Projects 2024.
Be concise, accurate, and cite page numbers when possible.
If the context doesn't contain the answer, say so clearly."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Groq API] Error: {e}")
        return f"⚠️ Groq API error: {str(e)}"

def get_session_history(session_id: str) -> List[Dict]:
    """Get chat history for a session"""
    if session_id not in session_memory:
        session_memory[session_id] = []
    return session_memory[session_id]

def add_to_session_history(session_id: str, role: str, content: str):
    """Add a message to session history"""
    history = get_session_history(session_id)
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # Keep only last N messages to prevent memory overflow
    if len(history) > MAX_MEMORY_MESSAGES:
        session_memory[session_id] = history[-MAX_MEMORY_MESSAGES:]

def build_context_with_memory(session_id: str, current_query: str) -> str:
    """Build context string including recent chat history for contextual understanding"""
    history = get_session_history(session_id)
    
    if not history:
        return ""
    
    # Get last 3 exchanges (6 messages) for context
    recent = history[-6:]
    
    context_parts = []
    for msg in recent:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        context_parts.append(f"{role_label}: {msg['content'][:200]}")
    
    return "Previous conversation:\n" + "\n".join(context_parts)

def clear_session_memory(session_id: str):
    """Clear memory for a session"""
    if session_id in session_memory:
        del session_memory[session_id]


# =====================================================
# SUGGESTED FOLLOW-UP QUESTIONS (ChatGPT-style)
# =====================================================

# v2.5.0-patch1: Comprehensive topic-based question suggestions
FOLLOW_UP_QUESTIONS = {
    "greeting": [
        "What is PC-I?",
        "What are the DDWP approval limits?",
        "How does project approval work?",
        "What is ECNEC?",
    ],
    "ambiguous": [
        "What is the purpose of PC-I?",
        "What is the approval hierarchy for projects?",
        "What are the different project phases?",
        "How is project cost estimated?",
    ],
    # PC-I related
    "pc-i": [
        "What are the components of PC-I?",
        "How to prepare a PC-I document?",
        "What is the approval process for PC-I?",
        "What attachments are required for PC-I?",
        "What is the difference between PC-I and PC-II?",
    ],
    # PC-II related  
    "pc-ii": [
        "When is PC-II required?",
        "What is the purpose of feasibility studies in PC-II?",
        "What cost limits apply to PC-II?",
        "How to submit PC-II for approval?",
    ],
    # PC-III related
    "pc-iii": [
        "What is PC-III used for?",
        "How often should PC-III be submitted?",
        "What information is included in PC-III?",
        "Who reviews PC-III reports?",
    ],
    # PC-IV related
    "pc-iv": [
        "What is PC-IV?",
        "When is PC-IV prepared?",
        "What is project completion report?",
        "What metrics are in PC-IV?",
    ],
    # PC-V related
    "pc-v": [
        "What is PC-V evaluation?",
        "When is PC-V conducted?",
        "What is post-completion evaluation?",
        "How is project impact measured?",
    ],
    # Approval bodies
    "ddwp": [
        "What is the DDWP approval limit?",
        "Who chairs the DDWP meeting?",
        "What projects go to DDWP?",
        "How is DDWP different from CDWP?",
    ],
    "cdwp": [
        "What is the CDWP approval threshold?",
        "Who are the members of CDWP?",
        "What projects require CDWP approval?",
        "How to submit projects to CDWP?",
    ],
    "ecnec": [
        "What is the ECNEC approval limit?",
        "Who chairs ECNEC meetings?",
        "What projects go to ECNEC?",
        "What is the ECNEC approval process?",
    ],
    # Numeric/financial queries
    "numeric_query": [
        "What are the threshold limits for CDWP?",
        "What is the ECNEC approval limit?",
        "What is the maximum DDWP approval limit?",
        "How is project cost calculated?",
    ],
    # Definition queries
    "definition_query": [
        "What are the types of PC proformas?",
        "What is the difference between PC-I and PC-II?",
        "What is PSDP?",
        "How is a project defined in the Manual?",
    ],
    # Comparison queries
    "comparison_query": [
        "What is the difference between DDWP and CDWP?",
        "How does PC-I differ from PC-II?",
        "What is the difference between federal and provincial projects?",
        "How is ADP different from PSDP?",
    ],
    # Procedure queries
    "procedure_query": [
        "What are the stages of project approval?",
        "What documents are required for PC-I?",
        "How does project revision work?",
        "What is the project cycle?",
    ],
    # Compliance queries
    "compliance_query": [
        "What are the audit requirements?",
        "How is project transparency ensured?",
        "What records must be maintained?",
        "What are the PC-I format requirements?",
    ],
    # Monitoring queries
    "monitoring_evaluation": [
        "What are the project monitoring KPIs?",
        "How is project progress tracked?",
        "What is the role of M&E Division?",
        "How often are projects reviewed?",
    ],
    # Budget/PSDP
    "budget": [
        "What is PSDP?",
        "How are funds allocated to projects?",
        "What is the budget release process?",
        "How is project cost overrun handled?",
    ],
    # General
    "general": [
        "What is the role of Planning Commission?",
        "What is PSDP?",
        "How are federal projects approved?",
        "What is project monitoring?",
        "What is the project approval hierarchy?",
    ],
}


def get_suggested_questions(query_class: str, query: str = "") -> List[str]:
    """
    Generate suggested follow-up questions based on query type.
    
    Args:
        query_class: Classification result
        query: Original query for context
        
    Returns:
        List of 3 suggested questions
    """
    import random
    
    # Check if query mentions specific topics
    q_lower = query.lower()
    pool = []
    
    # v2.5.0-patch1: Better topic detection
    if "pc-i" in q_lower or "pc1" in q_lower or "pc 1" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("pc-i", [])
    elif "pc-ii" in q_lower or "pc2" in q_lower or "pc 2" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("pc-ii", [])
    elif "pc-iii" in q_lower or "pc3" in q_lower or "pc 3" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("pc-iii", [])
    elif "pc-iv" in q_lower or "pc4" in q_lower or "pc 4" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("pc-iv", [])
    elif "pc-v" in q_lower or "pc5" in q_lower or "pc 5" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("pc-v", [])
    elif "ddwp" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("ddwp", [])
    elif "cdwp" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("cdwp", [])
    elif "ecnec" in q_lower or "nec" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("ecnec", [])
    elif "psdp" in q_lower or "budget" in q_lower or "fund" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("budget", [])
    elif "monitor" in q_lower or "evaluation" in q_lower or "m&e" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("monitoring_evaluation", [])
    elif "differ" in q_lower or "compare" in q_lower or "vs" in q_lower:
        pool = FOLLOW_UP_QUESTIONS.get("comparison_query", [])
    elif query_class in FOLLOW_UP_QUESTIONS:
        pool = FOLLOW_UP_QUESTIONS[query_class]
    else:
        pool = FOLLOW_UP_QUESTIONS.get("general", [])
    
    # Add some variety by mixing with general questions
    general = FOLLOW_UP_QUESTIONS.get("general", [])
    combined = list(set(pool + general))
    
    # Return 3 random questions, avoiding the current query
    suggestions = [q for q in combined if q.lower() not in query.lower()]
    random.shuffle(suggestions)
    return suggestions[:3]


def generate_contextual_followups(query: str, answer: str, query_class: str) -> List[str]:
    """
    Generate contextual follow-up questions based on the answer.
    
    Args:
        query: Original user query
        answer: Bot's response
        query_class: Classification result
        
    Returns:
        List of 3 contextual follow-up questions
    """
    followups = []
    q_lower = query.lower()
    a_lower = answer.lower()
    
    # v2.5.0-patch1: Enhanced contextual suggestions
    # PC proformas
    if "pc-i" in a_lower and "pc-i" not in q_lower:
        followups.append("What are the mandatory sections of PC-I?")
    if "pc-ii" in a_lower and "pc-ii" not in q_lower:
        followups.append("When is PC-II required?")
    if "pc-iii" in a_lower and "pc-iii" not in q_lower:
        followups.append("What is PC-III used for?")
    if "pc-iv" in a_lower and "pc-iv" not in q_lower:
        followups.append("What is the purpose of PC-IV?")
    if "pc-v" in a_lower and "pc-v" not in q_lower:
        followups.append("When is PC-V evaluation conducted?")
    
    # Approval bodies
    if "ddwp" in a_lower and "ddwp" not in q_lower:
        followups.append("What is the DDWP approval threshold?")
    if "cdwp" in a_lower and "cdwp" not in q_lower:
        followups.append("What projects go to CDWP?")
    if "ecnec" in a_lower and "ecnec" not in q_lower:
        followups.append("What is the ECNEC approval limit?")
    
    # Financial/process topics
    if ("approval" in a_lower or "approved" in a_lower) and "approval" not in q_lower:
        followups.append("What is the project approval hierarchy?")
    if ("cost" in a_lower or "budget" in a_lower) and "cost" not in q_lower:
        followups.append("How is project cost estimated?")
    if "monitoring" in a_lower and "monitoring" not in q_lower:
        followups.append("What are the project monitoring KPIs?")
    if "psdp" in a_lower and "psdp" not in q_lower:
        followups.append("How are PSDP funds allocated?")
    if "revision" in a_lower and "revision" not in q_lower:
        followups.append("What is the project revision process?")
    
    # For comparison queries, suggest related comparisons
    if query_class == "comparison_query":
        if "ddwp" in q_lower or "cdwp" in q_lower:
            followups.append("What is the difference between CDWP and ECNEC?")
        if "pc-i" in q_lower or "pc-ii" in q_lower:
            followups.append("What are the different PC proformas?")
    
    # Fill remaining slots with topic-based suggestions
    if len(followups) < 3:
        additional = get_suggested_questions(query_class, query)
        for q in additional:
            if q not in followups:
                followups.append(q)
            if len(followups) >= 3:
                break
    
    return followups[:3]


# v2.5.0-patch1: Long answer handling
MAX_ANSWER_WORDS = 250  # If answer exceeds this, suggest manual reference

def handle_long_answer(answer: str, sources: List[Dict], query: str) -> str:
    """
    Check if answer is too long and add page reference suggestion.
    
    Args:
        answer: The generated answer
        sources: List of source dictionaries with page info
        query: Original user query
        
    Returns:
        Modified answer with page reference if too long
    """
    word_count = len(answer.split())
    
    if word_count > MAX_ANSWER_WORDS:
        # Get unique page numbers from sources
        pages = list(set(str(s.get('page', '?')) for s in sources if s.get('page')))
        pages_str = ", ".join(sorted(pages)) if pages else "the relevant sections"
        
        # Add a note about detailed information
        truncation_note = f"\n\n📖 **Note:** This is a summary. For detailed information, please refer to **pages {pages_str}** in the Manual for Development Projects 2024."
        answer += truncation_note
    
    return answer


@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat requests from the widget with contextual memory.
    
    Request:
        {
            "query": "What is PC-I?",
            "session_id": "uuid",
            "clear_memory": false,  // Optional: clear session memory
            "exact_mode": false,    // Optional: return raw passages
            "use_groq": false       // Optional: use Groq API
        }
    
    Response:
        {
            "answer": "...",
            "sources": [...],
            "passages": [...],
            "mode": "local|exact|groq"
        }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        session_id = data.get('session_id', 'widget-session')
        clear_memory = data.get('clear_memory', False)
        exact_mode = data.get('exact_mode', False)
        use_groq = data.get('use_groq', False)
        
        # Handle memory clear request
        if clear_memory:
            clear_session_memory(session_id)
            return jsonify({
                'answer': 'Chat memory cleared.',
                'sources': [],
                'passages': []
            })
        
        if not query:
            return jsonify({
                'answer': 'Please enter a question.',
                'sources': [],
                'passages': []
            }), 400
        
        print(f"[Widget API] Query: {query[:50]}... (Session: {session_id[:8]}...)")
        
        # =====================================================
        # STEP 1: CLASSIFY QUERY (before RAG)
        # =====================================================
        query_classifier = get_classifier()
        classification = query_classifier.classify(query)
        query_class = classification.query_class
        
        print(f"[Widget API] Classification: {query_class}/{classification.subcategory}")
        
        # Handle guardrail classes (greeting, ambiguous, off-scope, red-line, abusive)
        if query_class in ["greeting", "ambiguous", "off_scope", "red_line", "abusive"]:
            guardrail_response = get_guardrail_response(query_class, classification.subcategory or "", query)
            add_to_session_history(session_id, "user", query)
            add_to_session_history(session_id, "bot", guardrail_response)
            
            return jsonify({
                'answer': guardrail_response,
                'sources': [],
                'passages': [],
                'mode': 'guardrail',
                'classification': query_class,
                'suggested_questions': get_suggested_questions(query_class) if query_class in ["greeting", "ambiguous"] else []
            })
        
        # Get conversation context from memory
        conversation_context = build_context_with_memory(session_id, query)
        
        # Add user message to memory
        add_to_session_history(session_id, "user", query)
        
        # Get RAG results
        rag_results = search_sentences(query, top_k=3)
        
        if not rag_results:
            no_result_answer = "I couldn't find relevant information in the manual for your question. Please try rephrasing or ask about Planning & Development topics."
            add_to_session_history(session_id, "bot", no_result_answer)
            return jsonify({
                'answer': no_result_answer,
                'sources': [],
                'passages': []
            })
        
        # Build context from RAG results
        context_parts = []
        sources = []
        passages = []  # Store full passage details
        for i, result in enumerate(rag_results[:3]):
            text = result.get('text', result.get('content', ''))
            page = result.get('page', result.get('metadata', {}).get('page', 'N/A'))
            score = result.get('score', result.get('relevance', 0))
            source = f"Manual for Development Projects 2024, p.{page}"
            
            context_parts.append(f"[{i+1}] {text}")
            sources.append({
                'title': 'Manual for Development Projects 2024',
                'page': page,
                'relevance': round(score * 100) if score else 0
            })
            passages.append({
                'text': text,
                'page': page,
                'relevance': round(score * 100) if score else 0
            })
        
        rag_context = "\n\n".join(context_parts)
        
        # EXACT MODE: Find exact locations like Streamlit version
        if exact_mode:
            pdf_pages = load_pdf_pages()
            exact_locations = find_exact_locations(query, pdf_pages, max_results=5)
            
            if exact_locations:
                exact_answer = "✅ **Answer:**\n\n"
                for loc in exact_locations[:3]:
                    page = loc.get('page', '?')
                    para = loc.get('paragraph', '?')
                    line = loc.get('line', '?')
                    sentence = loc.get('sentence', '')
                    exact_answer += f"**Pg {page}, Para {para}, Line {line}:** \"{sentence}\"\n\n"
                
                exact_answer += "📘 **Source:**\n"
                for loc in exact_locations[:3]:
                    exact_answer += f"Page {loc.get('page', '?')} – Paragraph {loc.get('paragraph', '?')} – Line {loc.get('line', '?')}\n"
                
                exact_sources = [{
                    'title': 'Manual for Development Projects 2024',
                    'page': loc.get('page', '?'),
                    'paragraph': loc.get('paragraph', '?'),
                    'line': loc.get('line', '?')
                } for loc in exact_locations[:3]]
                
                exact_passages = [{
                    'text': loc.get('sentence', ''),
                    'page': loc.get('page', '?'),
                    'paragraph': loc.get('paragraph', '?'),
                    'line': loc.get('line', '?')
                } for loc in exact_locations[:3]]
            else:
                exact_answer = "📖 **No exact match found. Here are related passages:**\n\n"
                for i, p in enumerate(passages, 1):
                    exact_answer += f"**[{i}] Page {p['page']}** (Relevance: {p['relevance']}%)\n"
                    exact_answer += f"{p['text']}\n\n"
                exact_sources = sources
                exact_passages = passages
            
            add_to_session_history(session_id, "bot", exact_answer)
            print(f"[Widget API] Exact Mode response")
            
            return jsonify({
                'answer': exact_answer,
                'sources': exact_sources,
                'passages': exact_passages,
                'mode': 'exact'
            })
        
        # Combine conversation context with RAG context for better understanding
        full_context = rag_context
        if conversation_context:
            full_context = f"{conversation_context}\n\n---\n\nRelevant information from Manual:\n{rag_context}"
        
        # GROQ MODE: Use Groq API for responses
        if use_groq:
            answer = generate_groq_response(query, full_context)
            response_mode = 'groq'
        else:
            # Generate answer using local model
            # Use higher max_new_tokens to avoid truncation
            llm = get_model()
            answer = llm.generate_response(query, full_context, max_new_tokens=200)
            response_mode = 'local'
        
        # Clean up answer
        if answer:
            answer = answer.strip()
            # Remove any prefix like "Answer:" if present
            for prefix in ["Answer:", "✅ Answer:", "Response:"]:
                if answer.startswith(prefix):
                    answer = answer[len(prefix):].strip()
        
        final_answer = answer or "I couldn't generate a response. Please try again."
        
        # v2.5.0-patch1: Handle long answers by adding page reference
        final_answer = handle_long_answer(final_answer, sources, query)
        
        # Add bot response to memory
        add_to_session_history(session_id, "bot", final_answer)
        
        # Generate contextual follow-up questions
        suggested_questions = generate_contextual_followups(query, final_answer, query_class)
        
        print(f"[Widget API] Response generated ({len(final_answer)} chars, mode: {response_mode})")
        
        return jsonify({
            'answer': final_answer,
            'sources': sources,
            'passages': passages,
            'mode': response_mode,
            'suggested_questions': suggested_questions
        })
        
    except Exception as e:
        print(f"[Widget API] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'answer': f'Sorry, an error occurred: {str(e)}',
            'sources': [],
            'passages': []
        }), 500


@app.route('/feedback/answer', methods=['POST'])
def answer_feedback():
    """
    Save feedback for a specific answer.
    
    Request:
        {
            "messageId": "...",
            "query": "...",
            "answer": "...",
            "type": "like" | "dislike",
            "reasonId": "...",
            "sessionId": "...",
            "timestamp": "..."
        }
    """
    try:
        data = request.get_json()
        
        # Create feedback directory if needed
        feedback_dir = os.path.join(os.path.dirname(__file__), 'feedback', 'widget_answers')
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Save feedback
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"answer_{timestamp}_{data.get('type', 'unknown')}.json"
        filepath = os.path.join(feedback_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[Widget API] Answer feedback saved: {filename}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"[Widget API] Feedback error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/feedback/session', methods=['POST'])
def session_feedback():
    """
    Save session feedback (rating, review).
    
    Request:
        {
            "rating": 1-3,
            "username": "...",
            "review": "...",
            "sessionId": "...",
            "timestamp": "..."
        }
    """
    try:
        data = request.get_json()
        rating = data.get('rating', 0)
        
        # Create feedback directory based on rating
        feedback_dir = os.path.join(os.path.dirname(__file__), 'feedback', f'{rating}_star')
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Save feedback
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        username = data.get('username', 'Widget_User').replace(' ', '_')[:20]
        filename = f"{timestamp}_{username}.json"
        filepath = os.path.join(feedback_dir, filename)
        
        # Also save as txt for compatibility with existing feedback
        txt_content = f"""Session Feedback (Widget)
========================
Rating: {rating} star(s)
Username: {data.get('username', 'Anonymous')}
Review: {data.get('review', 'No review')}
Messages: {data.get('messageCount', 0)}
Session ID: {data.get('sessionId', 'unknown')}
Timestamp: {data.get('timestamp', timestamp)}
"""
        
        txt_filepath = filepath.replace('.json', '.txt')
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[Widget API] Session feedback saved: {filename}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"[Widget API] Session feedback error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/memory/clear', methods=['POST'])
def clear_memory():
    """
    Clear chat memory for a session.
    
    Request:
        {
            "session_id": "uuid"
        }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'widget-session')
        clear_session_memory(session_id)
        print(f"[Widget API] Memory cleared for session: {session_id[:8]}...")
        return jsonify({'success': True, 'message': 'Chat memory cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'PDBOT Widget API',
        'version': '2.5.0',
        'features': ['contextual_memory', 'rag_retrieval', 'feedback_collection', 'admin_panel', 'suggested_questions', 'greeting_detection']
    })


@app.route('/admin/status', methods=['GET'])
def admin_status():
    """
    Admin endpoint - returns detailed backend status.
    Only accessible with admin code verification on frontend.
    """
    try:
        # Get memory usage
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
    except:
        memory_mb = 0
    
    # Count active sessions
    active_sessions = len(session_memory)
    total_messages = sum(len(msgs) for msgs in session_memory.values())
    
    # Check Qdrant status
    qdrant_status = "unknown"
    try:
        from qdrant_client import QdrantClient
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6338")
        client = QdrantClient(url=qdrant_url, timeout=2)
        collections = client.get_collections()
        qdrant_status = "connected"
    except Exception as e:
        qdrant_status = f"error: {str(e)[:50]}"
    
    # Check Ollama status
    ollama_status = "unknown"
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            ollama_status = "connected"
        else:
            ollama_status = "error"
    except:
        ollama_status = "not running"
    
    return jsonify({
        'status': 'ok',
        'version': '2.5.0',
        'uptime': datetime.now().isoformat(),
        'memory_mb': round(memory_mb, 2),
        'active_sessions': active_sessions,
        'total_messages_in_memory': total_messages,
        'max_memory_per_session': MAX_MEMORY_MESSAGES,
        'qdrant_status': qdrant_status,
        'ollama_status': ollama_status,
        'qdrant_url': os.getenv("QDRANT_URL", "http://localhost:6338"),
        'debug_mode': app.debug,
        'model_loaded': model is not None,
        'embedding_ready': True
    })


@app.route('/admin/statistics', methods=['GET'])
def admin_statistics():
    """
    Admin endpoint - returns comprehensive usage statistics.
    For dashboard monitoring.
    """
    try:
        import psutil
        import glob
        
        # System stats
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        # Session stats
        active_sessions = len(session_memory)
        total_messages = sum(len(msgs) for msgs in session_memory.values())
        
        # Per-session breakdown
        session_details = []
        for sid, msgs in session_memory.items():
            session_details.append({
                'session_id': sid[:12] + '...',
                'message_count': len(msgs),
                'last_activity': msgs[-1].get('timestamp', 'N/A') if msgs else 'N/A'
            })
        
        # Feedback stats (count files in feedback folders)
        feedback_dir = os.path.join(os.path.dirname(__file__), 'feedback')
        feedback_stats = {}
        for star in ['1_star', '2_star', '3_star', '4_star', '5_star']:
            star_dir = os.path.join(feedback_dir, star)
            if os.path.exists(star_dir):
                feedback_stats[star] = len(os.listdir(star_dir))
            else:
                feedback_stats[star] = 0
        
        # Log stats
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        log_count = len(glob.glob(os.path.join(log_dir, '*.log'))) if os.path.exists(log_dir) else 0
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'version': '2.5.0',
                'memory_mb': round(memory_mb, 2),
                'cpu_percent': round(cpu_percent, 2),
                'pid': os.getpid()
            },
            'sessions': {
                'active_count': active_sessions,
                'total_messages': total_messages,
                'max_per_session': MAX_MEMORY_MESSAGES,
                'details': session_details[:10]  # Top 10 sessions
            },
            'feedback': feedback_stats,
            'logs': {
                'log_files': log_count
            },
            'services': {
                'model_loaded': model is not None,
                'classifier_loaded': classifier is not None,
                'groq_available': GROQ_AVAILABLE
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/clear-all-memory', methods=['POST'])
def admin_clear_all_memory():
    """Admin endpoint to clear all session memory"""
    try:
        count = len(session_memory)
        session_memory.clear()
        return jsonify({
            'success': True,
            'message': f'Cleared {count} sessions from memory'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def get_local_ip():
    """Get the local IP address for network access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5000
    
    print("\n" + "="*60)
    print("  PDBOT Widget API Server v2.5.0")
    print("  Developed by M. Hassan Arif Afridi")
    print("="*60)
    print(f"\n  🌐 Local:   http://localhost:{port}")
    print(f"  📱 Network: http://{local_ip}:{port}")
    
    # Try localtunnel for external access (open source, free)
    use_tunnel = os.environ.get('USE_TUNNEL', '').lower() == 'true'
    if use_tunnel:
        import subprocess
        import threading
        def start_tunnel():
            try:
                # Use localtunnel (npm install -g localtunnel)
                process = subprocess.Popen(
                    ['lt', '--port', str(port), '--subdomain', 'pdbot-giki'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                for line in process.stdout:
                    if 'your url is:' in line.lower() or 'https://' in line:
                        print(f"\n  🌍 PUBLIC URL (for phone/external access):")
                        print(f"     {line.strip()}")
                        print("\n  ⚠️  Share this URL to access from any network!")
                        break
            except Exception as e:
                print(f"\n  ⚠️  localtunnel not available: {e}")
                print("     Install with: npm install -g localtunnel")
        
        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()
    else:
        print(f"\n  To access from phone (same network): http://{local_ip}:{port}")
        print("  For external access, set USE_TUNNEL=true (requires: npm install -g localtunnel)")
    
    print("\n  Endpoints:")
    print("    POST /chat           - Chat with PDBOT (with memory)")
    print("    POST /feedback/*     - Feedback endpoints")
    print("    POST /memory/clear   - Clear session memory")
    print("    GET  /health         - Health check")
    print("    GET  /admin/status   - Backend status (admin)")
    print("\n" + "="*60)
    
    # Check if waitress is available for production server
    try:
        from waitress import serve
        print("\n  ✅ Using Waitress (production WSGI server)")
        print("="*60 + "\n")
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        print("\n  ⚠️  Waitress not installed. Using Flask dev server.")
        print("     Install with: pip install waitress")
        print("="*60 + "\n")
        app.run(host='0.0.0.0', port=port, debug=False)
