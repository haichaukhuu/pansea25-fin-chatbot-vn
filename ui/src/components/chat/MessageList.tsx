import React from 'react';
import { format } from 'date-fns';
import { useChat } from '../../context/ChatContext';
import type { Message } from '../../types';

interface MessageListProps {
  className?: string;
}

export const MessageList: React.FC<MessageListProps> = ({ className = '' }) => {
  const { currentChat } = useChat();

  if (!currentChat) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.456L3 21l2.456-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Welcome to Financial Chatbot</h3>
          <p className="text-gray-500">
            Start a conversation or select a chat from the sidebar
          </p>
        </div>
      </div>
    );
  }

  if (currentChat.messages.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <div className="text-blue-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.456L3 21l2.456-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Start a New Conversation</h3>
          <p className="text-gray-500 mb-4">
            Ask me anything about financial planning, investments, or ASEAN markets
          </p>
          <div className="space-y-2 text-sm text-gray-400">
            <p>• Get personalized financial advice</p>
            <p>• Learn about investment strategies</p>
            <p>• Explore ASEAN financial markets</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${className}`}>
      {currentChat.messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
};

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900 border border-gray-200'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
          {format(message.timestamp, 'HH:mm')}
        </div>
      </div>
      
      {/* Avatar */}
      <div className={`flex-shrink-0 ${isUser ? 'order-2 ml-1' : 'order-2 mr-1'}`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-300 text-gray-600'
          }`}
        >
          {isUser ? 'U' : 'AI'}
        </div>
      </div>
    </div>
  );
};
