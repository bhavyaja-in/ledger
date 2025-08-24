import axios from 'axios';
import type {
  User,
  Transaction,
  TransactionListResponse,
  LoginRequest,
  TokenResponse,
  ClassifyRequest,
  SkipRequest,
  Suggestion,
  TransactionEnum,
  Category,
} from '../types';

// Configure axios defaults
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // For cookies
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      
      try {
        const refreshResponse = await api.post('/auth/refresh');
        const { access_token } = refreshResponse.data;
        localStorage.setItem('access_token', access_token);
        
        // Retry original request
        error.config.headers.Authorization = `Bearer ${access_token}`;
        return api.request(error.config);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  refreshToken: async (): Promise<TokenResponse> => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Transaction API
export const transactionApi = {
  list: async (params: {
    page?: number;
    size?: number;
    status?: string;
    search?: string;
    processor_type?: string;
  } = {}): Promise<TransactionListResponse> => {
    const response = await api.get('/transactions', { params });
    return response.data;
  },

  getNext: async (): Promise<{ id?: number; message?: string }> => {
    const response = await api.get('/transactions/next');
    return response.data;
  },

  getById: async (id: number): Promise<Transaction> => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  getSuggestions: async (id: number): Promise<Suggestion> => {
    const response = await api.get(`/transactions/${id}/suggestions`);
    return response.data;
  },

  classify: async (id: number, data: ClassifyRequest): Promise<{ message: string }> => {
    const response = await api.post(`/transactions/${id}/classify`, data);
    return response.data;
  },

  skip: async (id: number, data: SkipRequest): Promise<{ message: string }> => {
    const response = await api.post(`/transactions/${id}/skip`, data);
    return response.data;
  },

  reprocess: async (id: number): Promise<{ message: string }> => {
    const response = await api.post(`/transactions/${id}/reprocess`);
    return response.data;
  },
};

// Metadata API
export const metadataApi = {
  getEnums: async (): Promise<TransactionEnum[]> => {
    const response = await api.get('/metadata/enums');
    return response.data;
  },

  getCategories: async (): Promise<Category[]> => {
    const response = await api.get('/metadata/categories');
    return response.data;
  },
};

// Health check
export const healthApi = {
  check: async (): Promise<{ status: string; message: string; version: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;