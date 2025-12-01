/**
 * ChatWidget Component
 * ====================
 * 
 * Main chat widget component - floating, draggable, minimizable.
 * Contains all chat logic and renders child components.
 * 
 * Features:
 * - Admin mode (type "nufc" to access)
 * - Session memory management
 * - Logo customization
 * 
 * @author M. Hassan Arif Afridi
 * @version 2.3.0
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

// Components
import ChatBubble from './ChatBubble.jsx';
import TypingIndicator from './TypingIndicator.jsx';
import SuggestedQuestions from './SuggestedQuestions.jsx';
import SettingsMenu from './SettingsMenu.jsx';
import FeedbackModal from './FeedbackModal.jsx';
import AdminPanel from './AdminPanel.jsx';

// Utilities
import { sendChatMessage, clearChatMemory } from '../utils/api.js';
import { 
  getSessionId, 
  createNewSession,
  saveChatHistory, 
  loadChatHistory, 
  clearChatHistory,
  saveWidgetState,
  loadWidgetState,
  exportChatAsText,
  exportChatAsHTML,
  downloadFile
} from '../utils/storage.js';
import { generateMessageId } from '../utils/feedback.js';

// Greeting message
const GREETING_MESSAGE = "Assalam-o-Alaikum! I am PDBOT, your planning & development assistant. How can I help you today?";

// Admin code
const ADMIN_CODE = "nufc";

// Logo URL - Pakistan coat of arms
const DEFAULT_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Coat_of_arms_of_Pakistan.svg/800px-Coat_of_arms_of_Pakistan.svg.png";

/**
 * ChatWidget - Main floating chat widget
 */
function ChatWidget() {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasGreeted, setHasGreeted] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [newMessageId, setNewMessageId] = useState(null);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [adminCodeBuffer, setAdminCodeBuffer] = useState('');
  
  // Dragging state
  const [position, setPosition] = useState({ x: null, y: null });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  
  // Logo
  const customLogo = localStorage.getItem('pdbot_logo_path');
  const logoUrl = customLogo || DEFAULT_LOGO;
  
  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const widgetRef = useRef(null);
  const sessionId = useRef(getSessionId());
  
  // Load saved state on mount
  useEffect(() => {
    const savedState = loadWidgetState();
    setIsOpen(savedState.isOpen);
    setHasGreeted(savedState.hasGreeted);
    if (savedState.position.x !== null) {
      setPosition(savedState.position);
    }
    
    // Load chat history
    const history = loadChatHistory();
    if (history.length > 0) {
      setMessages(history);
      setHasGreeted(true);
    }
  }, []);
  
  // Save state changes
  useEffect(() => {
    saveWidgetState({ isOpen, isMinimized, position, hasGreeted });
  }, [isOpen, isMinimized, position, hasGreeted]);
  
  // Save messages to storage
  useEffect(() => {
    if (messages.length > 0) {
      saveChatHistory(messages);
    }
  }, [messages]);
  
  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);
  
  // Focus input when widget opens
  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, isMinimized]);
  
  // Admin code detection via keyboard
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      
      // Only track letters
      if (e.key.length === 1 && e.key.match(/[a-z]/i)) {
        const newBuffer = (adminCodeBuffer + e.key.toLowerCase()).slice(-4);
        setAdminCodeBuffer(newBuffer);
        
        if (newBuffer === ADMIN_CODE) {
          setShowAdminPanel(true);
          setAdminCodeBuffer('');
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, adminCodeBuffer]);
  
  // Show greeting when widget first opens
  useEffect(() => {
    if (isOpen && !hasGreeted && messages.length === 0) {
      const greetingMsg = {
        id: generateMessageId(),
        role: 'bot',
        content: GREETING_MESSAGE,
        timestamp: new Date().toISOString()
      };
      setMessages([greetingMsg]);
      setNewMessageId(greetingMsg.id);
      setHasGreeted(true);
    }
  }, [isOpen, hasGreeted, messages.length]);
  
  // Handle opening/closing
  const toggleOpen = () => {
    if (isMinimized) {
      setIsMinimized(false);
    } else {
      setIsOpen(!isOpen);
    }
  };
  
  // Handle minimize
  const handleMinimize = () => {
    setIsMinimized(true);
  };
  
  // Handle close
  const handleClose = () => {
    setIsOpen(false);
    setIsMinimized(false);
  };
  
  // Handle send message
  const handleSend = async () => {
    const query = inputValue.trim();
    if (!query || isLoading) return;
    
    // Add user message
    const userMsg = {
      id: generateMessageId(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);
    
    try {
      // Send to API
      const response = await sendChatMessage(query, sessionId.current);
      
      // Add bot response
      const botMsg = {
        id: generateMessageId(),
        role: 'bot',
        content: response.answer,
        query: query, // Store original query for regenerate
        sources: response.sources || [],
        passages: response.passages || [],
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, botMsg]);
      setNewMessageId(botMsg.id);
    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      const errorMsg = {
        id: generateMessageId(),
        role: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMsg]);
      setNewMessageId(errorMsg.id);
    }
    
    setIsLoading(false);
  };
  
  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  // Handle suggested question click
  const handleSuggestedClick = (question) => {
    setInputValue(question);
    setTimeout(() => handleSend(), 100);
  };
  
  // Handle regenerate
  const handleRegenerate = async (message) => {
    if (!message.query || isLoading) return;
    
    setIsLoading(true);
    
    try {
      const response = await sendChatMessage(message.query, sessionId.current);
      
      // Replace the message with new response
      const newBotMsg = {
        id: generateMessageId(),
        role: 'bot',
        content: response.answer,
        query: message.query,
        sources: response.sources,
        timestamp: new Date().toISOString(),
        regenerated: true
      };
      
      setMessages(prev => {
        const index = prev.findIndex(m => m.id === message.id);
        if (index !== -1) {
          const updated = [...prev];
          updated[index] = newBotMsg;
          return updated;
        }
        return [...prev, newBotMsg];
      });
      setNewMessageId(newBotMsg.id);
    } catch (error) {
      console.error('Regenerate error:', error);
    }
    
    setIsLoading(false);
  };
  
  // Handle feedback
  const handleFeedback = (type, message, reason) => {
    console.log(`Feedback: ${type} for message ${message.id}`, reason);
  };
  
  // Handle new chat
  const handleNewChat = () => {
    if (messages.length > 1) { // More than just greeting
      setShowFeedbackModal(true);
    } else {
      performNewChat();
    }
  };
  
  // Actually perform new chat after feedback
  const performNewChat = async () => {
    try {
      // Clear server-side memory for this session
      await clearChatMemory(sessionId.current);
    } catch (err) {
      console.warn('Failed to clear server memory:', err);
    }
    
    // Create new session
    sessionId.current = createNewSession();
    
    // Clear all local state
    setMessages([]);
    setHasGreeted(false);
    setInputValue('');
    
    // Clear localStorage completely
    clearChatHistory();
    localStorage.removeItem('pdbot_chat_history');
    localStorage.removeItem('pdbot_widget_state');
    
    // Re-trigger greeting after a short delay
    setTimeout(() => {
      const greetingMsg = {
        id: generateMessageId(),
        role: 'bot',
        content: GREETING_MESSAGE,
        timestamp: new Date().toISOString()
      };
      setMessages([greetingMsg]);
      setNewMessageId(greetingMsg.id);
      setHasGreeted(true);
    }, 100);
  };
  
  // Handle clear chat
  const handleClearChat = () => {
    if (messages.length > 1) {
      setShowFeedbackModal(true);
    } else {
      performNewChat();
    }
  };
  
  // Handle feedback modal close
  const handleFeedbackSubmit = () => {
    performNewChat();
  };
  
  // Handle download as text
  const handleDownloadText = () => {
    const text = exportChatAsText(messages);
    const filename = `pdbot_chat_${new Date().toISOString().split('T')[0]}.txt`;
    downloadFile(text, filename, 'text/plain');
  };
  
  // Handle download as PDF (HTML that can be printed/saved as PDF)
  const handleDownloadPDF = () => {
    const html = exportChatAsHTML(messages);
    const filename = `pdbot_chat_${new Date().toISOString().split('T')[0]}.html`;
    downloadFile(html, filename, 'text/html');
    
    // Also open in new tab for easy PDF printing
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };
  
  // Dragging handlers
  const handleDragStart = (e) => {
    // Don't start drag if clicking on buttons or menu
    if (e.target.closest('button') || e.target.closest('.pdbot-settings-menu')) {
      return;
    }
    
    e.preventDefault();
    setIsDragging(true);
    const rect = widgetRef.current.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };
  
  const handleDragMove = useCallback((e) => {
    if (isDragging) {
      const x = e.clientX - dragOffset.x;
      const y = e.clientY - dragOffset.y;
      
      // Keep within viewport
      const maxX = window.innerWidth - 380;
      const maxY = window.innerHeight - 600;
      
      setPosition({
        x: Math.max(0, Math.min(x, maxX)),
        y: Math.max(0, Math.min(y, maxY))
      });
    }
  }, [isDragging, dragOffset]);
  
  const handleDragEnd = () => {
    setIsDragging(false);
  };
  
  // Add/remove drag listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleDragMove);
      document.addEventListener('mouseup', handleDragEnd);
      return () => {
        document.removeEventListener('mousemove', handleDragMove);
        document.removeEventListener('mouseup', handleDragEnd);
      };
    }
  }, [isDragging, handleDragMove]);
  
  // Calculate widget style
  const widgetStyle = {
    ...(position.x !== null && position.y !== null ? {
      right: 'auto',
      bottom: 'auto',
      left: `${position.x}px`,
      top: `${position.y}px`
    } : {})
  };
  
  return (
    <>
      {/* Floating toggle button (when closed) */}
      {!isOpen && (
        <button 
          className="pdbot-toggle-btn"
          onClick={toggleOpen}
          aria-label="Open PDBOT chat"
        >
          <span className="pdbot-toggle-icon">💬</span>
          <span className="pdbot-toggle-label">Chat with PDBOT</span>
        </button>
      )}
      
      {/* Chat widget */}
      {isOpen && (
        <div 
          ref={widgetRef}
          className={`pdbot-widget ${isMinimized ? 'pdbot-minimized' : ''} ${isDragging ? 'pdbot-dragging' : ''}`}
          style={widgetStyle}
        >
          {/* Header */}
          <div 
            className="pdbot-header"
            onMouseDown={handleDragStart}
          >
            <div className="pdbot-header-info">
              <img 
                src={logoUrl} 
                alt="Pakistan Emblem" 
                className="pdbot-header-logo"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
              <div className="pdbot-header-text">
                <span className="pdbot-title">PDBOT</span>
                <span className="pdbot-subtitle">Planning & Development Assistant</span>
              </div>
            </div>
            
            <div className="pdbot-header-actions">
              <SettingsMenu
                onNewChat={handleNewChat}
                onClearChat={handleClearChat}
                onDownloadText={handleDownloadText}
                onDownloadPDF={handleDownloadPDF}
              />
              <button 
                className="pdbot-minimize-btn"
                onClick={handleMinimize}
                aria-label="Minimize"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M19 13H5v-2h14v2z"/>
                </svg>
              </button>
              <button 
                className="pdbot-close-btn"
                onClick={handleClose}
                aria-label="Close"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </button>
            </div>
          </div>
          
          {/* Body (hidden when minimized) */}
          {!isMinimized && (
            <>
              {/* Messages area */}
              <div className="pdbot-messages">
                {/* Suggested questions (show at start) */}
                {messages.length <= 1 && !isLoading && (
                  <SuggestedQuestions
                    onSelect={handleSuggestedClick}
                    disabled={isLoading}
                  />
                )}
                
                {/* Message bubbles */}
                {messages.map((msg) => (
                  <ChatBubble
                    key={msg.id}
                    message={msg}
                    isNew={msg.id === newMessageId}
                    onRegenerate={handleRegenerate}
                    onFeedback={handleFeedback}
                    showFeedback={msg.role === 'bot' && msg.id !== messages[0]?.id}
                  />
                ))}
                
                {/* Typing indicator */}
                {isLoading && <TypingIndicator />}
                
                {/* Scroll anchor */}
                <div ref={messagesEndRef} />
              </div>
              
              {/* Input area */}
              <div className="pdbot-input-area">
                <textarea
                  ref={inputRef}
                  className="pdbot-input"
                  placeholder="Type your question..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                  rows={1}
                />
                <button
                  className="pdbot-send-btn"
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isLoading}
                  aria-label="Send message"
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                  </svg>
                </button>
              </div>
              
              {/* Accuracy Warning */}
              <div className="pdbot-accuracy-warning">
                <span className="pdbot-warning-icon">⚠️</span>
                <span className="pdbot-warning-text">
                  Responses are AI-generated from the Manual for Development Projects 2024. 
                  Always verify important information with official sources.
                </span>
              </div>
              
              {/* Footer */}
              <div className="pdbot-footer">
                <span className="pdbot-footer-text">
                  Ministry of Planning, Development & Special Initiatives
                </span>
              </div>
            </>
          )}
          
          {/* Minimized state */}
          {isMinimized && (
            <div className="pdbot-minimized-content" onClick={toggleOpen}>
              <span className="pdbot-minimized-text">Click to expand</span>
            </div>
          )}
        </div>
      )}
      
      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => {
          setShowFeedbackModal(false);
          performNewChat();  // Always clear chat when modal closes
        }}
        onSubmit={handleFeedbackSubmit}
        messageCount={messages.length}
      />
      
      {/* Admin Panel (accessible via "nufc" code) */}
      <AdminPanel
        isOpen={showAdminPanel}
        onClose={() => setShowAdminPanel(false)}
      />
    </>
  );
}

export default ChatWidget;
