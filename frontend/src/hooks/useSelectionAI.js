import { useState, useEffect, useCallback } from 'react';

/**
 * Custom React hook that detects text selection on the page and provides
 * functionality to send the selected text to the backend /chat/selection endpoint.
 *
 * @param {string} backendUrl - The base URL of the backend API
 * @returns {Object} - Object containing selected text, loading state, error state,
 *                    and functions to handle selection and send to backend
 */
const useSelectionAI = (backendUrl = '') => {
  const [selectedText, setSelectedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // Function to get the currently selected text
  const getSelectedText = useCallback(() => {
    return window.getSelection?.toString().trim() || '';
  }, []);

  // Function to handle text selection
  const handleSelection = useCallback(() => {
    const text = getSelectedText();
    if (text) {
      setSelectedText(text);
    } else {
      setSelectedText('');
    }
  }, [getSelectedText]);

  // Effect to add event listeners for text selection
  useEffect(() => {
    const handleMouseUp = () => {
      // Add a small delay to ensure selection is complete
      setTimeout(handleSelection, 1);
    };

    const handleKeyDown = (e) => {
      // Handle selection that might happen with keyboard (like Shift+Arrow keys)
      if (e.key === 'Shift' || e.shiftKey) {
        setTimeout(handleSelection, 1);
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('keyup', handleSelection);
    document.addEventListener('keydown', handleKeyDown);

    // Clean up event listeners
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('keyup', handleSelection);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleSelection]);

  // Function to send selected text to the backend /chat/selection endpoint
  const sendSelectionToBackend = useCallback(async (customText = null) => {
    const textToSend = customText || selectedText;

    if (!textToSend) {
      setError('No text selected to send');
      return { success: false, error: 'No text selected to send' };
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/chat/selection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_text: textToSend,
          session_id: sessionId || localStorage.getItem('chat_session_id') || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Store session ID for future requests
      if (data.session_id) {
        setSessionId(data.session_id);
        localStorage.setItem('chat_session_id', data.session_id);
      }

      setIsLoading(false);
      return { success: true, data };
    } catch (err) {
      console.error('Error sending selection to backend:', err);
      setError(err.message);
      setIsLoading(false);
      return { success: false, error: err.message };
    }
  }, [selectedText, backendUrl, sessionId]);

  // Function to clear the current selection
  const clearSelection = useCallback(() => {
    setSelectedText('');
    window.getSelection?.removeAllRanges();
  }, []);

  // Function to get selection position (useful for showing context menus)
  const getSelectionPosition = useCallback(() => {
    const selection = window.getSelection?.();
    if (!selection || selection.toString().trim() === '') {
      return null;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    return {
      x: rect.left + window.scrollX,
      y: rect.top + window.scrollY - 40, // Position above the selection
      rect,
    };
  }, []);

  return {
    selectedText,
    isLoading,
    error,
    sessionId,
    getSelectedText,
    sendSelectionToBackend,
    clearSelection,
    getSelectionPosition,
  };
};

export default useSelectionAI;