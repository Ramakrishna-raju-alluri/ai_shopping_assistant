import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8100/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  signup: async (username: string, password: string, name: string, email: string) => {
    const response = await api.post('/auth/signup', {
      username,
      password,
      name,
      email,
    });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },
};

export const chatAPI = {
  sendMessage: async (message: string, sessionId?: string) => {
    const payload: any = { message };
    if (sessionId) {
      payload.session_id = sessionId;
    }
    const response = await api.post('/chat', payload);
    return response.data;
  },

  confirmStep: async (sessionId: string, confirmed: boolean, feedbackData?: any) => {
    const payload: any = {
      session_id: sessionId,
      confirmed,
    };
    
    if (feedbackData) {
      payload.feedback_data = feedbackData;
    }
    
    const response = await api.post('/confirm', payload);
    return response.data;
  },

  // New detailed feedback collection endpoints
  collectDetailedFeedback: async (sessionId: string, confirmed: boolean) => {
    const response = await api.post('/collect-feedback', {
      session_id: sessionId,
      confirmed,
    });
    return response.data;
  },

  submitFeedbackRating: async (sessionId: string, rating: number) => {
    const response = await api.post('/feedback-rating', {
      session_id: sessionId,
      overall_satisfaction: rating,
    });
    return response.data;
  },

  submitLikedItems: async (sessionId: string, likedItems: string[]) => {
    const response = await api.post('/feedback-liked', {
      session_id: sessionId,
      liked_items: likedItems,
    });
    return response.data;
  },

  submitDislikedItems: async (sessionId: string, dislikedItems: string[]) => {
    const response = await api.post('/feedback-disliked', {
      session_id: sessionId,
      disliked_items: dislikedItems,
    });
    return response.data;
  },

  submitSuggestions: async (sessionId: string, suggestions: string) => {
    const response = await api.post('/feedback-suggestions', {
      session_id: sessionId,
      suggestions,
    });
    return response.data;
  },

  submitPurchaseIntent: async (sessionId: string, willPurchase: boolean) => {
    const response = await api.post('/feedback-purchase', {
      session_id: sessionId,
      will_purchase: willPurchase,
    });
    return response.data;
  },
}; 