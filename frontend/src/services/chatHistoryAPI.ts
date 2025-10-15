import axios from 'axios';

const API_BASE_URL = 'http://localhost:8100/api/v1';

// Types
export interface ChatSession {
  session_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  step?: string;
  requires_confirmation?: boolean;
  confirmation_prompt?: string;
  requires_input?: boolean;
  input_prompt?: string;
  input_type?: string;
  input_options?: string[];
  data?: any;
}

export interface ChatSessionDetail {
  session_id: string;
  title: string;
  messages: ChatMessage[];
  message_count: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ChatHistoryListResponse {
  sessions: ChatSession[];
  total_count: number;
}

// Axios instance with authentication
const chatHistoryAxios = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
});

// Add auth token to requests
chatHistoryAxios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
chatHistoryAxios.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    console.error('Chat History API Error:', error.response?.data || error.message);
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Chat History API methods
export const chatHistoryAPI = {
  /**
   * Create a new chat session
   */
  async createChatSession(title?: string): Promise<ChatSession> {
    try {
      const request = title ? { title } : {};
      const response = await chatHistoryAxios.post('/chat-history/sessions', request);
      console.log('✅ Created new chat session:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error creating chat session:', error);
      throw new Error('Failed to create new chat session');
    }
  },

  /**
   * Get all chat sessions for the current user
   */
  async getChatSessions(): Promise<ChatHistoryListResponse> {
    try {
      const response = await chatHistoryAxios.get('/chat-history/sessions');
      console.log(`📚 Retrieved ${response.data.total_count} chat sessions`);
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching chat sessions:', error);
      throw new Error('Failed to load chat sessions');
    }
  },

  /**
   * Get a specific chat session with all messages
   */
  async getChatSession(sessionId: string): Promise<ChatSessionDetail> {
    try {
      const response = await chatHistoryAxios.get(`/chat-history/sessions/${sessionId}`);
      console.log(`📖 Retrieved chat session: ${sessionId} with ${response.data.message_count} messages`);
      return response.data;
    } catch (error) {
      console.error(`❌ Error fetching chat session ${sessionId}:`, error);
      throw new Error('Failed to load chat session');
    }
  },

  /**
   * Delete a chat session
   */
  async deleteChatSession(sessionId: string): Promise<void> {
    try {
      await chatHistoryAxios.delete(`/chat-history/sessions/${sessionId}`);
      console.log(`🗑️ Deleted chat session: ${sessionId}`);
    } catch (error) {
      console.error(`❌ Error deleting chat session ${sessionId}:`, error);
      throw new Error('Failed to delete chat session');
    }
  }
};

export default chatHistoryAPI; 