import React, { useState } from 'react';
import { 
  Bars3Icon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';
import { ChatSidebar } from './ChatSidebar';
import { FilesSidebar } from './FilesSidebar';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';
import LanguageSelector from '../common/LanguageSelector';

interface ChatInterfaceProps {
  onNavigateToProfile: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ onNavigateToProfile }) => {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const { currentChat, sendMessage } = useChat();
  const { t } = useLanguage();

  const handleSendMessage = async (message: string) => {
    await sendMessage(message);
  };

  return (
    <div className="flex h-screen" style={{ backgroundColor: '#B4B4B2' }}>
      {/* Left Sidebar - Chat History */}
      <ChatSidebar 
        isOpen={leftSidebarOpen}
        onToggle={() => setLeftSidebarOpen(!leftSidebarOpen)}
        onNavigateToProfile={onNavigateToProfile}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header (aligned) */}
        <div className="h-16 px-4 flex items-center justify-between" style={{ backgroundColor: '#21A691' }}>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
                className="p-2 rounded-lg transition-colors lg:hidden"
                style={{ color: '#FFFFFF' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1d9485'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <Bars3Icon className="h-5 w-5" />
              </button>
                              <div className="hidden lg:block">
                  <div className="flex items-center space-x-2">
                    <h1 className="text-lg font-semibold" style={{ color: '#FFFFFF' }}>
                      {currentChat?.title || t('header.title')}
                    </h1>
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#87DF2C' }}></div>
                  </div>
                  <p className="text-sm" style={{ color: '#E6F7F4' }}>
                    {t('header.subtitle')}
                  </p>
                </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <LanguageSelector />
              <button
                onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
                className="p-2 rounded-lg transition-colors"
                style={{ color: '#FFFFFF' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1d9485'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                title="Toggle files panel"
              >
                <ArchiveBoxIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <MessageList className="flex-1" />
          <MessageInput onSendMessage={handleSendMessage} />
        </div>
      </div>

      {/* Right Sidebar - Files */}
      <FilesSidebar 
        isOpen={rightSidebarOpen}
        onToggle={() => setRightSidebarOpen(!rightSidebarOpen)}
      />
    </div>
  );
};
