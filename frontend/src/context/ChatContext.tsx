import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { Chat, Message, FileItem } from '../types';

interface ChatContextType {
  chats: Chat[];
  currentChat: Chat | null;
  files: FileItem[];
  createNewChat: () => string;
  selectChat: (chatId: string) => void;
  sendMessage: (content: string) => void;
  searchChats: (query: string) => Chat[];
  uploadFile: (file: File) => Promise<void>;
  deleteChat: (chatId: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Demo data
const DEMO_CHATS: Chat[] = [
  {
    id: '1',
    title: 'Financial Chatbot Demo',
    createdAt: new Date(2025, 6, 30),
    updatedAt: new Date(2025, 6, 30),
    messages: [
      {
        id: '1',
        content: 'Hello! Can you help me with financial planning?',
        sender: 'user',
        timestamp: new Date(2025, 6, 30, 10, 0),
        chatId: '1'
      },
      {
        id: '2',
        content: 'Of course! I\'d be happy to help you with financial planning. Let\'s start with your financial goals. What are you looking to achieve?',
        sender: 'bot',
        timestamp: new Date(2025, 6, 30, 10, 1),
        chatId: '1'
      }
    ]
  },
  {
    id: '2',
    title: 'Financial Chatbot Help',
    createdAt: new Date(2025, 6, 29),
    updatedAt: new Date(2025, 6, 29),
    messages: [
      {
        id: '3',
        content: 'What are some good investment strategies for beginners?',
        sender: 'user',
        timestamp: new Date(2025, 6, 29, 14, 30),
        chatId: '2'
      },
      {
        id: '4',
        content: 'For beginners, I recommend starting with diversified index funds, setting up an emergency fund, and understanding your risk tolerance. Would you like me to explain any of these in detail?',
        sender: 'bot',
        timestamp: new Date(2025, 6, 29, 14, 31),
        chatId: '2'
      }
    ]
  }
];

const DEMO_FILES: FileItem[] = [
  {
    id: '1',
    name: 'Financial_Plan_2025.pdf',
    type: 'application/pdf',
    size: 1024000,
    url: '/demo/financial_plan.pdf',
    createdAt: new Date(2025, 6, 30),
    chatId: '1'
  },
  {
    id: '2',
    name: 'Investment_Portfolio.xlsx',
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    size: 512000,
    url: '/demo/portfolio.xlsx',
    createdAt: new Date(2025, 6, 29),
    chatId: '2'
  }
];

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [chats, setChats] = useState<Chat[]>(DEMO_CHATS);
  const [currentChat, setCurrentChat] = useState<Chat | null>(DEMO_CHATS[0]);
  const [files, setFiles] = useState<FileItem[]>(DEMO_FILES);

  const createNewChat = (): string => {
    const newChat: Chat = {
      id: Math.random().toString(36).substr(2, 9),
      title: 'Financial Chatbot',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChat(newChat);
    return newChat.id;
  };

  const selectChat = (chatId: string) => {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      setCurrentChat(chat);
    }
  };

  const sendMessage = (content: string) => {
    if (!currentChat) return;

    const userMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      content,
      sender: 'user',
      timestamp: new Date(),
      chatId: currentChat.id
    };

    // Simulate bot response
    const botMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      content: 'Thank you for your message. This is a demo response from the AI assistant. In the actual implementation, this would be connected to your Python backend.',
      sender: 'bot',
      timestamp: new Date(Date.now() + 1000),
      chatId: currentChat.id
    };

    const updatedChat = {
      ...currentChat,
      messages: [...currentChat.messages, userMessage, botMessage],
      updatedAt: new Date(),
      title: currentChat.messages.length === 0 ? content.slice(0, 30) + '...' : currentChat.title
    };

    setChats(prev => prev.map(chat => 
      chat.id === currentChat.id ? updatedChat : chat
    ));
    setCurrentChat(updatedChat);
  };

  const searchChats = (query: string): Chat[] => {
    if (!query.trim()) return chats;
    
    return chats.filter(chat => 
      chat.title.toLowerCase().includes(query.toLowerCase()) ||
      chat.messages.some(message => 
        message.content.toLowerCase().includes(query.toLowerCase())
      )
    );
  };

  const uploadFile = async (file: File): Promise<void> => {
    const newFile: FileItem = {
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: file.type,
      size: file.size,
      url: URL.createObjectURL(file),
      createdAt: new Date(),
      chatId: currentChat?.id || ''
    };
    setFiles(prev => [newFile, ...prev]);
  };

  const deleteChat = (chatId: string) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChat?.id === chatId) {
      setCurrentChat(chats.length > 1 ? chats[0] : null);
    }
  };

  return (
    <ChatContext.Provider value={{
      chats,
      currentChat,
      files,
      createNewChat,
      selectChat,
      sendMessage,
      searchChats,
      uploadFile,
      deleteChat
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
