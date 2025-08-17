import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { Chat, Message, FileItem } from '../types';
import { apiService, type ChatMessage } from '../services/api';

interface ChatContextType {
  chats: Chat[];
  currentChat: Chat | null;
  files: FileItem[];
  isStreaming: boolean;
  streamingMessage: Message | null;
  createNewChat: () => string;
  selectChat: (chatId: string) => void;
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>;
  searchChats: (query: string) => Chat[];
  uploadFile: (file: File) => Promise<void>;
  deleteChat: (chatId: string) => void;
  initializeForNewUser: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Demo data
const DEMO_CHATS: Chat[] = [
  {
    id: '1',
    title: 'Demo Chatbot Tài chính',
    createdAt: new Date(2025, 6, 30),
    updatedAt: new Date(2025, 6, 30),
    messages: [
      {
        id: '1',
        content: 'Xin chào! Bạn có thể giúp tôi lập kế hoạch tài chính không?',
        sender: 'user',
        timestamp: new Date(2025, 6, 30, 10, 0),
        chatId: '1'
      },
      {
        id: '2',
        content: 'Tất nhiên! Tôi rất vui được giúp bạn lập kế hoạch tài chính. Hãy bắt đầu với mục tiêu tài chính của bạn. Bạn muốn đạt được điều gì?',
        sender: 'bot',
        timestamp: new Date(2025, 6, 30, 10, 1),
        chatId: '1'
      }
    ]
  },
  {
    id: '2',
    title: 'Trợ giúp Chatbot Tài chính',
    createdAt: new Date(2025, 6, 29),
    updatedAt: new Date(2025, 6, 29),
    messages: [
      {
        id: '3',
        content: 'Những chiến lược đầu tư nào tốt cho người mới bắt đầu?',
        sender: 'user',
        timestamp: new Date(2025, 6, 29, 14, 30),
        chatId: '2'
      },
      {
        id: '4',
        content: 'Đối với người mới bắt đầu, tôi khuyên bạn nên bắt đầu với quỹ chỉ số đa dạng hóa, thiết lập quỹ khẩn cấp và hiểu rõ mức độ chấp nhận rủi ro của mình. Bạn có muốn tôi giải thích chi tiết về bất kỳ điều nào trong số này không?',
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
    name: 'Kế_hoạch_Tài_chính_2025.pdf',
    type: 'application/pdf',
    size: 1024000,
    url: '/demo/financial_plan.pdf',
    createdAt: new Date(2025, 6, 30),
    chatId: '1'
  },
  {
    id: '2',
    name: 'Danh_mục_Đầu_tư.xlsx',
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    size: 512000,
    url: '/demo/portfolio.xlsx',
    createdAt: new Date(2025, 6, 29),
    chatId: '2'
  }
];

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);

  const createNewChat = (): string => {
    const newChat: Chat = {
      id: Math.random().toString(36).substr(2, 9),
      title: 'Cuộc trò chuyện mới',
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

  const sendMessage = async (content: string, useStreaming: boolean = true) => {
    if (!currentChat) return;

    const userMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      content,
      sender: 'user',
      timestamp: new Date(),
      chatId: currentChat.id
    };

    // Add user message immediately
    const chatWithUserMessage = {
      ...currentChat,
      messages: [...currentChat.messages, userMessage],
      updatedAt: new Date(),
      title: currentChat.messages.length === 0 ? content.slice(0, 30) + '...' : currentChat.title
    };

    setChats(prev => prev.map(chat => 
      chat.id === currentChat.id ? chatWithUserMessage : chat
    ));
    setCurrentChat(chatWithUserMessage);

    try {
      // Prepare chat history for API call
      const chatHistory: ChatMessage[] = chatWithUserMessage.messages.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'bot',
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      }));

      const request = {
        message: content,
        chat_history: chatHistory.slice(0, -1), // Exclude the current message we just sent
        user_profile: {} // You can add user profile data here if available
      };

      if (useStreaming) {
        // Use streaming approach
        setIsStreaming(true);
        
        // Create initial streaming message
        const streamingMsg: Message = {
          id: Math.random().toString(36).substr(2, 9),
          content: '',
          sender: 'bot',
          timestamp: new Date(),
          chatId: currentChat.id,
          isStreaming: true,
          isComplete: false
        };

        setStreamingMessage(streamingMsg);

        // Add streaming message to chat
        const chatWithStreamingMessage = {
          ...chatWithUserMessage,
          messages: [...chatWithUserMessage.messages, streamingMsg],
          updatedAt: new Date()
        };

        setChats(prev => prev.map(chat => 
          chat.id === currentChat.id ? chatWithStreamingMessage : chat
        ));
        setCurrentChat(chatWithStreamingMessage);

        await apiService.sendStreamingMessage(
          request,
          // On chunk received
          (chunk: string) => {
            setStreamingMessage(prevMsg => {
              if (!prevMsg) return null;
              const updatedMsg = {
                ...prevMsg,
                content: prevMsg.content + chunk
              };
              
              // Update the message in the chat
              setChats(prev => prev.map(chat => 
                chat.id === currentChat.id 
                  ? {
                      ...chat,
                      messages: chat.messages.map(msg => 
                        msg.id === updatedMsg.id ? updatedMsg : msg
                      )
                    }
                  : chat
              ));
              setCurrentChat(prev => prev ? {
                ...prev,
                messages: prev.messages.map(msg => 
                  msg.id === updatedMsg.id ? updatedMsg : msg
                )
              } : null);

              return updatedMsg;
            });
          },
          // On complete
          () => {
            setIsStreaming(false);
            setStreamingMessage(prevMsg => {
              if (!prevMsg) return null;
              const completedMsg = {
                ...prevMsg,
                isStreaming: false,
                isComplete: true
              };

              // Update the final message in the chat
              setChats(prev => prev.map(chat => 
                chat.id === currentChat.id 
                  ? {
                      ...chat,
                      messages: chat.messages.map(msg => 
                        msg.id === completedMsg.id ? completedMsg : msg
                      )
                    }
                  : chat
              ));
              setCurrentChat(prev => prev ? {
                ...prev,
                messages: prev.messages.map(msg => 
                  msg.id === completedMsg.id ? completedMsg : msg
                )
              } : null);

              return null; // Clear streaming message
            });
          },
          // On error
          (error: Error) => {
            console.error('Streaming error:', error);
            setIsStreaming(false);
            setStreamingMessage(null);
            
            // Add error message
            const errorMessage: Message = {
              id: Math.random().toString(36).substr(2, 9),
              content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
              sender: 'bot',
              timestamp: new Date(),
              chatId: currentChat.id
            };

            const errorChat = {
              ...chatWithUserMessage,
              messages: [...chatWithUserMessage.messages, errorMessage],
              updatedAt: new Date()
            };

            setChats(prev => prev.map(chat => 
              chat.id === currentChat.id ? errorChat : chat
            ));
            setCurrentChat(errorChat);
          }
        );
      } else {
        // Use non-streaming approach (fallback)
        const response = await apiService.sendMessage(request);

        // Create bot response message
        const botMessage: Message = {
          id: Math.random().toString(36).substr(2, 9),
          content: response.response,
          sender: 'bot',
          timestamp: new Date(),
          chatId: currentChat.id,
          isComplete: true
        };

        // Update chat with bot response
        const updatedChat = {
          ...chatWithUserMessage,
          messages: [...chatWithUserMessage.messages, botMessage],
          updatedAt: new Date()
        };

        setChats(prev => prev.map(chat => 
          chat.id === currentChat.id ? updatedChat : chat
        ));
        setCurrentChat(updatedChat);
      }

    } catch (error) {
      console.error('Failed to get AI response:', error);
      setIsStreaming(false);
      setStreamingMessage(null);
      
      // Fallback to error message if API fails
      const errorMessage: Message = {
        id: Math.random().toString(36).substr(2, 9),
        content: 'Sorry, I encountered an error while processing your message. Please make sure the backend server is running and try again.',
        sender: 'bot',
        timestamp: new Date(),
        chatId: currentChat.id
      };

      const errorChat = {
        ...chatWithUserMessage,
        messages: [...chatWithUserMessage.messages, errorMessage],
        updatedAt: new Date()
      };

      setChats(prev => prev.map(chat => 
        chat.id === currentChat.id ? errorChat : chat
      ));
      setCurrentChat(errorChat);
    }
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

  const initializeForNewUser = () => {
    // Create a new chat for the user when they sign in
    const newChat: Chat = {
      id: Math.random().toString(36).substr(2, 9),
      title: 'Cuộc trò chuyện mới',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    setChats([newChat]);
    setCurrentChat(newChat);
    setFiles([]);
  };

  return (
    <ChatContext.Provider value={{
      chats,
      currentChat,
      files,
      isStreaming,
      streamingMessage,
      createNewChat,
      selectChat,
      sendMessage,
      searchChats,
      uploadFile,
      deleteChat,
      initializeForNewUser
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
