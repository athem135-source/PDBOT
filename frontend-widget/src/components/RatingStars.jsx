/**
 * RatingStars Component
 * =====================
 * 
 * Interactive 1-3 star rating selector for session feedback.
 * Uses gold stars with hover/click effects.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React, { useState } from 'react';
import { RATING_DESCRIPTIONS } from '../utils/feedback.js';

/**
 * RatingStars - Star rating selector
 * 
 * @param {Object} props
 * @param {number} props.rating - Current rating (1-3)
 * @param {Function} props.onChange - Callback when rating changes
 * @param {boolean} props.disabled - Whether selector is disabled
 */
function RatingStars({ rating = 0, onChange, disabled = false }) {
  const [hoverRating, setHoverRating] = useState(0);
  
  const displayRating = hoverRating || rating;
  const ratingInfo = RATING_DESCRIPTIONS[displayRating];
  
  const handleClick = (value) => {
    if (disabled) return;
    if (onChange) onChange(value);
  };
  
  const handleMouseEnter = (value) => {
    if (disabled) return;
    setHoverRating(value);
  };
  
  const handleMouseLeave = () => {
    setHoverRating(0);
  };
  
  return (
    <div className="pdbot-rating-stars">
      <div className="pdbot-stars-container" onMouseLeave={handleMouseLeave}>
        {[1, 2, 3].map((value) => (
          <button
            key={value}
            type="button"
            className={`pdbot-star ${value <= displayRating ? 'pdbot-star-filled' : 'pdbot-star-empty'}`}
            onClick={() => handleClick(value)}
            onMouseEnter={() => handleMouseEnter(value)}
            disabled={disabled}
            aria-label={`Rate ${value} stars`}
          >
            <svg viewBox="0 0 24 24" width="32" height="32">
              <path
                d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                fill={value <= displayRating ? '#d4af37' : 'none'}
                stroke="#d4af37"
                strokeWidth="2"
              />
            </svg>
          </button>
        ))}
      </div>
      
      {/* Rating label */}
      {displayRating > 0 && ratingInfo && (
        <div className="pdbot-rating-label">
          <span className="pdbot-rating-emoji">{ratingInfo.emoji}</span>
          <span className="pdbot-rating-text">{ratingInfo.label}</span>
        </div>
      )}
    </div>
  );
}

export default RatingStars;
