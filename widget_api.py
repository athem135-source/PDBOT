"""
PDBOT Widget API Server
=======================

A lightweight Flask API that bridges the React widget to the PDBOT RAG pipeline.
This is the primary frontend API (Streamlit is now legacy).

Features:
  - Contextual memory (session-based chat history)
  - RAG-powered responses from Manual for Development Projects 2024
  - Multi-class query classification (off-scope, red-line, abusive detection)
  - Source and passage tracking
  - Feedback collection
  - Admin status endpoint
  - Production WSGI server (waitress)
  - Localtunnel for mobile access

Endpoints:
  POST /chat - Send a query and get a response
  POST /feedback/answer - Submit answer feedback
  POST /feedback/session - Submit session feedback
  POST /memory/clear - Clear session memory
  GET  /health - Health check
  GET  /admin/status - Backend status for admin panel

@author M. Hassan Arif Afridi
@version 2.4.7
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
        
        # Handle guardrail classes (off-scope, red-line, abusive)
        if query_class in ["off_scope", "red_line", "abusive"]:
            guardrail_response = get_guardrail_response(query_class, classification.subcategory or "")
            add_to_session_history(session_id, "user", query)
            add_to_session_history(session_id, "bot", guardrail_response)
            
            return jsonify({
                'answer': guardrail_response,
                'sources': [],
                'passages': [],
                'mode': 'guardrail',
                'classification': query_class
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
        
        # Add bot response to memory
        add_to_session_history(session_id, "bot", final_answer)
        
        print(f"[Widget API] Response generated ({len(final_answer)} chars, mode: {response_mode})")
        
        return jsonify({
            'answer': final_answer,
            'sources': sources,
            'passages': passages,
            'mode': response_mode
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
        'version': '2.3.1',
        'features': ['contextual_memory', 'rag_retrieval', 'feedback_collection', 'admin_panel']
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
        'version': '2.3.1',
        'uptime': datetime.now().isoformat(),
        'memory_mb': round(memory_mb, 2),
        'active_sessions': active_sessions,
        'total_messages_in_memory': total_messages,
        'max_memory_per_session': MAX_MEMORY_MESSAGES,
        'qdrant_status': qdrant_status,
        'ollama_status': ollama_status,
        'qdrant_url': os.getenv("QDRANT_URL", "http://localhost:6338"),
        'debug_mode': app.debug
    })


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
    print("  PDBOT Widget API Server v2.4.0")
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
