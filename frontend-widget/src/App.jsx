/**
 * App Component - PDBOT Widget Root
 * ==================================
 * 
 * Root application component that renders the ChatWidget.
 * This is the main entry point for the React application.
 * 
 * @author Ministry of Planning, Development & Special Initiatives
 * @version 1.0.0
 */

import React from 'react';
import ChatWidget from './components/ChatWidget.jsx';
import './styles/widget.css';

/**
 * App - Root component
 * Renders the floating chat widget
 */
function App() {
  return (
    <div className="pdbot-app">
      <ChatWidget />
    </div>
  );
}

export default App;
