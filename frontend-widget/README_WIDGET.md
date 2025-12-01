# 🤖 PDBOT React Widget

**Government of Pakistan – Ministry of Planning, Development & Special Initiatives**

A modern, floating chat widget for PDBOT - the Planning & Development Manual Assistant.

![Version](https://img.shields.io/badge/version-1.0.0-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![Vite](https://img.shields.io/badge/Vite-5.0-purple)

---

## ✨ Features

- 💬 **Floating Chat Widget** - Bottom-right positioned, always accessible
- 🎯 **Draggable** - Move the widget anywhere on screen
- 📦 **Minimizable** - Collapse to save space
- ⌨️ **Typewriter Effect** - Smooth typing animation for bot responses
- 💡 **Suggested Questions** - Quick-start with common queries
- ⭐ **Feedback System** - Like/dislike answers with reasons
- 📊 **Session Feedback** - 1-3 star rating after chat completion
- 🔄 **Regenerate Responses** - Request new answers
- 💾 **Chat Export** - Download as TXT or PDF
- 📱 **Responsive Design** - Works on desktop and mobile
- 🎨 **Government Theme** - Official Pakistani ministry colors

---

## 🎨 Theme Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Dark Green | `#006600` | Primary, headers |
| Light Green | `#1fa67a` | Accents, buttons |
| White | `#FFFFFF` | Backgrounds |
| Gold | `#d4af37` | Stars, highlights |

---

## 📁 Project Structure

```
frontend-widget/
├── src/
│   ├── index.jsx              # Entry point
│   ├── App.jsx                # Root component
│   ├── components/
│   │   ├── ChatWidget.jsx     # Main widget container
│   │   ├── ChatBubble.jsx     # Message bubbles with typewriter
│   │   ├── TypingIndicator.jsx # "PDBOT is typing..." animation
│   │   ├── SuggestedQuestions.jsx # Quick-start questions
│   │   ├── SettingsMenu.jsx   # 3-dot menu (new/clear/download)
│   │   ├── FeedbackModal.jsx  # Session feedback modal
│   │   ├── RatingStars.jsx    # Star rating component
│   │   ├── LikeDislikeButtons.jsx # Answer feedback
│   │   └── RegenButton.jsx    # Regenerate response
│   ├── utils/
│   │   ├── api.js             # API communication
│   │   ├── storage.js         # localStorage operations
│   │   └── feedback.js        # Feedback utilities
│   └── styles/
│       └── widget.css         # All CSS styles
├── index.html                 # Dev HTML page
├── package.json               # Dependencies
├── vite.config.js             # Build configuration
└── README_WIDGET.md           # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- PDBOT backend running (Streamlit app)

### Installation

```bash
# Navigate to widget folder
cd frontend-widget

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:3000` in your browser.

### Build for Production

```bash
# Build the widget
npm run build

# Output files in dist/
# - pdbot-widget.js (main bundle)
# - pdbot-widget.css (styles)
```

---

## 📦 Embedding in Websites

### Method 1: Script Tag (Recommended)

```html
<!-- Add at end of <body> -->
<script src="path/to/pdbot-widget.js"></script>
```

The widget will automatically mount and appear in the bottom-right corner.

### Method 2: Custom Mount Point

```html
<!-- Add mount point -->
<div id="pdbot-widget"></div>

<!-- Add script -->
<script src="path/to/pdbot-widget.js"></script>
```

### Method 3: Configure API URL

```html
<script>
  // Set API URL before loading widget
  window.PDBOT_API_URL = 'https://your-api-server.com';
</script>
<script src="path/to/pdbot-widget.js"></script>
```

---

## 🔌 API Integration

The widget expects a backend API with these endpoints:

### POST /chat
Send a message and get a response.

**Request:**
```json
{
  "query": "What is PC-I?",
  "session_id": "uuid-v4"
}
```

**Response:**
```json
{
  "answer": "PC-I (Project Concept-I) is...",
  "sources": ["chapter-3.pdf", "section-4.2"]
}
```

### POST /feedback/answer
Submit feedback for an individual answer.

**Request:**
```json
{
  "messageId": "msg_12345",
  "query": "What is PC-I?",
  "answer": "...",
  "type": "like|dislike",
  "reasonId": "incorrect",
  "sessionId": "uuid",
  "timestamp": "ISO-8601"
}
```

### POST /feedback/session
Submit session-level feedback.

**Request:**
```json
{
  "rating": 3,
  "ratingLabel": "Great",
  "username": "John",
  "review": "Very helpful bot!",
  "sessionId": "uuid",
  "timestamp": "ISO-8601"
}
```

---

## ⚙️ Configuration

### Suggested Questions

Edit `src/components/SuggestedQuestions.jsx`:

```javascript
const DEFAULT_QUESTIONS = [
  "What are the approval limits of DDWP?",
  "What is PC-I?",
  "How does project revision work?"
];
```

### Greeting Message

Edit `src/components/ChatWidget.jsx`:

```javascript
const GREETING_MESSAGE = "Assalam-o-Alaikum! I am PDBOT...";
```

### Theme Colors

Edit CSS variables in `src/styles/widget.css`:

```css
:root {
  --pdbot-dark-green: #006600;
  --pdbot-light-green: #1fa67a;
  --pdbot-gold: #d4af37;
}
```

---

## 🧪 Development

### Run Development Server

```bash
npm run dev
```

### Run Production Preview

```bash
npm run build
npm run preview
```

### Serve Production Build

```bash
npm run build
npx serve dist
```

---

## 📋 Feedback Data Format

### Answer Feedback (feedback/answer_feedback_*.json)

```json
{
  "messageId": "msg_1234567890_abc123",
  "query": "What is PC-I?",
  "answer": "PC-I (Project Concept-I) is...",
  "type": "dislike",
  "reasonId": "incomplete",
  "reasonLabel": "Incomplete",
  "customReason": "",
  "sessionId": "uuid-v4",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Session Feedback (feedback/session_feedback_*.json)

```json
{
  "rating": 3,
  "ratingLabel": "Great",
  "username": "Hassan",
  "review": "Very helpful for understanding the PND manual!",
  "messageCount": 12,
  "sessionId": "uuid-v4",
  "timestamp": "2024-01-15T11:00:00.000Z"
}
```

---

## 🌐 Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

---

## 📄 License

© 2024 Ministry of Planning, Development & Special Initiatives, Government of Pakistan

---

## 🔗 Links

- [PDBOT Repository](https://github.com/athem135-source/PDBOT)
- [Ministry Website](https://www.pc.gov.pk/)

---

## 📝 Changelog

### v1.0.0 (2024-12-01)
- Initial release
- Floating draggable widget
- Typewriter animation
- Suggested questions
- Like/dislike feedback
- Session rating modal
- Chat export (TXT/PDF)
- Mobile responsive design
