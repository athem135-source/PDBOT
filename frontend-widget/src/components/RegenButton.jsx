/**
 * RegenButton Component
 * =====================
 * 
 * Regenerate button for bot responses.
 * Allows users to request a new answer to their question.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React, { useState } from 'react';

/**
 * RegenButton - Regenerate response button
 * 
 * @param {Object} props
 * @param {Function} props.onRegenerate - Callback when clicked
 * @param {boolean} props.disabled - Whether button is disabled
 */
function RegenButton({ onRegenerate, disabled = false }) {
  const [isAnimating, setIsAnimating] = useState(false);
  
  const handleClick = () => {
    if (disabled || isAnimating) return;
    
    // Trigger spin animation
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 500);
    
    // Call callback
    if (onRegenerate) {
      onRegenerate();
    }
  };
  
  return (
    <button
      className={`pdbot-regen-btn ${isAnimating ? 'pdbot-spinning' : ''}`}
      onClick={handleClick}
      disabled={disabled}
      title="Regenerate response"
      aria-label="Regenerate response"
    >
      <svg 
        className="pdbot-regen-icon" 
        viewBox="0 0 24 24" 
        width="16" 
        height="16"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M23 4v6h-6M1 20v-6h6" />
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
      </svg>
    </button>
  );
}

export default RegenButton;
