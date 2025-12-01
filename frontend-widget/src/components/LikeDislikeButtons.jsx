/**
 * LikeDislikeButtons Component
 * ============================
 * 
 * Thumbs up/down buttons for answer feedback.
 * Dislike opens a mini modal for selecting reasons.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React, { useState } from 'react';
import { DISLIKE_REASONS, submitLike, submitDislike } from '../utils/feedback.js';

/**
 * LikeDislikeButtons - Feedback buttons for bot responses
 * 
 * @param {Object} props
 * @param {Object} props.message - The message being rated
 * @param {Function} props.onFeedback - Callback after feedback submitted
 * @param {boolean} props.disabled - Whether buttons are disabled
 */
function LikeDislikeButtons({ message, onFeedback, disabled = false }) {
  const [feedback, setFeedback] = useState(null); // 'like' | 'dislike' | null
  const [showReasons, setShowReasons] = useState(false);
  const [selectedReason, setSelectedReason] = useState('');
  const [customReason, setCustomReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Handle like click
  const handleLike = async () => {
    if (disabled || feedback || isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await submitLike(message);
      setFeedback('like');
      if (onFeedback) onFeedback('like', message);
    } catch (error) {
      console.error('Failed to submit like:', error);
    }
    setIsSubmitting(false);
  };
  
  // Handle dislike click - show reasons
  const handleDislike = () => {
    if (disabled || feedback || isSubmitting) return;
    setShowReasons(true);
  };
  
  // Submit dislike with reason
  const handleSubmitDislike = async () => {
    if (!selectedReason) return;
    
    setIsSubmitting(true);
    try {
      await submitDislike(message, selectedReason, customReason);
      setFeedback('dislike');
      setShowReasons(false);
      if (onFeedback) onFeedback('dislike', message, selectedReason);
    } catch (error) {
      console.error('Failed to submit dislike:', error);
    }
    setIsSubmitting(false);
  };
  
  // Cancel dislike
  const handleCancel = () => {
    setShowReasons(false);
    setSelectedReason('');
    setCustomReason('');
  };
  
  // Skip feedback
  const handleSkip = () => {
    setShowReasons(false);
    setSelectedReason('');
    setCustomReason('');
  };
  
  return (
    <div className="pdbot-like-dislike">
      {/* Like/Dislike buttons */}
      <div className="pdbot-feedback-buttons">
        <button
          className={`pdbot-like-btn ${feedback === 'like' ? 'pdbot-active' : ''}`}
          onClick={handleLike}
          disabled={disabled || feedback !== null || isSubmitting}
          title="Helpful"
          aria-label="Mark as helpful"
        >
          👍
        </button>
        
        <button
          className={`pdbot-dislike-btn ${feedback === 'dislike' ? 'pdbot-active' : ''}`}
          onClick={handleDislike}
          disabled={disabled || feedback !== null || isSubmitting}
          title="Not helpful"
          aria-label="Mark as not helpful"
        >
          👎
        </button>
      </div>
      
      {/* Dislike reasons modal */}
      {showReasons && (
        <div className="pdbot-dislike-modal">
          <div className="pdbot-dislike-header">
            <span>What was wrong?</span>
            <button 
              className="pdbot-dislike-close"
              onClick={handleCancel}
              aria-label="Close"
            >
              ×
            </button>
          </div>
          
          <div className="pdbot-dislike-reasons">
            {DISLIKE_REASONS.map((reason) => (
              <label 
                key={reason.id}
                className={`pdbot-reason-option ${selectedReason === reason.id ? 'pdbot-selected' : ''}`}
              >
                <input
                  type="radio"
                  name="dislike-reason"
                  value={reason.id}
                  checked={selectedReason === reason.id}
                  onChange={(e) => setSelectedReason(e.target.value)}
                />
                <span className="pdbot-reason-label">{reason.label}</span>
              </label>
            ))}
          </div>
          
          {/* Custom reason text field */}
          {selectedReason === 'other' && (
            <textarea
              className="pdbot-custom-reason"
              placeholder="Please describe the issue..."
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              rows={2}
            />
          )}
          
          <div className="pdbot-dislike-actions">
            <button
              className="pdbot-skip-btn"
              onClick={handleSkip}
            >
              Skip
            </button>
            <button
              className="pdbot-submit-btn"
              onClick={handleSubmitDislike}
              disabled={!selectedReason || (selectedReason === 'other' && !customReason.trim())}
            >
              Submit
            </button>
          </div>
        </div>
      )}
      
      {/* Feedback confirmation */}
      {feedback && (
        <span className="pdbot-feedback-thanks">
          {feedback === 'like' ? 'Thanks! 👍' : 'Thanks for feedback'}
        </span>
      )}
    </div>
  );
}

export default LikeDislikeButtons;
