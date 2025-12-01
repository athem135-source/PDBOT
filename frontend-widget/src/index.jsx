/**
 * PDBOT Widget - Entry Point
 * ==========================
 * 
 * Main entry point for the PDBOT React widget.
 * Mounts the widget to #pdbot-widget element.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

/**
 * Mount the PDBOT widget
 * Looks for #pdbot-widget element, creates one if not found
 */
function mountWidget() {
  // Find or create mount point
  let container = document.getElementById('pdbot-widget');
  
  if (!container) {
    container = document.createElement('div');
    container.id = 'pdbot-widget';
    document.body.appendChild(container);
    console.log('[PDBOT] Created mount point #pdbot-widget');
  }
  
  // Create React root and render
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  
  console.log('[PDBOT] Widget mounted successfully');
}

/**
 * Initialize widget when DOM is ready
 */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountWidget);
} else {
  mountWidget();
}

// Export for programmatic use
export { mountWidget };
export default App;
