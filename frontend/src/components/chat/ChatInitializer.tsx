import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';

interface ChatInitializerProps {
  children: React.ReactNode;
}

export const ChatInitializer: React.FC<ChatInitializerProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const { chats, initializeForNewUser } = useChat();

  useEffect(() => {
    // When user is authenticated and has no chats, create a new chat
    if (isAuthenticated && user && chats.length === 0) {
      initializeForNewUser();
    }
  }, [isAuthenticated, user, chats.length, initializeForNewUser]);

  return <>{children}</>;
};
