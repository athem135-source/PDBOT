/**
 * SuggestedQuestions Component
 * ============================
 * 
 * Displays clickable suggested questions to help users get started.
 * Customizable questions with default PND-related examples.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React from 'react';

// Default suggested questions (PND Manual related)
const DEFAULT_QUESTIONS = [
  "What are the approval limits of DDWP?",
  "What is PC-I?",
  "How does project revision work?"
];

/**
 * SuggestedQuestions - Clickable question chips
 * 
 * @param {Object} props
 * @param {Array} props.questions - Array of question strings (optional)
 * @param {Function} props.onSelect - Callback when a question is clicked
 * @param {boolean} props.disabled - Whether buttons are disabled
 */
function SuggestedQuestions({ 
  questions = DEFAULT_QUESTIONS, 
  onSelect,
  disabled = false 
}) {
  const handleClick = (question) => {
    if (!disabled && onSelect) {
      onSelect(question);
    }
  };
  
  return (
    <div className="pdbot-suggested-questions">
      <div className="pdbot-suggested-label">
        <span className="pdbot-suggested-icon">💡</span>
        Suggested Questions
      </div>
      <div className="pdbot-suggested-list">
        {questions.map((question, index) => (
          <button
            key={index}
            className="pdbot-suggested-btn"
            onClick={() => handleClick(question)}
            disabled={disabled}
            title={question}
          >
            <span className="pdbot-suggested-text">{question}</span>
            <span className="pdbot-suggested-arrow">→</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default SuggestedQuestions;
export { DEFAULT_QUESTIONS };
