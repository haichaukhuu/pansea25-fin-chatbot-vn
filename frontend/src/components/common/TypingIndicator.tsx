import React from 'react';
import { useLanguage } from '../../context/LanguageContext';

interface TypingIndicatorProps {
  className?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ className = '' }) => {
  const { t } = useLanguage();
  
  return (
    <div className={`flex ${className}`}>
      {/* Avatar */}
      <div className="flex-shrink-0 order-1 mr-2">
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium shadow-md"
          style={{
            backgroundColor: '#27403E',
            color: '#FFFFFF'
          }}
        >
          AI
        </div>
      </div>

      {/* Typing indicator content */}
      <div className="max-w-xs lg:max-w-md xl:max-w-lg order-2">
        <div
          className="px-4 py-3 rounded-lg shadow-md flex items-center space-x-1"
          style={{
            backgroundColor: '#FFFFFF',
            color: '#27403E',
            border: '2px solid #B4B4B2'
          }}
        >
          <div className="flex space-x-1">
            <div 
              className="w-2 h-2 rounded-full animate-bounce"
              style={{ 
                backgroundColor: '#21A691',
                animationDelay: '0ms',
                animationDuration: '1400ms'
              }}
            />
            <div 
              className="w-2 h-2 rounded-full animate-bounce"
              style={{ 
                backgroundColor: '#21A691',
                animationDelay: '200ms',
                animationDuration: '1400ms'
              }}
            />
            <div 
              className="w-2 h-2 rounded-full animate-bounce"
              style={{ 
                backgroundColor: '#21A691',
                animationDelay: '400ms',
                animationDuration: '1400ms'
              }}
            />
          </div>
          <span className="text-sm ml-2" style={{ color: '#B4B4B2' }}>{t('chat.ai_responding')}</span>
        </div>
      </div>
    </div>
  );
};
