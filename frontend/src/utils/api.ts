/**
 * ULTRA v3.0 - API Client Utilities
 * ==================================
 * 
 * Axios-based API client for all backend endpoints.
 * Implements error handling and request/response interceptors.
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type { IGlobalAPIResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Create configured Axios instance
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // 90s timeout (increased for Slow Path deep analysis)
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor for adding auth headers
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add admin key if present (for admin endpoints)
    const adminKey = localStorage.getItem('ultra_admin_key');

    if (adminKey && config.url?.includes('/admin/')) {
      // Direct property assignment works reliably with AxiosHeaders
      config.headers['X-Admin-Key'] = adminKey;
      console.log('✅ Added X-Admin-Key header for:', config.url);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor for standardized error handling
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<IGlobalAPIResponse<any>>) => {
    // Extract error message from response
    const message = error.response?.data?.message || error.message || 'Unknown error occurred';

    // Log errors for debugging (only in development)
    if (error.response?.status && error.response.status >= 400) {
      console.error('API Error:', {
        status: error.response.status,
        message,
        url: error.config?.url,
      });
    }

    return Promise.reject(error);
  }
);

export default apiClient;

/**
 * API Helper Functions
 */

export const api = {
  // Session Endpoints (View 1 & 2)
  
  async createSession() {
    const response = await apiClient.post<IGlobalAPIResponse<{ session_id: string }>>('/sessions/new');
    return response.data;
  },
  
  async getSession(sessionId: string) {
    const response = await apiClient.get(`/sessions/${sessionId}`);
    return response.data;
  },
  
  async sendMessage(payload: {
    session_id: string;
    user_input: string;
    journey_stage: string;
    language: string;
  }) {
    const response = await apiClient.post('/sessions/send', payload);
    return response.data;
  },
  
  async refineMessage(payload: {
    session_id: string;
    original_input: string;
    bad_suggestion: string;
    feedback_note: string;
    language: string;
  }) {
    const response = await apiClient.post('/sessions/refine', payload);
    return response.data;
  },
  
  async retrySlowPath(sessionId: string) {
    const response = await apiClient.post('/sessions/retry_slowpath', { session_id: sessionId });
    return response.data;
  },
  
  async endSession(sessionId: string, finalStatus: string) {
    const response = await apiClient.post('/sessions/end', {
      session_id: sessionId,
      final_status: finalStatus,
    });
    return response.data;
  },

  async sendFeedback(payload: {
    session_id: string;
    message_index: number;
    sentiment: 'positive' | 'negative';
    user_comment: string;
    context: string;
  }) {
    const response = await apiClient.post('/sessions/feedback', payload);
    return response.data;
  },

  async refineResponse(payload: {
    session_id: string;
    message_index: number;
    user_comment: string;
    language: string;
  }) {
    const response = await apiClient.post('/sessions/refine', payload);
    return response.data;
  },
  
  // Admin Endpoints (View 3)
  
  async getFeedbackGrouped(language: string) {
    const response = await apiClient.get(`/admin/feedback/grouped?language=${language}`);
    return response.data;
  },
  
  async getFeedbackDetails(note: string, language: string) {
    const response = await apiClient.get(`/admin/feedback/details?note=${encodeURIComponent(note)}&language=${language}`);
    return response.data;
  },
  
  async createGoldenStandard(payload: {
    trigger_context: string;
    golden_response: string;
    language: string;
    category: string;
  }) {
    const response = await apiClient.post('/admin/feedback/create_standard', payload);
    return response.data;
  },

  async listGoldenStandards(language: string) {
    const response = await apiClient.get(`/admin/golden-standards/list?language=${language}`);
    return response.data;
  },

  async listRAGNuggets(language: string) {
    const response = await apiClient.get(`/admin/rag/list?language=${language}`);
    return response.data;
  },
  
  async addRAGNugget(payload: {
    title: string;
    content: string;
    keywords: string;
    language: string;
  }) {
    const response = await apiClient.post('/admin/rag/add', payload);
    return response.data;
  },
  
  async deleteRAGNugget(nuggetId: string) {
    const response = await apiClient.delete(`/admin/rag/delete/${nuggetId}`);
    return response.data;
  },
  
  async getAnalyticsDashboard(params?: {
    date_from?: string;
    date_to?: string;
    language?: string;
  }) {
    const queryParams = new URLSearchParams(params as Record<string, string>).toString();
    const response = await apiClient.get(`/admin/analytics/v1_dashboard?${queryParams}`);
    return response.data;
  },
};
