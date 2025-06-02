/**
 * API Configuration for the Document Management System
 * This file contains API endpoints and configuration options
 */

export const API_CONFIG = {
  // Base URL for API requests
  BASE_URL: 'http://localhost:8000',
  
  // API Endpoints
  ENDPOINTS: {
    DOCUMENTS: '/api/documents',
    UPLOAD: '/api/documents/upload',
    SEARCH: '/api/documents/search',
    DELETE: (id) => `/api/documents/${id}`,
    CHAT: '/api/chat',
    CHAT_STATUS: '/api/chat/status',
    CHAT_INITIALIZE: '/api/chat/initialize'
  },
  
  // Default request options
  DEFAULT_OPTIONS: {
    headers: {
      'Accept': 'application/json'
    }
  },
  
  // Request timeout in milliseconds
  TIMEOUT: 30000,
};

/**
 * Makes an API request with error handling
 * @param {string} url - The API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise} - Response data or error
 */
export const apiRequest = async (url, options = {}) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
  
  try {
    const response = await fetch(
      `${API_CONFIG.BASE_URL}${url}`, 
      {
        ...API_CONFIG.DEFAULT_OPTIONS,
        ...options,
        signal: controller.signal
      }
    );
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      // Try to get error message from response
      try {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      } catch (jsonError) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
    }
    
    // Handle empty responses
    if (response.status === 204) {
      return { success: true };
    }
    
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }
    throw error;
  }
};

export default API_CONFIG;
