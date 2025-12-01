/**
 * DetailsModal Component
 * ======================
 * 
 * Reusable modal for displaying passages and sources.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React from 'react';

/**
 * DetailsModal - Shows passages or sources in a closeable modal
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Callback when modal closes
 * @param {string} props.title - Modal title
 * @param {string} props.type - 'passages' or 'sources'
 * @param {Array} props.data - Array of passages or sources
 */
function DetailsModal({ isOpen, onClose, title, type, data = [] }) {
  if (!isOpen) return null;
  
  return (
    <div className="pdbot-details-overlay" onClick={onClose}>
      <div 
        className="pdbot-details-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="pdbot-details-header">
          <h3 className="pdbot-details-title">
            <span className="pdbot-details-icon">
              {type === 'passages' ? '📄' : '📚'}
            </span>
            {title}
          </h3>
          <button 
            className="pdbot-details-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        
        {/* Body */}
        <div className="pdbot-details-body">
          {data.length === 0 ? (
            <p className="pdbot-details-empty">No data available</p>
          ) : (
            <ul className="pdbot-details-list">
              {data.map((item, index) => (
                <li key={index} className="pdbot-details-item">
                  {type === 'passages' ? (
                    <>
                      <div className="pdbot-passage-header">
                        <span className="pdbot-passage-num">Passage {index + 1}</span>
                        <span className="pdbot-passage-meta">
                          Page {item.page || 'N/A'} • {item.relevance || 0}% match
                        </span>
                      </div>
                      <p className="pdbot-passage-text">{item.text}</p>
                    </>
                  ) : (
                    <>
                      <div className="pdbot-source-header">
                        <span className="pdbot-source-icon">📖</span>
                        <span className="pdbot-source-title">{item.title || 'Manual for Development Projects 2024'}</span>
                      </div>
                      <div className="pdbot-source-meta">
                        <span className="pdbot-source-page">Page {item.page || 'N/A'}</span>
                        <span className="pdbot-source-relevance">{item.relevance || 0}% relevance</span>
                      </div>
                    </>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {/* Footer */}
        <div className="pdbot-details-footer">
          <button 
            className="pdbot-btn pdbot-btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default DetailsModal;
