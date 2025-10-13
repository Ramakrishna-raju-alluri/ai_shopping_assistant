import React, { useState, useEffect } from 'react';
import { chatHistoryAPI } from '../../services/chatHistoryAPI';
import './ChatHistorySidebar.css';

interface ChatSession {
  session_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface ChatHistorySidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string, messages: any[], sessionTitle?: string) => void;
  onNewChat: () => void;
}

const ChatHistorySidebar: React.FC<ChatHistorySidebarProps> = ({
  currentSessionId,
  onSessionSelect,
  onNewChat
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadChatSessions();
    
    // Listen for refresh events from Dashboard
    const handleRefresh = () => {
      console.log('📚 Refreshing chat history from event trigger');
      loadChatSessions();
    };
    
    window.addEventListener('refreshChatHistory', handleRefresh);
    
    // Cleanup
    return () => {
      window.removeEventListener('refreshChatHistory', handleRefresh);
    };
  }, []);

  const loadChatSessions = async () => {
    try {
      console.log('🔄 Loading chat sessions from API...');
      setLoading(true);
      setError(null);
      
      const response = await chatHistoryAPI.getChatSessions();
      console.log('📚 API Response:', response);
      
      if (response && response.sessions) {
        setSessions(response.sessions);
        console.log(`✅ Loaded ${response.sessions.length} chat sessions:`, response.sessions);
      } else {
        console.log('⚠️ Invalid response format:', response);
        setSessions([]);
      }
      
    } catch (err) {
      console.error('❌ Error loading chat sessions:', err);
      if (err instanceof Error) {
        console.error('Error details:', err.message);
        setError(`Failed to load chat history: ${err.message}`);
      } else {
        setError('Failed to load chat history');
      }
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionClick = async (sessionId: string) => {
    try {
      setLoading(true);
      console.log(`📋 Loading session from sidebar: ${sessionId}`);
      
      // Get full session details including messages
      const sessionDetails = await chatHistoryAPI.getChatSession(sessionId);
      console.log(`📋 Sidebar session details:`, sessionDetails);
      console.log(`📋 Sidebar raw messages:`, sessionDetails.messages);
      
      // Convert DynamoDB messages to frontend format
      const formattedMessages = sessionDetails.messages.map((msg: any) => {
        console.log(`📋 Sidebar processing message:`, msg);
        
        // Ensure message type is properly preserved as string
        const messageType = String(msg.type || 'user').toLowerCase();
        if (messageType !== 'user' && messageType !== 'assistant') {
          console.warn(`⚠️ Sidebar: Invalid message type "${messageType}", defaulting to "user"`);
        }
        
        // For assistant messages, prioritize assistant_message field, then fall back to content
        let messageContent = String(msg.content || '');
        if (messageType === 'assistant') {
          if (msg.assistant_message) {
            messageContent = String(msg.assistant_message);
            console.log(`📋 Sidebar: Using assistant_message: "${messageContent.substring(0, 50)}..."`);
          } else {
            console.log(`📋 Sidebar: No assistant_message found, using content: "${messageContent.substring(0, 50)}..."`);
          }
        }
        
        const formatted = {
          id: msg.id || Math.random().toString(36),
          type: (messageType === 'assistant' || messageType === 'user') ? messageType as 'user' | 'assistant' : 'user',
          content: messageContent,
          timestamp: new Date(msg.timestamp),
          sessionId: sessionId,
          step: msg.step,
          requiresConfirmation: Boolean(msg.requires_confirmation),
          confirmationPrompt: msg.confirmation_prompt,
          requiresInput: Boolean(msg.requires_input),
          input_prompt: msg.input_prompt,
          input_type: msg.input_type,
          input_options: msg.input_options,
          data: msg.data
        };
        
        console.log(`📋 Sidebar formatted message:`, formatted);
        console.log(`📋 Sidebar message type: "${formatted.type}" (should be "user" or "assistant")`);
        return formatted;
      });
      
      console.log(`📋 Sidebar total formatted messages:`, formattedMessages.length);
      console.log(`📋 Sidebar message types:`, {
        user: formattedMessages.filter(m => m.type === 'user').length,
        assistant: formattedMessages.filter(m => m.type === 'assistant').length,
        other: formattedMessages.filter(m => m.type !== 'user' && m.type !== 'assistant').length
      });
      
      // Call parent component to update main chat
      onSessionSelect(sessionId, formattedMessages, sessionDetails.title);
      
    } catch (err) {
      console.error('❌ Error loading session:', err);
      setError('Failed to load session');
    } finally {
      setLoading(false);
    }
  };

  const handleNewChatClick = () => {
    // Clear the current session and messages in the main dashboard
    onNewChat();
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this chat?')) {
      return;
    }
    
    try {
      setLoading(true);
      
      await chatHistoryAPI.deleteChatSession(sessionId);
      
      // Reload sessions
      await loadChatSessions();
      
      // If this was the current session, start a new chat
      if (sessionId === currentSessionId) {
        onNewChat();
      }
      
      console.log(`🗑️ Deleted chat session: ${sessionId}`);
    } catch (err) {
      console.error('Error deleting session:', err);
      setError('Failed to delete chat');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return 'Today';
    } else if (diffDays === 2) {
      return 'Yesterday';
    } else if (diffDays <= 7) {
      return `${diffDays - 1} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="chat-sidebar">
      {/* Error Message */}
      {error && (
        <div className="sidebar-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
          <button 
            onClick={() => setError(null)}
            className="error-dismiss"
          >
            ✕
          </button>
        </div>
      )}

      {/* Sessions List */}
      <div className="sessions-list">
        {loading && sessions.length === 0 && (
          <div className="sessions-loading">
            <div className="loading-spinner"></div>
            <span>Loading chat history...</span>
          </div>
        )}

        {/* New Chat Item - Always at the top */}
        <div
          className={`session-item new-chat-item ${!currentSessionId ? 'active' : ''}`}
          onClick={handleNewChatClick}
        >
          <div className="session-content">
            <div className="session-header">
              <div className="session-title new-chat-title">
                ➕ New Chat
              </div>
            </div>
            <div className="session-meta">
              <span className="message-count">
                Start fresh conversation
              </span>
            </div>
          </div>
        </div>

        {/* Existing Sessions */}
        {!loading && sessions.length === 0 && (
          <div className="sessions-empty">
            <div className="empty-icon">💬</div>
            <div className="empty-title">No chat history yet</div>
            <div className="empty-subtitle">Click "New Chat" above to start!</div>
          </div>
        )}

        {sessions.map((session) => (
          <div
            key={session.session_id}
            className={`session-item ${session.session_id === currentSessionId ? 'active' : ''}`}
            onClick={() => handleSessionClick(session.session_id)}
          >
            <div className="session-content">
              <div className="session-header">
                <div className="session-title" title={session.title}>
                  {session.title}
                </div>
                
                <button
                  onClick={(e) => handleDeleteSession(session.session_id, e)}
                  className="session-action-btn delete-btn"
                  title="Delete chat"
                >
                  🗑️
                </button>
              </div>
              
              <div className="session-meta">
                <span className="message-count">
                  {session.message_count} messages
                </span>
                <span className="session-date">
                  {formatDate(session.updated_at)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="session-count">
          {sessions.length}/5 sessions
        </div>
        {sessions.length >= 5 && (
          <div className="session-limit-warning">
            <span className="warning-icon">⚠️</span>
            <span>Oldest chats are auto-deleted</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistorySidebar;