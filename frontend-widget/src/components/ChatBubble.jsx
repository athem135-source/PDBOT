/**
 * ChatBubble Component
 * ====================
 * 
 * Individual chat message bubble with typewriter effect for bot messages,
 * feedback buttons (like/dislike/regenerate), and styling based on role.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.1.0
 */

import React, { useState, useEffect, useRef } from 'react';
import LikeDislikeButtons from './LikeDislikeButtons.jsx';
import RegenButton from './RegenButton.jsx';
import DetailsModal from './DetailsModal.jsx';

/**
 * ChatBubble - Displays a single chat message
 * 
 * @param {Object} props
 * @param {Object} props.message - Message object { id, role, content, timestamp, passages, sources }
 * @param {boolean} props.isNew - Whether this is a new message (triggers animation)
 * @param {Function} props.onRegenerate - Callback for regenerate button
 * @param {Function} props.onFeedback - Callback for like/dislike feedback
 * @param {boolean} props.showFeedback - Whether to show feedback buttons (bot messages only)
 */
function ChatBubble({ 
  message, 
  isNew = false, 
  onRegenerate, 
  onFeedback,
  showFeedback = true 
}) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [showPassages, setShowPassages] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const contentRef = useRef(null);
  
  const isUser = message.role === 'user';
  const isBot = message.role === 'bot' || message.role === 'assistant';
  
  // Check if message has passages/sources (not for greeting)
  const hasDetails = isBot && (message.passages?.length > 0 || message.sources?.length > 0);
  
  // Typewriter effect for new bot messages
  useEffect(() => {
    if (isBot && isNew && message.content) {
      setIsTyping(true);
      setIsComplete(false);
      setDisplayedText('');
      
      const text = message.content;
      let index = 0;
      
      // Random typing speed between 5-20ms per character
      const getDelay = () => Math.floor(Math.random() * 15) + 5;
      
      const typeChar = () => {
        if (index < text.length) {
          const currentChar = text[index]; // Capture current character
          setDisplayedText(prev => prev + currentChar);
          index++;
          setTimeout(typeChar, getDelay());
        } else {
          setIsTyping(false);
          setIsComplete(true);
        }
      };
      
      // Start typing after a small delay
      const startDelay = setTimeout(typeChar, 100);
      
      return () => clearTimeout(startDelay);
    } else {
      // Not a new message or user message - show full content
      setDisplayedText(message.content || '');
      setIsComplete(true);
    }
  }, [message.content, isNew, isBot]);
  
  // Auto-scroll when typing
  useEffect(() => {
    if (isTyping && contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [displayedText, isTyping]);
  
  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div 
      className={`pdbot-bubble-wrapper ${isUser ? 'pdbot-user' : 'pdbot-bot'} ${isNew ? 'pdbot-new' : ''}`}
      ref={contentRef}
    >
      {/* Avatar for bot messages */}
      {isBot && (
        <div className="pdbot-avatar">🤖</div>
      )}
      
      <div className={`pdbot-bubble ${isUser ? 'pdbot-bubble-user' : 'pdbot-bubble-bot'}`}>
        {/* Message content */}
        <div className="pdbot-bubble-content">
          {displayedText}
          {isTyping && <span className="pdbot-cursor">▊</span>}
        </div>
        
        {/* Timestamp */}
        <div className="pdbot-bubble-time">
          {formatTime(message.timestamp)}
        </div>
        
        {/* Feedback buttons for completed bot messages */}
        {isBot && isComplete && showFeedback && (
          <div className="pdbot-bubble-actions">
            {/* Detail buttons (View Passages / View Sources) */}
            {hasDetails && (
              <div className="pdbot-detail-buttons">
                {message.passages?.length > 0 && (
                  <button 
                    className="pdbot-detail-btn"
                    onClick={() => setShowPassages(true)}
                    title="View supporting passages"
                  >
                    <span className="pdbot-detail-icon">📄</span>
                    <span className="pdbot-detail-label">Passages</span>
                  </button>
                )}
                {message.sources?.length > 0 && (
                  <button 
                    className="pdbot-detail-btn"
                    onClick={() => setShowSources(true)}
                    title="View sources"
                  >
                    <span className="pdbot-detail-icon">📚</span>
                    <span className="pdbot-detail-label">Sources</span>
                  </button>
                )}
              </div>
            )}
            
            <div className="pdbot-feedback-buttons">
              <RegenButton 
                onRegenerate={() => onRegenerate && onRegenerate(message)}
                disabled={isTyping}
              />
              <LikeDislikeButtons
                message={message}
                onFeedback={onFeedback}
                disabled={isTyping}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Avatar placeholder for user messages (to maintain spacing) */}
      {isUser && (
        <div className="pdbot-avatar pdbot-avatar-user">👤</div>
      )}
      
      {/* Passages Modal */}
      <DetailsModal
        isOpen={showPassages}
        onClose={() => setShowPassages(false)}
        title="Supporting Passages"
        type="passages"
        data={message.passages || []}
      />
      
      {/* Sources Modal */}
      <DetailsModal
        isOpen={showSources}
        onClose={() => setShowSources(false)}
        title="Source References"
        type="sources"
        data={message.sources || []}
      />
    </div>
  );
}

export default ChatBubble;
