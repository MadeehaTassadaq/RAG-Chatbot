import React, { createContext, useContext, useEffect, useState } from 'react';

const ChatContext = createContext();

export const ChatProvider = ({ children, backendUrl: propBackendUrl = null }) => {
  const [backendUrl, setBackendUrl] = useState('');

  useEffect(() => {
    // First check if backend URL is provided as a prop
    if (propBackendUrl) {
      setBackendUrl(propBackendUrl);
      return;
    }

    // Otherwise, try to get it from environment or default configuration
    const url = process.env.REACT_APP_BACKEND_URL ||
                process.env.BACKEND_URL ||
                window.ENV?.REACT_APP_BACKEND_URL ||
                localStorage.getItem('backend_url') ||
                'http://localhost:8000'; // Default fallback

    setBackendUrl(url);
  }, [propBackendUrl]);

  return (
    <ChatContext.Provider value={{ backendUrl, setBackendUrl }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};