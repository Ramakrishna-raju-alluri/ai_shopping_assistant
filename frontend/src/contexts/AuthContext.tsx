import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';

interface User {
  user_id: string;
  username: string;
  name?: string;
  email?: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, password: string, name: string, email: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isNewUser: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        setUser(user);
        setIsNewUser(false); // Existing user
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await authAPI.login(username, password);
      const { access_token, user_id, name, email } = response;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify({ user_id, username, name, email }));
      
      setUser({ user_id, username, name, email });
      setIsNewUser(false); // Existing user logging in
    } catch (error: any) {
      // Enhanced error handling to prevent [object Object]
      let errorMessage = 'Login failed';
      
      if (error.response?.data?.error) {
        // Business logic errors (400)
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Validation errors (422) - array format
          errorMessage = error.response.data.detail.map((err: any) => err.msg).join(', ');
        } else {
          // Single detail error
          errorMessage = error.response.data.detail;
        }
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (typeof error.message === 'string') {
        errorMessage = error.message;
      } else if (error.response?.status === 401) {
        errorMessage = 'Invalid username or password. Please try again.';
      } else if (error.response?.status === 422) {
        errorMessage = 'Invalid input data. Please check your information.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
      }
      
      throw new Error(errorMessage);
    }
  };

  const signup = async (username: string, password: string, name: string, email: string) => {
    try {
      const response = await authAPI.signup(username, password, name, email);
      const { access_token, user_id, email: userEmail } = response;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify({ user_id, username, name, email: userEmail }));
      
      setUser({ user_id, username, name, email: userEmail });
      setIsNewUser(true); // New user just signed up
    } catch (error: any) {
      // Enhanced error handling to prevent [object Object]
      let errorMessage = 'Signup failed';
      
      if (error.response?.data?.error) {
        // Business logic errors (400)
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Validation errors (422) - array format
          errorMessage = error.response.data.detail.map((err: any) => err.msg).join(', ');
        } else {
          // Single detail error
          errorMessage = error.response.data.detail;
        }
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (typeof error.message === 'string') {
        errorMessage = error.message;
      } else if (error.response?.status === 400) {
        errorMessage = 'Username or email already exists. Please try a different one.';
      } else if (error.response?.status === 422) {
        errorMessage = 'Invalid input data. Please check your information.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
      }
      
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsNewUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading, isNewUser }}>
      {children}
    </AuthContext.Provider>
  );
}; 