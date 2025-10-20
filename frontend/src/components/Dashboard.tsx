import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { chatAPI } from '../services/api';
import { chatHistoryAPI } from '../services/chatHistoryAPI';
import Button from './common/Button';
import ChatMessage from './chat/ChatMessage';
import ChatHistorySidebar from './chat/ChatHistorySidebar';
import UserProfile from './profile/UserProfile';
import CartWidget from './CartWidget';
import { API_CONFIG } from '../config/api';
import './Dashboard.css';

interface ChatMessageType {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sessionId?: string;
  step?: string;
  requiresConfirmation?: boolean;
  confirmationPrompt?: string;
  requiresInput?: boolean;
  input_prompt?: string;
  input_type?: string;
  input_options?: string[];
  data?: any;
}

interface ProfileStatus {
  is_setup_complete: boolean;
  missing_sections: string[];
  profile_data: any;
}

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [showProfile, setShowProfile] = useState(false);
  const [profileStatus, setProfileStatus] = useState<ProfileStatus | null>(null);
  const [showProfileSetup, setShowProfileSetup] = useState(false);
  const [currentSessionTitle, setCurrentSessionTitle] = useState<string>('New Chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [showCartWidget, setShowCartWidget] = useState(true);

  // Debug: Check authentication status
  useEffect(() => {
    console.log('Current user:', user);
    console.log('Auth token:', localStorage.getItem('access_token'));
  }, [user]);

  // Load chat history but don't auto-select any session
  const loadInitialChatHistory = async () => {
    try {
      console.log('Loading initial chat history...');
      const response = await chatHistoryAPI.getChatSessions();
      console.log(`Found ${response.sessions.length} existing sessions`);

      // Don't auto-load any session - let user choose or start new chat
      console.log('Chat history loaded but not auto-selecting any session - user will start fresh or choose from sidebar');

    } catch (error) {
      console.error('Failed to load chat history:', error);
      // Log more details for debugging
      if (error instanceof Error) {
        console.error('Error details:', error.message);
      }
    }
  };

  // Check profile setup status and load chat history
  useEffect(() => {
    if (user) {
      console.log('User available:', user);
      console.log('Auth token:', localStorage.getItem('access_token'));
      console.log('User available, checking profile and loading chat history');
      checkProfileStatus();
      // Always start with a fresh chat - don't auto-load any previous session
      loadInitialChatHistory();
    } else {
      console.log('No user available yet');
    }
  }, [user]);

  const checkProfileStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const response = await fetch(`${API_CONFIG.BASE_URL}/profile-setup/status`, {
        headers
      });

      if (response.ok) {
        const status = await response.json();
        setProfileStatus(status);

        // If profile is not complete, show setup notification
        if (!status.is_setup_complete) {
          setShowProfileSetup(true);
        }
      }
    } catch (error) {
      console.error('Error checking profile status:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Chat history handlers
  const handleSessionSelect = (sessionId: string, sessionMessages: any[], sessionTitle?: string) => {
    console.log(`Loading session: ${sessionId} with ${sessionMessages.length} messages`);
    setCurrentSessionId(sessionId);
    setMessages(sessionMessages);
    setCurrentSessionTitle(sessionTitle || 'Chat Session');
  };

  const handleNewChat = () => {
    console.log('Starting new chat - clearing all state');
    setCurrentSessionId(null);
    setMessages([]);
    setInputMessage('');
    setCurrentSessionTitle('New Chat');

    // Clear any loading states
    setLoading(false);

    // Note: The new DynamoDB session will be created when the user sends the first message
    // This ensures consistency between the chat system and chat history
    console.log('New chat initialized - ready for user input');
  };

  // Add a ref to trigger sidebar refresh
  const sidebarRefreshTrigger = () => {
    console.log('Triggering sidebar refresh...');
    // Trigger refresh in the sidebar component
    window.dispatchEvent(new CustomEvent('refreshChatHistory'));
  };

  // Only trigger sidebar refresh for new sessions (don't reload messages)
  const triggerDelayedRefresh = (sessionId: string) => {
    console.log(`Setting up delayed sidebar refresh for session: ${sessionId}`);
    setTimeout(() => {
      // Only refresh the sidebar to show the new session, don't reload messages
      sidebarRefreshTrigger();
      console.log(`Sidebar refreshed for new session: ${sessionId}`);
    }, 2000); // Reduced to 2 seconds
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessageContent = inputMessage;
    setInputMessage('');

    // Immediately add the user's message to the UI
    const userMessage: ChatMessageType = {
      id: Date.now().toString(),
      type: 'user',
      content: userMessageContent,
      timestamp: new Date(),
    };
    setMessages(prev => {
      const lastMessage = prev.length > 0 ? prev[prev.length - 1] : null;
      if (lastMessage && lastMessage.id === userMessage.id) {
        return prev;
      }
      return [...prev, userMessage];
    });

    setLoading(true);
    try {
      let response;
      const lowerMessage = userMessageContent.toLowerCase().trim();
      const lastMessage = messages[messages.length - 1];
      const currentStep = lastMessage?.step;

      if (lastMessage?.requiresConfirmation && (lowerMessage === 'yes' || lowerMessage === 'y' || lowerMessage === 'no' || lowerMessage === 'n')) {
        const confirmed = lowerMessage === 'yes' || lowerMessage === 'y';
        if (currentStep === 'feedback_purchase') {
          response = await chatAPI.submitPurchaseIntent(currentSessionId!, confirmed);
        } else if (currentStep === 'final_cart_ready') {
          response = await chatAPI.collectDetailedFeedback(currentSessionId!, confirmed);
        } else {
          response = await chatAPI.confirmStep(currentSessionId!, confirmed);
        }
      } else if (lastMessage?.requiresInput && currentStep?.startsWith('feedback_')) {
        if (currentStep === 'feedback_rating') {
          const rating = parseInt(userMessageContent, 10);
          if (!isNaN(rating) && rating >= 1 && rating <= 5) {
            response = await chatAPI.submitFeedbackRating(currentSessionId!, rating);
          } else {
            // Create a local error message without calling the backend
            response = {
              ...(lastMessage || {}),
              content: "Please provide a valid rating between 1 and 5.",
              assistant_message: "Please provide a valid rating between 1 and 5.",
              requiresInput: true,
            };
          }
        } else if (currentStep === 'feedback_liked_items') {
          const likedItems = lowerMessage === 'none' ? [] : userMessageContent.split(',').map(item => item.trim());
          response = await chatAPI.submitLikedItems(currentSessionId!, likedItems);
        } else if (currentStep === 'feedback_disliked_items') {
          const dislikedItems = lowerMessage === 'none' ? [] : userMessageContent.split(',').map(item => item.trim());
          response = await chatAPI.submitDislikedItems(currentSessionId!, dislikedItems);
        } else if (currentStep === 'feedback_suggestions') {
          response = await chatAPI.submitSuggestions(currentSessionId!, userMessageContent);
        }
      } else {
        response = await chatAPI.sendMessage(userMessageContent, currentSessionId || undefined);
      }

      if (response) {
        if (!currentSessionId && response.session_id) {
          setCurrentSessionId(response.session_id);
          const newTitle = userMessageContent.substring(0, 50) + (userMessageContent.length > 50 ? '...' : '');
          setCurrentSessionTitle(newTitle);
          triggerDelayedRefresh(response.session_id);
        }

        const assistantMessage: ChatMessageType = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: response.assistant_message || response.message || 'Processing your request...',
          timestamp: new Date(),
          sessionId: response.session_id,
          step: response.step,
          requiresConfirmation: response.requires_confirmation,
          confirmationPrompt: response.confirmation_prompt,
          requiresInput: response.requires_input,
          input_prompt: response.input_prompt,
          input_type: response.input_type,
          input_options: response.input_options,
          data: response.data,
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error: any) {
      console.error('Error:', error);
      const errorMessage: ChatMessageType = {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmation = async (confirmed: boolean) => {
    if (!currentSessionId) return;

    setLoading(true);
    try {
      // Get the current step from the last message
      const lastMessage = messages[messages.length - 1];
      const currentStep = lastMessage?.step;

      console.log('Debug - Current step:', currentStep);
      console.log('Debug - Last message:', lastMessage);

      let response;

      // Use confirmStep for all confirmation operations
      if (currentStep === 'casual_response') {
        // For general query search confirmation from casual response
        response = await chatAPI.confirmStep(currentSessionId, confirmed);
      } else if (currentStep === 'general_query_search') {
        // For general query search confirmation
        response = await chatAPI.confirmStep(currentSessionId, confirmed);
      } else if (currentStep === 'feedback_purchase') {
        // For purchase intent confirmation
        response = await chatAPI.submitPurchaseIntent(currentSessionId, confirmed);
      } else {
        // For all other confirmations (intent, goal, recipes_ready, cart_ready, etc.)
        response = await chatAPI.confirmStep(currentSessionId, confirmed);
      }

      const assistantMessage: ChatMessageType = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.assistant_message || response.message || 'Processing your request...',
        timestamp: new Date(),
        sessionId: response.session_id,
        step: response.step,
        requiresConfirmation: response.requires_confirmation,
        confirmationPrompt: response.confirmation_prompt,
        data: response.data,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If the session is complete, show a completion message
      if (response.is_complete) {
        console.log("Session completed successfully!");
      }
    } catch (error: any) {
      console.error('Confirmation error:', error);
      const errorMessage: ChatMessageType = {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputSubmit = async (input: string | number | boolean) => {
    if (!currentSessionId) return;

    setLoading(true);
    try {
      // Get the current step from the last message
      const lastMessage = messages[messages.length - 1];
      const currentStep = lastMessage?.step;

      let response;

      // Call different endpoints based on the current step
      if (currentStep === 'feedback_rating') {
        // Handle rating submission
        response = await chatAPI.submitFeedbackRating(currentSessionId, input as number);
      } else if (currentStep === 'feedback_liked_items') {
        // Handle liked items submission - parse string into array
        const likedItems = (input as string).toLowerCase() === 'none' ? [] : (input as string).split(',').map(item => item.trim());
        response = await chatAPI.submitLikedItems(currentSessionId, likedItems);
      } else if (currentStep === 'feedback_disliked_items') {
        // Handle disliked items submission - parse string into array
        const dislikedItems = (input as string).toLowerCase() === 'none' ? [] : (input as string).split(',').map(item => item.trim());
        response = await chatAPI.submitDislikedItems(currentSessionId, dislikedItems);
      } else if (currentStep === 'feedback_suggestions') {
        // Handle suggestions submission
        response = await chatAPI.submitSuggestions(currentSessionId, input as string);
      } else {
        // Default to general input handling
        response = await chatAPI.confirmStep(currentSessionId, true);
      }

      const assistantMessage: ChatMessageType = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.assistant_message || response.message || 'Processing your input...',
        timestamp: new Date(),
        sessionId: response.session_id,
        step: response.step,
        requiresConfirmation: response.requires_confirmation,
        confirmationPrompt: response.confirmation_prompt,
        requiresInput: response.requires_input,
        input_prompt: response.input_prompt,
        input_type: response.input_type,
        input_options: response.input_options,
        data: response.data,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If the session is complete, show a completion message
      if (response.is_complete) {
        console.log("Session completed successfully!");
      }
    } catch (error: any) {
      console.error('Input submission error:', error);
      const errorMessage: ChatMessageType = {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleCartAction = async (action: string) => {
    if (!currentSessionId) return;

    setLoading(true);
    try {
      console.log(`🛒 Cart action triggered: ${action}`);

      if (action === "View Product Catalog") {
        // Handle product catalog view - navigate to landing page
        console.log('🛍️ Opening product catalog...');
        navigate('/');
        setLoading(false);
        return;
      }

      // Create a confirmation request with the cart action
      const confirmationData = {
        choice: action
      };

      const response = await chatAPI.confirmStep(currentSessionId, true, confirmationData);

      // Only add message if it's not empty and not a loop
      if (response.assistant_message && response.assistant_message.trim() !== '') {
        const assistantMessage: ChatMessageType = {
          id: Date.now().toString(),
          type: 'assistant',
          content: response.assistant_message,
          timestamp: new Date(),
          sessionId: response.session_id,
          step: response.step,
          requiresConfirmation: response.requires_confirmation,
          confirmationPrompt: response.confirmation_prompt,
          requiresInput: response.requires_input,
          input_prompt: response.input_prompt,
          input_type: response.input_type,
          input_options: response.input_options,
          data: response.data,
        };

        setMessages(prev => [...prev, assistantMessage]);
      }

      // If the session is complete, show a completion message
      if (response.is_complete) {
        console.log("Cart action completed successfully!");
      }
    } catch (error: any) {
      console.error('Cart action error:', error);
      const errorMessage: ChatMessageType = {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your cart action. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product: any) => {
    try {
      console.log(`🛒 Adding product to cart: ${product.name}`);

      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const response = await fetch(`${API_CONFIG.BASE_URL}/cart/add`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          items: [{
            item_id: product.item_id,
            name: product.name,
            price: product.price,
            quantity: 1
          }]
        })
      });

      const data = await response.json();

      if (data.success) {
        console.log('✅ Product added to cart successfully');
        // Show success message
        const successMessage: ChatMessageType = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `✅ Added "${product.name}" to your cart!`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, successMessage]);
      } else {
        console.error('❌ Failed to add product to cart:', data.message);
        const errorMessage: ChatMessageType = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `❌ Failed to add "${product.name}" to cart: ${data.message}`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('❌ Error adding product to cart:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    console.log('Clearing chat - same as new chat');
    handleNewChat();
  };

  const toggleRightSidebar = () => {
    setRightSidebarOpen(!rightSidebarOpen);
  };

  // Handle clicking outside quick actions dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (rightSidebarOpen && !target.closest('.quick-actions-dropdown') && !target.closest('.dashboard-buttons')) {
        setRightSidebarOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [rightSidebarOpen]);

  return (
    <div className="full-page-layout">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>MealCart Shopping Assistant</h1>
        </div>
        <div className="dashboard-buttons">

          <Button variant="secondary" size="sm" onClick={() => navigate('/')}>
            View Catalog

          </Button>
          <Button variant="secondary" size="sm" onClick={() => setShowProfile(!showProfile)}>
            Profile
          </Button>
          <Button variant="primary" size="sm" onClick={() => navigate('/profile-setup?mode=update')}>
            Update Profile
          </Button>
          <Button variant="secondary" size="sm" onClick={clearChat}>
            Clear Chat
          </Button>
          <Button variant="primary" size="sm" onClick={toggleRightSidebar}>
            {rightSidebarOpen ? 'Close' : 'Quick Actions'}
          </Button>
          <Button variant="danger" size="sm" onClick={logout}>
            Logout
          </Button>
        </div>
      </div>

      {/* Optional Profile Warning */}
      {showProfileSetup && (
        <div className="mb-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-yellow-800 font-semibold text-sm mb-1">Profile Setup Required</h3>
                <p className="text-sm text-yellow-700">
                  To get personalized recommendations, please complete your profile setup first.
                  {profileStatus?.missing_sections && (
                    <span> Missing: {profileStatus.missing_sections.join(', ')}</span>
                  )}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/profile-setup?mode=update')}
                  className="bg-yellow-600 text-white px-3 py-1 rounded-md text-sm"
                >
                  Complete Setup
                </button>
                <button
                  onClick={() => setShowProfileSetup(false)}
                  className="text-yellow-700 text-sm"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="dashboard-body">
        {/* Left Sidebar - Chat History */}
        <div className={`left-sidebar ${leftSidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <h3>Chat History</h3>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
              className="hide-history-btn"
            >
              {leftSidebarOpen ? 'Hide' : 'Show'} History
            </Button>
          </div>

          <div className="chat-history-container">
            <ChatHistorySidebar
              currentSessionId={currentSessionId}
              onSessionSelect={handleSessionSelect}
              onNewChat={handleNewChat}
            />
          </div>
        </div>

        {/* Main Chat Area */}
        <div className={`chat-wrapper ${leftSidebarOpen ? 'left-sidebar-open' : ''} ${rightSidebarOpen ? 'right-sidebar-open' : ''}`}>
          {/* Floating Show History Button - Only visible when sidebar is closed */}
          {!leftSidebarOpen && (
            <div className="floating-show-history-btn">
              <Button
                variant="primary"
                size="sm"
                onClick={() => setLeftSidebarOpen(true)}
                className="show-history-btn"
              >
                Show History
              </Button>
            </div>
          )}

          {/* Quick Actions Dropdown */}
          {rightSidebarOpen && (
            <div className="quick-actions-dropdown">
              <div className="quick-actions-header">
                <h3>Quick Actions</h3>
                <button
                  className="close-quick-actions-btn"
                  onClick={toggleRightSidebar}
                >
                  ×
                </button>
              </div>

              <div className="quick-actions-content">
                <div className="quick-action-group">
                  <h4>Meal Planning</h4>
                  <div className="action-buttons">
                    <button onClick={() => { setInputMessage("Plan 3 meals under $50"); toggleRightSidebar(); }}>
                      Budget Meals
                    </button>
                    <button onClick={() => { setInputMessage("Plan healthy meals for the week"); toggleRightSidebar(); }}>
                      Healthy Meals
                    </button>
                    <button onClick={() => { setInputMessage("Plan vegetarian meals"); toggleRightSidebar(); }}>
                      Vegetarian
                    </button>
                  </div>
                </div>

                <div className="quick-action-group">
                  <h4>Product Recommendations</h4>
                  <div className="action-buttons">
                    <button onClick={() => { setInputMessage("Suggest gluten-free products"); toggleRightSidebar(); }}>
                      Gluten-Free
                    </button>
                    <button onClick={() => { setInputMessage("Suggest low-carb snacks"); toggleRightSidebar(); }}>
                      Low-Carb
                    </button>
                    <button onClick={() => { setInputMessage("Suggest organic products"); toggleRightSidebar(); }}>
                      Organic
                    </button>
                  </div>
                </div>

                <div className="quick-action-group">
                  <h4>Product Availability</h4>
                  <div className="action-buttons">
                    <button onClick={() => { setInputMessage("Do you have organic milk?"); toggleRightSidebar(); }}>
                      Check Stock
                    </button>
                    <button onClick={() => { setInputMessage("What are your store hours?"); toggleRightSidebar(); }}>
                      Store Hours
                    </button>
                    <button onClick={() => { setInputMessage("Find nearest store"); toggleRightSidebar(); }}>
                      Find Store
                    </button>
                  </div>
                </div>

                <div className="quick-action-group">
                  <h4>Shopping Help</h4>
                  <div className="action-buttons">
                    <button onClick={() => { setInputMessage("Create a shopping list"); toggleRightSidebar(); }}>
                      Shopping List
                    </button>
                    <button onClick={() => { setInputMessage("Find deals and promotions"); toggleRightSidebar(); }}>
                      Deals & Promos
                    </button>
                    <button onClick={() => { setInputMessage("Track my order"); toggleRightSidebar(); }}>
                      Track Order
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Chat Messages */}
          <div className="chat-scroll-area">
            {messages.length === 0 ? (
              <div className="empty-message">
                <div className="text-6xl mb-4">Start a conversation!</div>
                <p className="text-lg font-medium mb-2">Welcome to MealCart Shopping Assistant</p>
                <p className="text-sm">Try: "Plan 3 meals under $50" or "Suggest gluten-free products"</p>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onConfirm={handleConfirmation}
                  onInputSubmit={handleInputSubmit}
                  onCartAction={handleCartAction}
                />
              ))
            )}

            {loading && <div className="thinking">AI is thinking...</div>}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="chat-input-bar">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={loading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || loading}
              loading={loading}
            >
              {loading ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </div>

        {/* Profile Modal */}
        {showProfile && (
          <div className="profile-modal">
            <UserProfile onClose={() => setShowProfile(false)} />
          </div>
        )}

        {/* Floating Cart Widget */}
        <CartWidget
          isVisible={showCartWidget}
          onToggle={() => setShowCartWidget(!showCartWidget)}
        />
      </div>
    </div>
  );
};

export default Dashboard; 