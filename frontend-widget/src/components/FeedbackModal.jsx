/**
 * FeedbackModal Component
 * =======================
 * 
 * Session feedback modal displayed after Clear/New Chat.
 * Collects star rating, optional username, and review text.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React, { useState } from 'react';
import RatingStars from './RatingStars.jsx';
import { submitSession, validateSessionFeedback } from '../utils/feedback.js';

/**
 * FeedbackModal - Session feedback collection
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Callback when modal closes
 * @param {Function} props.onSubmit - Callback after successful submission
 * @param {number} props.messageCount - Number of messages in session
 */
function FeedbackModal({ isOpen, onClose, onSubmit, messageCount = 0 }) {
  const [rating, setRating] = useState(0);
  const [username, setUsername] = useState('');
  const [review, setReview] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Reset form when modal opens
  React.useEffect(() => {
    if (isOpen) {
      setRating(0);
      setUsername('');
      setReview('');
      setError('');
    }
  }, [isOpen]);
  
  // Handle form submission
  const handleSubmit = async () => {
    // Validate
    const validation = validateSessionFeedback(rating);
    if (!validation.valid) {
      setError(validation.error);
      return;
    }
    
    setIsSubmitting(true);
    setError('');
    
    try {
      await submitSession(rating, username, review, messageCount);
      if (onSubmit) onSubmit({ rating, username, review });
      onClose();
    } catch (err) {
      setError('Failed to submit feedback. Please try again.');
      console.error('Feedback submission error:', err);
    }
    
    setIsSubmitting(false);
  };
  
  // Handle skip
  const handleSkip = () => {
    onClose();
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="pdbot-modal-overlay">
      <div className="pdbot-feedback-modal">
        {/* Header */}
        <div className="pdbot-modal-header">
          <h3 className="pdbot-modal-title">
            <span className="pdbot-modal-icon">📝</span>
            How was your experience?
          </h3>
          <button 
            className="pdbot-modal-close"
            onClick={handleSkip}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        
        {/* Body */}
        <div className="pdbot-modal-body">
          {/* Star Rating */}
          <div className="pdbot-form-group">
            <label className="pdbot-form-label">Rate your experience</label>
            <RatingStars 
              rating={rating}
              onChange={setRating}
              disabled={isSubmitting}
            />
          </div>
          
          {/* Username (optional) */}
          <div className="pdbot-form-group">
            <label className="pdbot-form-label">
              Your name <span className="pdbot-optional">(optional)</span>
            </label>
            <input
              type="text"
              className="pdbot-form-input"
              placeholder="Enter your name"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isSubmitting}
              maxLength={50}
            />
          </div>
          
          {/* Review (optional) */}
          <div className="pdbot-form-group">
            <label className="pdbot-form-label">
              Your feedback <span className="pdbot-optional">(optional)</span>
            </label>
            <textarea
              className="pdbot-form-textarea"
              placeholder="Tell us about your experience..."
              value={review}
              onChange={(e) => setReview(e.target.value)}
              disabled={isSubmitting}
              rows={3}
              maxLength={500}
            />
            <span className="pdbot-char-count">{review.length}/500</span>
          </div>
          
          {/* Error message */}
          {error && (
            <div className="pdbot-form-error">{error}</div>
          )}
        </div>
        
        {/* Footer */}
        <div className="pdbot-modal-footer">
          <button 
            className="pdbot-btn pdbot-btn-secondary"
            onClick={handleSkip}
            disabled={isSubmitting}
          >
            Skip
          </button>
          <button 
            className="pdbot-btn pdbot-btn-primary"
            onClick={handleSubmit}
            disabled={isSubmitting || rating === 0}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default FeedbackModal;
