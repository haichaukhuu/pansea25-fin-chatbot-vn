import React, { useState } from 'react';
import { 
  Bars3Icon, 
  PlusIcon, 
  MagnifyingGlassIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';
import { format } from 'date-fns';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNavigateToProfile: () => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({ 
  isOpen, 
  onToggle, 
  onNavigateToProfile 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const { chats, currentChat, createNewChat, selectChat, searchChats, deleteChat } = useChat();
  const { user } = useAuth();

  const filteredChats = searchQuery.trim() ? searchChats(searchQuery) : chats;

  const handleNewChat = () => {
    createNewChat();
  };

  const handleChatSelect = (chatId: string) => {
    selectChat(chatId);
  };

  const handleDeleteChat = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat?')) {
      deleteChat(chatId);
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={onToggle}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-80 bg-gray-900 transform transition-transform duration-300 ease-in-out
        lg:relative lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">Chats</h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleNewChat}
                className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                title="New Chat"
              >
                <PlusIcon className="h-5 w-5" />
              </button>
              <button
                onClick={onToggle}
                className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors lg:hidden"
              >
                <Bars3Icon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="p-4">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-1 p-2">
              {filteredChats.map((chat) => (
                <div
                  key={chat.id}
                  onClick={() => handleChatSelect(chat.id)}
                  className={`
                    group relative flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors
                    ${currentChat?.id === chat.id 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }
                  `}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {chat.title}
                    </p>
                    <p className="text-xs opacity-75 truncate">
                      {chat.messages.length > 0 
                        ? chat.messages[chat.messages.length - 1].content.slice(0, 50) + '...'
                        : 'No messages'
                      }
                    </p>
                    <p className="text-xs opacity-50">
                      {format(chat.updatedAt, 'MMM d, yyyy')}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteChat(e, chat.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-400 transition-opacity"
                    title="Delete chat"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
              {filteredChats.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  {searchQuery ? 'No chats found' : 'No chats yet'}
                </div>
              )}
            </div>
          </div>

          {/* User Profile Section */}
          <div className="border-t border-gray-700 p-4">
            <button
              onClick={onNavigateToProfile}
              className="w-full flex items-center space-x-3 p-3 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <UserCircleIcon className="h-8 w-8" />
              <div className="flex-1 text-left">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs opacity-75">{user?.email}</p>
              </div>
              <Cog6ToothIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
