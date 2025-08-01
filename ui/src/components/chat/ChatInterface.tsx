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

interface ChatInterfaceProps {
  onNavigateToProfile: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ onNavigateToProfile }) => {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const { currentChat, sendMessage } = useChat();

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Chat History */}
      <ChatSidebar 
        isOpen={leftSidebarOpen}
        onToggle={() => setLeftSidebarOpen(!leftSidebarOpen)}
        onNavigateToProfile={onNavigateToProfile}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
              >
                <Bars3Icon className="h-5 w-5" />
              </button>
              <div className="hidden lg:block">
                <h1 className="text-lg font-semibold text-gray-900">
                  {currentChat?.title || 'Financial Chatbot'}
                </h1>
                <p className="text-sm text-gray-500">
                  AI-powered financial assistant for ASEAN markets
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
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
