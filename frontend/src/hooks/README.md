# React Hooks

This directory contains custom React hooks for the Docusaurus frontend.

## Available Hooks

### `useSelectionAI.js`

A custom React hook that detects text selection on the page and provides functionality to send the selected text to the backend `/chat/selection` endpoint as context for the AI assistant.

#### Features
- Detects text selection using mouse and keyboard events
- Captures the selected text string
- Provides function to send selected text to `/chat/selection` endpoint
- Handles loading and error states
- Manages session ID for conversation continuity

#### Usage

```javascript
import useSelectionAI from './hooks/useSelectionAI';

const MyComponent = () => {
  const {
    selectedText,
    isLoading,
    error,
    sendSelectionToBackend,
    clearSelection,
    getSelectionPosition
  } = useSelectionAI('http://localhost:8000'); // Backend URL

  const handleSendSelection = async () => {
    const result = await sendSelectionToBackend();
    if (result.success) {
      console.log('Selection sent successfully');
    } else {
      console.error('Error sending selection:', result.error);
    }
  };

  return (
    <div>
      {selectedText && (
        <div>
          <p>Selected: {selectedText.substring(0, 50)}...</p>
          <button onClick={handleSendSelection} disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send to AI'}
          </button>
          <button onClick={clearSelection}>Clear</button>
        </div>
      )}
      {error && <p>Error: {error}</p>}
    </div>
  );
};
```

#### API
- `selectedText`: The currently selected text string
- `isLoading`: Boolean indicating if a request is in progress
- `error`: Error message if there was an error
- `sessionId`: Current session ID for conversation continuity
- `getSelectedText()`: Function to get the current selection
- `sendSelectionToBackend(text?)`: Function to send selection to backend (optionally with custom text)
- `clearSelection()`: Function to clear the current selection
- `getSelectionPosition()`: Function to get the position of the selection (useful for context menus)