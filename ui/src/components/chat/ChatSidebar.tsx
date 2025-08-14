import React, { useState } from 'react';
import { 
  Bars3Icon, 
  PlusIcon, 
  MagnifyingGlassIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  TrashIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';
import { format, isToday, isYesterday, startOfDay } from 'date-fns';

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

  // Group chats by date
  const groupedChats = filteredChats.reduce((groups, chat) => {
    const dateKey = format(startOfDay(chat.updatedAt), 'yyyy-MM-dd');
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(chat);
    return groups;
  }, {} as Record<string, typeof filteredChats>);

  const getDateLabel = (dateStr: string) => {
    const date = new Date(dateStr);
    if (isToday(date)) return 'Today';
    if (isYesterday(date)) return 'Yesterday';
    return format(date, 'MMM d, yyyy');
  };

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
          className="fixed inset-0 bg-transparent backdrop-blur-sm z-20 lg:hidden"
          onClick={onToggle}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-80 transform transition-transform duration-300 ease-in-out
        lg:relative lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `} style={{ backgroundColor: '#27403E' }}>
        <div className="flex flex-col h-full">
          {/* Header (aligned with main and files headers) */}
          <div className="flex items-center justify-between h-16 px-4" style={{ backgroundColor: '#1a322e' }}>
            <h2 className="text-lg font-semibold tracking-tight" style={{ color: '#FFFFFF' }}>Chats</h2>
            <div className="flex items-center space-x-2">
              <button
                    onClick={handleNewChat}
                    className="p-2 rounded-lg transition-colors border"
                    style={{ 
                      backgroundColor: '#FFFFFF',
                      color: '#000000',
                      borderColor: '#21A691',
                      borderWidth: '1px',
                      boxShadow: 'none'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#21A691';
                      e.currentTarget.style.borderColor = '#87DF2C';
                      e.currentTarget.style.color = '#FFFFFF';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#FFFFFF';
                      e.currentTarget.style.borderColor = '#21A691';
                      e.currentTarget.style.color = '#000000';
                    }}
                    title="New Chat"
                  >
                    <PlusIcon className="h-5 w-5" style={{ color: '#000000' }} />
                  </button>
              <button
                onClick={onToggle}
                className="p-2 rounded-lg transition-colors lg:hidden"
                style={{ color: '#B4B4B2' }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#000000'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#000000'}
              >
                <Bars3Icon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="p-4">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4" style={{ color: '#000000' }} />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg transition-colors"
                style={{ 
                  backgroundColor: '#FFFFFF', 
                  borderColor: '#21A691', 
                  borderWidth: '1px',
                  color: '#000000'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#87DF2C';
                  e.currentTarget.style.boxShadow = '0 0 0 2px rgba(135, 223, 44, 0.2)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#21A691';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto">
            {Object.keys(groupedChats).length === 0 ? (
              <div className="text-center py-8" style={{ color: '#B4B4B2' }}>
                {searchQuery ? 'No chats found' : 'No chats yet'}
              </div>
            ) : (
              <div className="p-2 space-y-6">
                {Object.entries(groupedChats)
                  .sort(([a], [b]) => new Date(b).getTime() - new Date(a).getTime())
                  .map(([dateKey, dateChats]) => (
                    <div key={dateKey}>
                      <div className="flex items-center space-x-2 mb-3 px-1">
                        <CalendarIcon className="h-4 w-4" style={{ color: '#87DF2C' }} />
                        <h3 className="text-sm font-medium" style={{ color: '#FFFFFF' }}>
                          {getDateLabel(dateKey)}
                        </h3>
                      </div>
                      <div className="space-y-1">
                        {dateChats
                          .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
                          .map((chat) => (
                            <div
                              key={chat.id}
                              onClick={() => handleChatSelect(chat.id)}
                              className="group relative flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors"
                              style={{ 
                                backgroundColor: currentChat?.id === chat.id ? '#21A691' : 'transparent',
                                color: '#FFFFFF'
                              }}
                              onMouseEnter={(e) => {
                                if (currentChat?.id !== chat.id) {
                                  e.currentTarget.style.backgroundColor = '#1a322e';
                                }
                              }}
                              onMouseLeave={(e) => {
                                if (currentChat?.id !== chat.id) {
                                  e.currentTarget.style.backgroundColor = 'transparent';
                                }
                              }}
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
                                  {format(chat.updatedAt, 'HH:mm')}
                                </p>
                              </div>
                              <button
                                onClick={(e) => handleDeleteChat(e, chat.id)}
                                className="opacity-100 p-1 transition-opacity"
                                style={{ color: '#FFFFFF' }}
                                onMouseEnter={(e) => e.currentTarget.style.color = '#ff6b6b'}
                                onMouseLeave={(e) => e.currentTarget.style.color = '#FFFFFF'}
                                title="Delete chat"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* User Profile Section */}
          <div className="p-4" style={{ backgroundColor: '#1a322e', }}>
            <button
              onClick={onNavigateToProfile}
              className="w-full flex items-center space-x-3 p-3 rounded-lg transition-colors"
              style={{ 
                color: '#B4B4B2',
                borderColor: '#21A691'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#21A691';
                e.currentTarget.style.color = '#FFFFFF';
                e.currentTarget.style.borderColor = '#87DF2C';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = '#B4B4B2';
                e.currentTarget.style.borderColor = '#21A691';
              }}
            >
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: '#21A691' }}>
                <UserCircleIcon className="h-6 w-6" style={{ color: '#FFFFFF' }} />
              </div>
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
