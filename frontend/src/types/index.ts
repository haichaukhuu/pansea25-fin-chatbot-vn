export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  provider?: 'email' | 'google';
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  chatId: string;
  isStreaming?: boolean; // True when message is being streamed
  isComplete?: boolean; // True when streaming is complete
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
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
