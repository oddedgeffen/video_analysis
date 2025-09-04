import axios from 'axios';

// Determine if we're running on localhost
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// API base URL configuration
const API_BASE_URL = isLocalhost 
  ? 'http://localhost:8000/api'  // Local development
  : '/api';  // Production (render.com)

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Set CSRF token handling for Django
api.defaults.xsrfCookieName = 'csrftoken';
api.defaults.xsrfHeaderName = 'X-CSRFToken';

// Export the base URL for components that need it directly
export { API_BASE_URL };

// Helper function to get the full API URL
export const getApiUrl = (endpoint) => `${API_BASE_URL}${endpoint}`;

export const uploadDocument = async (formData) => {
  try {
    const response = await api.post('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data?.message || 'An error occurred during upload';
  }
};

export const downloadProcessedDocument = async (url) => {
  try {
    const response = await axios.get(url, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    throw 'Failed to download the processed document';
  }
}; 