import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';

interface ChatInitializerProps {
  children: React.ReactNode;
}

export const ChatInitializer: React.FC<ChatInitializerProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const { hasLoadedInitialHistory, loadChatHistory } = useChat();

  useEffect(() => {
    // When user is authenticated and conversation history hasn't been loaded yet, load it
    if (isAuthenticated && user && !hasLoadedInitialHistory) {
      loadChatHistory().catch(error => {
        console.error('Failed to load chat history:', error);
      });
    }
  }, [isAuthenticated, user, hasLoadedInitialHistory, loadChatHistory]);

  return <>{children}</>;
};
