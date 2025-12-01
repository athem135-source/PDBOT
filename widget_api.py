"""
PDBOT Widget API Server
=======================

A lightweight Flask API that bridges the React widget to the PDBOT RAG pipeline.
This runs alongside Streamlit to provide REST endpoints for the widget.

Features:
  - Contextual memory (session-based chat history)
  - RAG-powered responses from Manual for Development Projects 2024
  - Source and passage tracking
  - Feedback collection

Endpoints:
  POST /chat - Send a query and get a response
  POST /feedback/answer - Submit answer feedback
  POST /feedback/session - Submit session feedback
  GET  /health - Health check

@author Ministry of Planning, Development & Special Initiatives
@version 2.2.0
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import PDBOT modules
from rag_langchain import search_sentences
from models.local_model import LocalModel

app = Flask(__name__)
CORS(app)  # Enable CORS for widget requests

# Initialize model
model = None

# Session memory store (in-memory, per-session chat history)
# Format: { session_id: [ { "role": "user/bot", "content": "...", "timestamp": "..." }, ... ] }
session_memory: Dict[str, List[Dict]] = {}

# Maximum messages to keep in memory per session
MAX_MEMORY_MESSAGES = 20

def get_model():
    """Lazy load the model"""
    global model
    if model is None:
        model = LocalModel()
    return model

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
            "clear_memory": false  // Optional: clear session memory
        }
    
    Response:
        {
            "answer": "...",
            "sources": [...],
            "passages": [...]
        }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        session_id = data.get('session_id', 'widget-session')
        clear_memory = data.get('clear_memory', False)
        
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
        
        # Combine conversation context with RAG context for better understanding
        full_context = rag_context
        if conversation_context:
            full_context = f"{conversation_context}\n\n---\n\nRelevant information from Manual:\n{rag_context}"
        
        # Generate answer using local model
        llm = get_model()
        answer = llm.generate_response(query, full_context)
        
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
        
        print(f"[Widget API] Response generated ({len(final_answer)} chars)")
        
        return jsonify({
            'answer': final_answer,
            'sources': sources,
            'passages': passages
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
        'version': '2.2.0',
        'features': ['contextual_memory', 'rag_retrieval', 'feedback_collection']
    })


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  PDBOT Widget API Server v2.2.0")
    print("  Government of Pakistan")
    print("="*50)
    print("\n  Starting on http://localhost:5000")
    print("  Endpoints:")
    print("    POST /chat - Chat with PDBOT (with memory)")
    print("    POST /feedback/answer - Answer feedback")
    print("    POST /feedback/session - Session feedback")
    print("    POST /memory/clear - Clear session memory")
    print("    GET  /health - Health check")
    print("\n" + "="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
