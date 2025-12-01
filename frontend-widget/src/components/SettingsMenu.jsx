/**
 * SettingsMenu Component
 * ======================
 * 
 * Three-dot settings menu with options for:
 * - Exact Mode toggle
 * - Groq API toggle
 * - New Chat
 * - Clear Chat
 * - Download Chat (TXT/PDF)
 * - About PDBOT
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 2.4.0
 */

import React, { useState, useRef, useEffect } from 'react';

/**
 * SettingsMenu - Dropdown settings menu
 * 
 * @param {Object} props
 * @param {Function} props.onNewChat - Callback for new chat
 * @param {Function} props.onClearChat - Callback for clear chat
 * @param {Function} props.onDownloadText - Callback for download as text
 * @param {Function} props.onDownloadPDF - Callback for download as PDF
 * @param {boolean} props.exactMode - Current exact mode state
 * @param {Function} props.onExactModeToggle - Callback for exact mode toggle
 * @param {boolean} props.useGroq - Current Groq state
 * @param {Function} props.onGroqToggle - Callback for Groq toggle
 * @param {boolean} props.disabled - Whether menu is disabled
 */
function SettingsMenu({ 
  onNewChat, 
  onClearChat, 
  onDownloadText, 
  onDownloadPDF,
  exactMode = false,
  onExactModeToggle,
  useGroq = false,
  onGroqToggle,
  disabled = false 
}) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);
  
  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  const handleAction = (action) => {
    setIsOpen(false);
    if (action) action();
  };
  
  return (
    <div className="pdbot-settings-menu" ref={menuRef}>
      {/* Menu trigger button */}
      <button
        className={`pdbot-settings-btn ${isOpen ? 'pdbot-active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        aria-label="Settings menu"
        aria-expanded={isOpen}
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <circle cx="12" cy="5" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="19" r="2" />
        </svg>
      </button>
      
      {/* Dropdown menu */}
      {isOpen && (
        <div className="pdbot-settings-dropdown">
          {/* Exact Mode Toggle */}
          <button 
            className={`pdbot-menu-item pdbot-toggle-item ${exactMode ? 'pdbot-active' : ''}`}
            onClick={() => {
              if (onExactModeToggle) onExactModeToggle(!exactMode);
            }}
          >
            <span className="pdbot-menu-icon">{exactMode ? '✅' : '⬜'}</span>
            <span className="pdbot-menu-label">Exact Mode</span>
            <span className="pdbot-toggle-hint">{exactMode ? 'ON' : 'OFF'}</span>
          </button>
          
          {/* Groq API Toggle */}
          <button 
            className={`pdbot-menu-item pdbot-toggle-item ${useGroq ? 'pdbot-active' : ''}`}
            onClick={() => {
              if (onGroqToggle) onGroqToggle(!useGroq);
            }}
          >
            <span className="pdbot-menu-icon">{useGroq ? '✅' : '⬜'}</span>
            <span className="pdbot-menu-label">Use Groq API</span>
            <span className="pdbot-toggle-hint">{useGroq ? 'ON' : 'OFF'}</span>
          </button>
          
          {/* Divider */}
          <div className="pdbot-menu-divider"></div>
          
          {/* New Chat */}
          <button 
            className="pdbot-menu-item"
            onClick={() => handleAction(onNewChat)}
          >
            <span className="pdbot-menu-icon">🔄</span>
            <span className="pdbot-menu-label">New Chat</span>
          </button>
          
          {/* Clear Chat */}
          <button 
            className="pdbot-menu-item"
            onClick={() => handleAction(onClearChat)}
          >
            <span className="pdbot-menu-icon">🗑️</span>
            <span className="pdbot-menu-label">Clear Chat</span>
          </button>
          
          {/* Divider */}
          <div className="pdbot-menu-divider"></div>
          
          {/* Download submenu */}
          <div className="pdbot-menu-group">
            <span className="pdbot-menu-group-label">Download Chat</span>
            <button 
              className="pdbot-menu-item pdbot-menu-sub"
              onClick={() => handleAction(onDownloadText)}
            >
              <span className="pdbot-menu-icon">📄</span>
              <span className="pdbot-menu-label">As Text (.txt)</span>
            </button>
            <button 
              className="pdbot-menu-item pdbot-menu-sub"
              onClick={() => handleAction(onDownloadPDF)}
            >
              <span className="pdbot-menu-icon">📑</span>
              <span className="pdbot-menu-label">As PDF</span>
            </button>
          </div>
          
          {/* Divider */}
          <div className="pdbot-menu-divider"></div>
          
          {/* About */}
          <button 
            className="pdbot-menu-item"
            onClick={() => handleAction(() => {
              alert('PDBOT v2.1.0\n\nPlanning & Development Bot\nMinistry of Planning, Development & Special Initiatives\nGovernment of Pakistan\n\n© 2024');
            })}
          >
            <span className="pdbot-menu-icon">ℹ️</span>
            <span className="pdbot-menu-label">About PDBOT</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default SettingsMenu;
