export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  hasCompletedOnboarding?: boolean;
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  chatId: string;
  conversationId?: string; // Added for backend compatibility
  isStreaming?: boolean; // True when message is being streamed
  isComplete?: boolean; // True when streaming is complete
}

export interface Chat {
  id: string;
  conversationId?: string; // Added for backend compatibility
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  lastMessage?: string; // Added for display purposes
  messageCount?: number; // Added for display purposes
}

export interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  createdAt: Date;
  chatId: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}
