/**
 * TypingIndicator Component
 * =========================
 * 
 * Animated "PDBOT is typing..." indicator with bouncing dots.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React from 'react';

/**
 * Typing indicator with animated dots
 * Shows when bot is generating a response
 */
function TypingIndicator() {
  return (
    <div className="pdbot-typing-indicator">
      <div className="pdbot-typing-content">
        <span className="pdbot-typing-avatar">🤖</span>
        <div className="pdbot-typing-bubble">
          <span className="pdbot-typing-text">PDBOT is typing</span>
          <span className="pdbot-typing-dots">
            <span className="pdbot-dot"></span>
            <span className="pdbot-dot"></span>
            <span className="pdbot-dot"></span>
          </span>
        </div>
      </div>
    </div>
  );
}

export default TypingIndicator;
