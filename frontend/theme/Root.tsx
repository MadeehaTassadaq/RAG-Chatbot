import React from 'react';
import ChatBot from '../components/ChatBot';

// Default implementation, that you can customize
const Root = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      {children}
      <ChatBot />
    </>
  );
};

export default Root;