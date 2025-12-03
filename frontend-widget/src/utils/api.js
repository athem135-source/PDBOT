/**
 * API Utility Functions for PDBOT Widget
 * ======================================
 * 
 * Handles all communication with the PDBOT backend.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

// API base URL - configurable for different environments
const API_BASE_URL = window.PDBOT_API_URL || 'http://localhost:5000';

/**
 * Send a chat message to the PDBOT backend
 * 
 * @param {string} query - The user's question
 * @param {string} sessionId - Unique session identifier
 * @param {boolean} exactMode - Whether to use exact mode (raw passages)
 * @param {boolean} useGroq - Whether to use Groq API
 * @returns {Promise<Object>} Response containing answer and sources
 */
export async function sendChatMessage(query, sessionId, exactMode = false, useGroq = false) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        session_id: sessionId,
        exact_mode: exactMode,
        use_groq: useGroq
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      answer: data.answer || data.response || 'No response received.',
      sources: data.sources || [],
      passages: data.passages || [],
      suggested_questions: data.suggested_questions || [],  // v2.5.0-patch2: Add suggested questions
      mode: data.mode || 'local',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error('[PDBOT API] Chat error:', error);
    return {
      success: false,
      answer: 'Sorry, I encountered an error connecting to the server. Please try again.',
      sources: [],
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Submit feedback for a specific answer
 * 
 * @param {Object} feedbackData - Feedback details
 * @param {string} feedbackData.messageId - ID of the message
 * @param {string} feedbackData.query - Original question
 * @param {string} feedbackData.answer - Bot's answer
 * @param {string} feedbackData.type - 'like' or 'dislike'
 * @param {string} feedbackData.reason - Reason for dislike (optional)
 * @param {string} feedbackData.sessionId - Session ID
 * @returns {Promise<Object>} Submission result
 */
export async function submitAnswerFeedback(feedbackData) {
  try {
    const response = await fetch(`${API_BASE_URL}/feedback/answer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...feedbackData,
        timestamp: new Date().toISOString(),
        source: 'widget'
      })
    });

    if (!response.ok) {
      // Fallback: save to localStorage if API fails
      saveFeedbackLocally('answer', feedbackData);
      return { success: true, fallback: true };
    }

    return { success: true };
  } catch (error) {
    console.error('[PDBOT API] Feedback error:', error);
    // Fallback: save to localStorage
    saveFeedbackLocally('answer', feedbackData);
    return { success: true, fallback: true };
  }
}

/**
 * Submit session feedback (after clear/new chat)
 * 
 * @param {Object} feedbackData - Session feedback
 * @param {number} feedbackData.rating - 1-3 stars
 * @param {string} feedbackData.username - Optional username
 * @param {string} feedbackData.review - Optional review text
 * @param {string} feedbackData.sessionId - Session ID
 * @returns {Promise<Object>} Submission result
 */
export async function submitSessionFeedback(feedbackData) {
  try {
    const response = await fetch(`${API_BASE_URL}/feedback/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...feedbackData,
        timestamp: new Date().toISOString(),
        source: 'widget'
      })
    });

    if (!response.ok) {
      // Fallback: save to localStorage if API fails
      saveFeedbackLocally('session', feedbackData);
      return { success: true, fallback: true };
    }

    return { success: true };
  } catch (error) {
    console.error('[PDBOT API] Session feedback error:', error);
    // Fallback: save to localStorage
    saveFeedbackLocally('session', feedbackData);
    return { success: true, fallback: true };
  }
}

/**
 * Fallback: Save feedback to localStorage when API is unavailable
 * 
 * @param {string} type - 'answer' or 'session'
 * @param {Object} data - Feedback data
 */
function saveFeedbackLocally(type, data) {
  try {
    const key = `pdbot_feedback_${type}`;
    const existing = JSON.parse(localStorage.getItem(key) || '[]');
    existing.push({
      ...data,
      timestamp: new Date().toISOString(),
      pending: true
    });
    localStorage.setItem(key, JSON.stringify(existing));
    console.log(`[PDBOT] Feedback saved locally (${type})`);
  } catch (error) {
    console.error('[PDBOT] Failed to save feedback locally:', error);
  }
}

/**
 * Clear chat memory on the server
 * Called when starting a new chat session
 * 
 * @param {string} sessionId - Session ID to clear
 * @returns {Promise<Object>} Result
 */
export async function clearChatMemory(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/memory/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId
      })
    });

    if (!response.ok) {
      console.warn('[PDBOT API] Failed to clear memory on server');
      return { success: false };
    }

    return { success: true };
  } catch (error) {
    console.error('[PDBOT API] Clear memory error:', error);
    return { success: false };
  }
}

/**
 * Sync pending local feedback to server
 * Called periodically or when connection is restored
 */
export async function syncPendingFeedback() {
  const types = ['answer', 'session'];
  
  for (const type of types) {
    try {
      const key = `pdbot_feedback_${type}`;
      const pending = JSON.parse(localStorage.getItem(key) || '[]');
      
      if (pending.length === 0) continue;
      
      const synced = [];
      for (const item of pending) {
        try {
          const endpoint = type === 'answer' ? '/feedback/answer' : '/feedback/session';
          const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...item, synced: true })
          });
          
          if (response.ok) {
            synced.push(item);
          }
        } catch (e) {
          // Keep in pending
        }
      }
      
      // Remove synced items
      const remaining = pending.filter(item => !synced.includes(item));
      localStorage.setItem(key, JSON.stringify(remaining));
      
      if (synced.length > 0) {
        console.log(`[PDBOT] Synced ${synced.length} ${type} feedback items`);
      }
    } catch (error) {
      console.error(`[PDBOT] Sync error for ${type}:`, error);
    }
  }
}

export default {
  sendChatMessage,
  submitAnswerFeedback,
  submitSessionFeedback,
  clearChatMemory,
  syncPendingFeedback
};
