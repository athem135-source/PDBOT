/**
 * AdminPanel Component
 * ====================
 * 
 * Hidden admin panel accessible via secret code "nufc".
 * Provides backend status, debug info, and settings.
 * 
 * @author M. Hassan Arif Afridi
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function AdminPanel({ isOpen, onClose }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [logoPath, setLogoPath] = useState(localStorage.getItem('pdbot_logo_path') || '');
  const [customApiUrl, setCustomApiUrl] = useState(localStorage.getItem('pdbot_api_url') || API_URL);
  
  // Fetch backend status
  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${customApiUrl}/admin/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err.message);
      setStatus(null);
    }
    setLoading(false);
  };
  
  // Fetch on open
  useEffect(() => {
    if (isOpen) {
      fetchStatus();
    }
  }, [isOpen]);
  
  // Clear all memory
  const handleClearAllMemory = async () => {
    if (!confirm('Clear ALL session memory on server?')) return;
    try {
      const response = await fetch(`${customApiUrl}/admin/clear-all-memory`, {
        method: 'POST'
      });
      const data = await response.json();
      alert(data.message || 'Memory cleared');
      fetchStatus();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };
  
  // Save settings
  const handleSaveSettings = () => {
    localStorage.setItem('pdbot_logo_path', logoPath);
    localStorage.setItem('pdbot_api_url', customApiUrl);
    alert('Settings saved! Reload to apply changes.');
  };
  
  // Clear local storage
  const handleClearLocalStorage = () => {
    if (!confirm('Clear all local chat history and settings?')) return;
    localStorage.removeItem('pdbot_chat_history');
    localStorage.removeItem('pdbot_session_id');
    localStorage.removeItem('pdbot_widget_state');
    alert('Local storage cleared. Reload to apply.');
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="pdbot-admin-overlay" onClick={onClose}>
      <div className="pdbot-admin-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="pdbot-admin-header">
          <h3>🔧 PDBOT Admin Panel</h3>
          <button className="pdbot-admin-close" onClick={onClose}>✕</button>
        </div>
        
        {/* Content */}
        <div className="pdbot-admin-content">
          {/* Backend Status */}
          <div className="pdbot-admin-section">
            <h4>📡 Backend Status</h4>
            {loading && <p className="pdbot-admin-loading">Loading...</p>}
            {error && <p className="pdbot-admin-error">❌ {error}</p>}
            {status && (
              <div className="pdbot-admin-status-grid">
                <div className="pdbot-admin-status-item">
                  <span className="pdbot-admin-label">Version</span>
                  <span className="pdbot-admin-value">{status.version}</span>
                </div>
                <div className="pdbot-admin-status-item">
                  <span className="pdbot-admin-label">Memory Usage</span>
                  <span className="pdbot-admin-value">{status.memory_mb} MB</span>
                </div>
                <div className="pdbot-admin-status-item">
                  <span className="pdbot-admin-label">Active Sessions</span>
                  <span className="pdbot-admin-value">{status.active_sessions}</span>
                </div>
                <div className="pdbot-admin-status-item">
                  <span className="pdbot-admin-label">Messages in Memory</span>
                  <span className="pdbot-admin-value">{status.total_messages_in_memory}</span>
                </div>
                <div className="pdbot-admin-status-item">
                  <span className="pdbot-admin-label">Qdrant</span>
                  <span className={`pdbot-admin-value ${status.qdrant_status === 'connected' ? 'status-ok' : 'status-error'}`}>
                    {status.qdrant_status}
                  </span>
                </div>
                <div className="pdbot-admin-status-item">
                  <span className="pdbot-admin-label">Ollama</span>
                  <span className={`pdbot-admin-value ${status.ollama_status === 'connected' ? 'status-ok' : 'status-error'}`}>
                    {status.ollama_status}
                  </span>
                </div>
              </div>
            )}
            <button className="pdbot-admin-btn" onClick={fetchStatus}>
              🔄 Refresh Status
            </button>
          </div>
          
          {/* Settings */}
          <div className="pdbot-admin-section">
            <h4>⚙️ Settings</h4>
            <div className="pdbot-admin-input-group">
              <label>API URL</label>
              <input 
                type="text"
                value={customApiUrl}
                onChange={e => setCustomApiUrl(e.target.value)}
                placeholder="http://localhost:5000"
              />
            </div>
            <div className="pdbot-admin-input-group">
              <label>Custom Logo Path (URL)</label>
              <input 
                type="text"
                value={logoPath}
                onChange={e => setLogoPath(e.target.value)}
                placeholder="https://example.com/logo.png"
              />
            </div>
            <button className="pdbot-admin-btn pdbot-admin-btn-primary" onClick={handleSaveSettings}>
              💾 Save Settings
            </button>
          </div>
          
          {/* Actions */}
          <div className="pdbot-admin-section">
            <h4>🛠️ Actions</h4>
            <div className="pdbot-admin-actions">
              <button className="pdbot-admin-btn pdbot-admin-btn-warning" onClick={handleClearAllMemory}>
                🗑️ Clear Server Memory
              </button>
              <button className="pdbot-admin-btn pdbot-admin-btn-warning" onClick={handleClearLocalStorage}>
                🧹 Clear Local Storage
              </button>
            </div>
          </div>
          
          {/* Debug Info */}
          <div className="pdbot-admin-section">
            <h4>🐛 Debug Info</h4>
            <div className="pdbot-admin-debug">
              <p><strong>Session ID:</strong> {localStorage.getItem('pdbot_session_id') || 'none'}</p>
              <p><strong>API URL:</strong> {customApiUrl}</p>
              <p><strong>Widget Version:</strong> 2.3.0</p>
              <p><strong>User Agent:</strong> {navigator.userAgent.slice(0, 50)}...</p>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="pdbot-admin-footer">
          <span>PDBOT Admin v2.3.0 | Code: nufc</span>
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;
