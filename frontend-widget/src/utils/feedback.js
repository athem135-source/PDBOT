/**
 * Feedback Utility Functions for PDBOT Widget
 * ============================================
 * 
 * Handles feedback collection, validation, and submission
 * for both individual answers and session-level feedback.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import { submitAnswerFeedback, submitSessionFeedback } from './api.js';
import { getSessionId } from './storage.js';

/**
 * Dislike reasons for answer feedback
 */
export const DISLIKE_REASONS = [
  { id: 'incorrect', label: 'Incorrect', description: 'The answer contains wrong information' },
  { id: 'incomplete', label: 'Incomplete', description: 'The answer is missing important details' },
  { id: 'too_long', label: 'Too Long', description: 'The answer is unnecessarily verbose' },
  { id: 'off_topic', label: 'Off-topic', description: 'The answer doesn\'t address my question' },
  { id: 'other', label: 'Other', description: 'Different issue (please specify)' }
];

/**
 * Rating descriptions for session feedback
 */
export const RATING_DESCRIPTIONS = {
  1: { label: 'Poor', emoji: '😞', description: 'The bot was not helpful' },
  2: { label: 'Fair', emoji: '😐', description: 'The bot was somewhat helpful' },
  3: { label: 'Great', emoji: '😊', description: 'The bot was very helpful' }
};

/**
 * Create feedback object for a liked answer
 * 
 * @param {Object} message - The message object
 * @returns {Object} Formatted feedback
 */
export function createLikeFeedback(message) {
  return {
    messageId: message.id,
    query: message.query || '',
    answer: message.content,
    type: 'like',
    sessionId: getSessionId(),
    timestamp: new Date().toISOString()
  };
}

/**
 * Create feedback object for a disliked answer
 * 
 * @param {Object} message - The message object
 * @param {string} reasonId - Selected reason ID
 * @param {string} customReason - Custom text if 'other' selected
 * @returns {Object} Formatted feedback
 */
export function createDislikeFeedback(message, reasonId, customReason = '') {
  const reason = DISLIKE_REASONS.find(r => r.id === reasonId);
  
  return {
    messageId: message.id,
    query: message.query || '',
    answer: message.content,
    type: 'dislike',
    reasonId: reasonId,
    reasonLabel: reason?.label || reasonId,
    customReason: reasonId === 'other' ? customReason : '',
    sessionId: getSessionId(),
    timestamp: new Date().toISOString()
  };
}

/**
 * Create session feedback object
 * 
 * @param {number} rating - Star rating (1-3)
 * @param {string} username - Optional username
 * @param {string} review - Optional review text
 * @param {number} messageCount - Total messages in session
 * @returns {Object} Formatted session feedback
 */
export function createSessionFeedback(rating, username = '', review = '', messageCount = 0) {
  const ratingInfo = RATING_DESCRIPTIONS[rating] || RATING_DESCRIPTIONS[2];
  
  return {
    rating: rating,
    ratingLabel: ratingInfo.label,
    username: username.trim() || 'Anonymous',
    review: review.trim(),
    messageCount: messageCount,
    sessionId: getSessionId(),
    timestamp: new Date().toISOString()
  };
}

/**
 * Submit like feedback for an answer
 * 
 * @param {Object} message - The message object
 * @returns {Promise<Object>} Submission result
 */
export async function submitLike(message) {
  const feedback = createLikeFeedback(message);
  return await submitAnswerFeedback(feedback);
}

/**
 * Submit dislike feedback for an answer
 * 
 * @param {Object} message - The message object
 * @param {string} reasonId - Selected reason ID
 * @param {string} customReason - Custom reason text
 * @returns {Promise<Object>} Submission result
 */
export async function submitDislike(message, reasonId, customReason = '') {
  const feedback = createDislikeFeedback(message, reasonId, customReason);
  return await submitAnswerFeedback(feedback);
}

/**
 * Submit session feedback
 * 
 * @param {number} rating - Star rating (1-3)
 * @param {string} username - Optional username
 * @param {string} review - Optional review text
 * @param {number} messageCount - Message count
 * @returns {Promise<Object>} Submission result
 */
export async function submitSession(rating, username, review, messageCount) {
  const feedback = createSessionFeedback(rating, username, review, messageCount);
  return await submitSessionFeedback(feedback);
}

/**
 * Validate session feedback before submission
 * 
 * @param {number} rating - Star rating
 * @returns {Object} Validation result
 */
export function validateSessionFeedback(rating) {
  if (!rating || rating < 1 || rating > 3) {
    return { valid: false, error: 'Please select a rating (1-3 stars)' };
  }
  return { valid: true };
}

/**
 * Validate answer feedback before submission
 * 
 * @param {string} type - 'like' or 'dislike'
 * @param {string} reasonId - Reason ID (for dislike)
 * @param {string} customReason - Custom reason text
 * @returns {Object} Validation result
 */
export function validateAnswerFeedback(type, reasonId = '', customReason = '') {
  if (type === 'like') {
    return { valid: true };
  }
  
  if (type === 'dislike') {
    if (!reasonId) {
      return { valid: false, error: 'Please select a reason' };
    }
    if (reasonId === 'other' && !customReason.trim()) {
      return { valid: false, error: 'Please provide details for "Other"' };
    }
    return { valid: true };
  }
  
  return { valid: false, error: 'Invalid feedback type' };
}

/**
 * Generate unique message ID
 * @returns {string} Unique ID
 */
export function generateMessageId() {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export default {
  DISLIKE_REASONS,
  RATING_DESCRIPTIONS,
  createLikeFeedback,
  createDislikeFeedback,
  createSessionFeedback,
  submitLike,
  submitDislike,
  submitSession,
  validateSessionFeedback,
  validateAnswerFeedback,
  generateMessageId
};
