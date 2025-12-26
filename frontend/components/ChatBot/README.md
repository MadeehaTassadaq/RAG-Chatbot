# ChatBot UI Component

A floating chat interface for the Physical AI documentation site that includes text selection functionality and backend integration.

## Features

- **Floating Chat Interface**: Always accessible chat window with smooth animations
- **Text Selection Popup**: "Ask AI about this" popup appears when text is selected
- **Backend Integration**: Connects to FastAPI backend for AI responses
- **Responsive Design**: Works on desktop and mobile devices
- **Smooth Animations**: Using Framer Motion for polished interactions

## Components

### ChatBot
Main component that provides the floating chat interface and text selection functionality.

### ChatPopup
Contextual popup that appears when text is selected, allowing users to ask the AI about the selected content.

## Environment Variables

The component uses the following environment variables to connect to the backend:

- `REACT_APP_BACKEND_URL` or `BACKEND_URL`: URL of the FastAPI backend (defaults to `http://localhost:8000`)

## API Integration

The component communicates with the backend using these endpoints:

- `POST /chat`: Send messages to the AI assistant
- `POST /chat/selection`: Send selected text as primary context (handled internally)

## Styling

- Uses Tailwind CSS for styling
- Responsive design that works on different screen sizes
- Accessible color scheme and interactive elements

## Animation

- Uses Framer Motion for smooth transitions and animations
- Chat window slides in/out with spring physics
- Popup appears/disappears with fade and position animations

## State Management

- Tracks chat messages (user and assistant)
- Manages chat window open/closed state
- Handles loading states during API requests
- Tracks selected text and popup position

## Integration

The component is integrated into the Docusaurus site through `src/theme/Root.tsx`, making it available on all pages.

## Usage

The component is automatically included on all documentation pages. Users can:

1. Click the floating chat button to open the chat interface
2. Select text on any page to see the "Ask AI about this" popup
3. Send messages through the chat interface to get AI responses
4. Receive responses with proper citations and context