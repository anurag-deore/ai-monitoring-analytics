import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChatIcon, DashboardIcon, SettingsIcon } from './icons/dashbaord.icon';
import useChatStore from './store/chatstore';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const [isChatsExpanded, setIsChatsExpanded] = useState(false);
  const { chats, setChats } = useChatStore();
  const [isLoadingChats, setIsLoadingChats] = useState(false);

  // Fetch chats on component mount
  useEffect(() => {
    if (location.pathname.startsWith('/chat')) {
      setIsChatsExpanded(true);
    }
    const fetchChats = async () => {
      setIsLoadingChats(true);
      try {
        const response = await fetch('http://localhost:8001/chats');
        if (response.ok) {
          const chatsData = await response.json();
          setChats(chatsData?.data?.chats || []);
        } else {
          console.error('Failed to fetch chats');
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
      } finally {
        setIsLoadingChats(false);
      }
    };

    fetchChats();
  }, []);

  const handleDeleteChat = async (chatId: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Show confirmation dialog
    const confirmed = window.confirm('Are you sure you want to delete this chat? This action cannot be undone.');
    
    if (!confirmed) {
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8001/chats/${chatId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        // Remove chat from local state
        setChats(chats.filter(chat => chat.chat_id !== chatId));
      } else {
        console.error('Failed to delete chat');
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  return (
    <div className="flex flex-col w-[20vw] h-full shrink-0 bg-white shadow-lg border-r border-gray-200 overflow-hidden ">
      {/* Navigation */}
      <nav className="flex-1 py-2 pl-2 pr-0 space-y-1.5 max-h-full overflow-hidden">
        <div className="space-y-2 pr-4 max-h-full h-full overflow-y-auto">
          <Link
            key={"reports"}
            to={"/reports"}
            className={`group flex items-center px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
              location.pathname === '/reports'
                ? 'bg-purple-50 text-purple-700'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
            }`}
          >
            <span className="mr-3 w-6 h-6">
              <DashboardIcon />
            </span>
            Reports
          </Link>

          <div className="space-y-1">
            <button
              onClick={() => setIsChatsExpanded(!isChatsExpanded)}
              className={`group flex items-center justify-between w-full px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
                location.pathname.startsWith('/chat')
                  ? 'bg-purple-50 text-purple-700'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center">
                <span className="mr-3 w-6 h-6">
                  <ChatIcon />
                </span>
                Chat
              </div>
              <svg
                className={`w-4 h-4 transition-transform duration-200 ${
                  isChatsExpanded ? 'rotate-90' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>

            {/* Chat List - Expanded */}
            {isChatsExpanded && (
              <div className="pl-3 space-y-1 overflow-hidden">
                {isLoadingChats ? (
                  <div className="flex items-center px-3 py-2 text-xs text-gray-500">
                    <svg className="animate-spin w-3 h-3 mr-2" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Loading chats...
                  </div>
                ) : (
                  <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-10rem)]">
                    <Link
                      to="/chat/new"
                      className={`block px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
                        location.pathname === '/chat/new'
                          ? 'bg-purple-50 text-purple-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      + New Chat
                    </Link>
                    {chats.map(chat => (
                      <div
                        key={chat.chat_id}
                        className="group relative"
                      >
                        <Link
                          to={`/chat/${chat.chat_id}`}
                          className={`block px-3 py-2 pr-8 text-[14px] rounded-se transition-colors duration-200 ${
                            location.pathname === `/chat/${chat.chat_id}`
                              ? 'bg-purple-50 text-purple-700 border-l-2 font-medium border-purple-700'
                              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 border-l-2 border-transparent'
                          }`}
                        >
                          <div className="truncate" title={chat.query}>
                            {chat.query || `Chat ${chat.chat_id}`}
                          </div>
                          {chat.timestamp && (
                            <div className="text-xs text-gray-400 mt-1">
                              {new Date(chat.timestamp).toLocaleDateString()}
                            </div>
                          )}
                        </Link>
                        <button
                          onClick={(e) => chat.chat_id && handleDeleteChat(chat.chat_id, e)}
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-600"
                          title="Delete chat"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>
      <div className="p-4">
        <Link
          key="Settings"
          to={'/settings'}
          className={`group flex items-center px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
            location.pathname === '/settings'
              ? 'bg-purple-50 text-purple-700'
              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
          }`}
        >
          <span className="mr-3 w-6 h-6">
            <SettingsIcon />
          </span>
          Settings
        </Link>
      </div>
    </div>
  );
};

export default Sidebar;
