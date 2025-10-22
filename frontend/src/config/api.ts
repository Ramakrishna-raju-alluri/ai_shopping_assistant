// API Configuration
// This file centralizes all API-related configuration

export const API_CONFIG = {
  // Base URL for all API calls - automatically switches based on environment
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8100/api/v1',
  
  // Timeout for API requests (in milliseconds)
  TIMEOUT: 360000,
  
  // Default headers for API requests
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },
} as const;

// Helper function to get the full API URL for an endpoint
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_CONFIG.BASE_URL}/${cleanEndpoint}`;
};

// Helper function to get API URL without the /api/v1 prefix (for root endpoints)
export const getApiBaseUrl = (): string => {
  return API_CONFIG.BASE_URL.replace('/api/v1', '');
};

// Environment detection
export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NODE_ENV === 'production';

// Log the current API configuration in development
if (isDevelopment) {
  console.log('🔧 API Configuration:', {
    baseUrl: API_CONFIG.BASE_URL,
    environment: process.env.NODE_ENV,
  });
}