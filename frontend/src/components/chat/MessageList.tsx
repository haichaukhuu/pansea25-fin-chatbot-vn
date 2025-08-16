import React from 'react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';
import type { Message } from '../../types';

interface MessageListProps {
  className?: string;
}

export const MessageList: React.FC<MessageListProps> = ({ className = '' }) => {
  const { currentChat } = useChat();
  const { t } = useLanguage();

  if (!currentChat) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`} style={{ backgroundColor: '#FFFFFF' }}>
        <div className="text-center">
          <div className="mb-4" style={{ color: '#21A691' }}>
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.456L3 21l2.456-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium mb-2" style={{ color: '#27403E' }}>{t('welcome.title')}</h3>
          <p style={{ color: '#27403E' }}>
            {t('welcome.subtitle')}
          </p>
        </div>
      </div>
    );
  }

  if (currentChat.messages.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`} style={{ backgroundColor: '#FFFFFF' }}>
        <div className="text-center">
          <div className="mb-4" style={{ color: '#21A691' }}>
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.456L3 21l2.456-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium mb-2" style={{ color: '#27403E' }}>{t('welcome.new_conversation')}</h3>
          <p className="mb-4" style={{ color: '#27403E' }}>
            {t('welcome.description')}
          </p>
          <div className="space-y-2 text-sm" style={{ color: '#27403E' }}>
            <p>{t('welcome.bullet1')}</p>
            <p>{t('welcome.bullet2')}</p>
            <p>{t('welcome.bullet3')}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${className}`} style={{ backgroundColor: '#FFFFFF' }}>
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
  const { formatTime } = useLanguage();

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 ${isUser ? 'order-2 ml-2' : 'order-1 mr-2'}`}>
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium shadow-md"
          style={{
            backgroundColor: isUser ? '#21A691' : '#27403E',
            color: '#FFFFFF'
          }}
        >
          {isUser ? 'U' : 'AI'}
        </div>
      </div>

      {/* Message content */}
      <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${isUser ? 'order-1' : 'order-2'}`}>
        <div
          className="px-4 py-2 rounded-lg shadow-md"
          style={{
            backgroundColor: isUser ? '#21A691' : '#FFFFFF',
            color: isUser ? '#FFFFFF' : '#27403E',
            border: isUser ? 'none' : '2px solid #B4B4B2'
          }}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className={`mt-1 text-xs ${isUser ? 'text-right' : 'text-left'}`} style={{ color: '#B4B4B2' }}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
};
