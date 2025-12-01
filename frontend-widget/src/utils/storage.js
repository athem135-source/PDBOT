/**
 * Storage Utility Functions for PDBOT Widget
 * ==========================================
 * 
 * Handles localStorage operations for chat history,
 * session management, and widget state persistence.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

// Storage keys
const STORAGE_KEYS = {
  CHAT_HISTORY: 'pdbot_chat_history',
  SESSION_ID: 'pdbot_session_id',
  WIDGET_STATE: 'pdbot_widget_state',
  USER_PREFERENCES: 'pdbot_user_prefs'
};

/**
 * Generate a unique session ID
 * @returns {string} UUID v4
 */
export function generateSessionId() {
  // Use crypto API if available, fallback to manual generation
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  // Fallback UUID generation
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Get or create session ID
 * @returns {string} Session ID
 */
export function getSessionId() {
  let sessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
  
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
  }
  
  return sessionId;
}

/**
 * Create a new session (generates new ID)
 * @returns {string} New session ID
 */
export function createNewSession() {
  const newSessionId = generateSessionId();
  localStorage.setItem(STORAGE_KEYS.SESSION_ID, newSessionId);
  return newSessionId;
}

/**
 * Save chat history to localStorage
 * @param {Array} messages - Array of chat messages
 */
export function saveChatHistory(messages) {
  try {
    const data = {
      messages: messages,
      lastUpdated: new Date().toISOString(),
      sessionId: getSessionId()
    };
    localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(data));
  } catch (error) {
    console.error('[PDBOT Storage] Failed to save chat history:', error);
  }
}

/**
 * Load chat history from localStorage
 * @returns {Array} Array of chat messages
 */
export function loadChatHistory() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
    if (!data) return [];
    
    const parsed = JSON.parse(data);
    
    // Check if session matches
    const currentSession = getSessionId();
    if (parsed.sessionId !== currentSession) {
      // Different session, clear old history
      clearChatHistory();
      return [];
    }
    
    return parsed.messages || [];
  } catch (error) {
    console.error('[PDBOT Storage] Failed to load chat history:', error);
    return [];
  }
}

/**
 * Clear chat history
 */
export function clearChatHistory() {
  try {
    localStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
    console.log('[PDBOT Storage] Chat history cleared');
  } catch (error) {
    console.error('[PDBOT Storage] Failed to clear chat history:', error);
  }
}

/**
 * Save widget state (position, minimized, etc.)
 * @param {Object} state - Widget state object
 */
export function saveWidgetState(state) {
  try {
    localStorage.setItem(STORAGE_KEYS.WIDGET_STATE, JSON.stringify(state));
  } catch (error) {
    console.error('[PDBOT Storage] Failed to save widget state:', error);
  }
}

/**
 * Load widget state
 * @returns {Object} Widget state or defaults
 */
export function loadWidgetState() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.WIDGET_STATE);
    if (!data) {
      return getDefaultWidgetState();
    }
    return { ...getDefaultWidgetState(), ...JSON.parse(data) };
  } catch (error) {
    console.error('[PDBOT Storage] Failed to load widget state:', error);
    return getDefaultWidgetState();
  }
}

/**
 * Get default widget state
 * @returns {Object} Default state
 */
function getDefaultWidgetState() {
  return {
    isOpen: false,
    isMinimized: false,
    position: { x: null, y: null }, // null = default bottom-right
    hasGreeted: false
  };
}

/**
 * Save user preferences
 * @param {Object} prefs - User preferences
 */
export function saveUserPreferences(prefs) {
  try {
    const existing = loadUserPreferences();
    const merged = { ...existing, ...prefs };
    localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(merged));
  } catch (error) {
    console.error('[PDBOT Storage] Failed to save preferences:', error);
  }
}

/**
 * Load user preferences
 * @returns {Object} User preferences
 */
export function loadUserPreferences() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
    return data ? JSON.parse(data) : {};
  } catch (error) {
    console.error('[PDBOT Storage] Failed to load preferences:', error);
    return {};
  }
}

/**
 * Export chat history as text
 * @param {Array} messages - Chat messages
 * @returns {string} Formatted text
 */
export function exportChatAsText(messages) {
  const header = `PDBOT Chat Export
==================
Ministry of Planning, Development & Special Initiatives
Government of Pakistan

Exported: ${new Date().toLocaleString()}
Session ID: ${getSessionId()}

-------------------

`;

  const body = messages.map(msg => {
    const role = msg.role === 'user' ? '👤 You' : '🤖 PDBOT';
    const time = new Date(msg.timestamp).toLocaleTimeString();
    return `[${time}] ${role}:\n${msg.content}\n`;
  }).join('\n---\n\n');

  return header + body;
}

/**
 * Export chat history as PDF-ready HTML
 * @param {Array} messages - Chat messages
 * @returns {string} HTML content
 */
export function exportChatAsHTML(messages) {
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>PDBOT Chat Export</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px;
      background: #fff;
      color: #333;
    }
    .header {
      text-align: center;
      border-bottom: 3px solid #006600;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }
    .header h1 {
      color: #006600;
      margin: 0;
    }
    .header h2 {
      color: #1fa67a;
      font-weight: normal;
      font-size: 1rem;
      margin: 10px 0 0;
    }
    .meta {
      color: #666;
      font-size: 0.9rem;
      margin-top: 15px;
    }
    .message {
      margin: 20px 0;
      padding: 15px;
      border-radius: 8px;
    }
    .message.user {
      background: #e8f5e9;
      border-left: 4px solid #006600;
    }
    .message.bot {
      background: #f5f5f5;
      border-left: 4px solid #1fa67a;
    }
    .message .role {
      font-weight: bold;
      color: #006600;
      margin-bottom: 8px;
    }
    .message .time {
      color: #999;
      font-size: 0.8rem;
      margin-left: 10px;
    }
    .message .content {
      line-height: 1.6;
    }
    .footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #ddd;
      text-align: center;
      color: #666;
      font-size: 0.9rem;
    }
    @media print {
      body { padding: 20px; }
      .message { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🤖 PDBOT Chat Export</h1>
    <h2>Ministry of Planning, Development & Special Initiatives</h2>
    <h2>Government of Pakistan</h2>
    <div class="meta">
      <div>Exported: ${new Date().toLocaleString()}</div>
      <div>Session: ${getSessionId()}</div>
    </div>
  </div>
  
  <div class="messages">
    ${messages.map(msg => `
      <div class="message ${msg.role}">
        <div class="role">
          ${msg.role === 'user' ? '👤 You' : '🤖 PDBOT'}
          <span class="time">${new Date(msg.timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="content">${escapeHtml(msg.content)}</div>
      </div>
    `).join('')}
  </div>
  
  <div class="footer">
    <p>Generated by PDBOT Widget v1.0.0</p>
    <p>© Ministry of Planning, Development & Special Initiatives</p>
  </div>
</body>
</html>`;

  return html;
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML.replace(/\n/g, '<br>');
}

/**
 * Download content as file
 * @param {string} content - File content
 * @param {string} filename - File name
 * @param {string} mimeType - MIME type
 */
export function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default {
  getSessionId,
  createNewSession,
  saveChatHistory,
  loadChatHistory,
  clearChatHistory,
  saveWidgetState,
  loadWidgetState,
  saveUserPreferences,
  loadUserPreferences,
  exportChatAsText,
  exportChatAsHTML,
  downloadFile
};
