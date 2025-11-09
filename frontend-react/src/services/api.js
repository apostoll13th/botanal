import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let authToken = null;

export const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};

export const clearAuthToken = () => {
  authToken = null;
  delete api.defaults.headers.common.Authorization;
};

export const login = async (login, password) => {
  const response = await api.post('/auth/login', { login, password });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/me');
  return response.data;
};

export const getUserProfile = async () => {
  const response = await api.get('/user');
  return response.data;
};

export const getExpenses = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  if (filters.category) params.append('category', filters.category);
  if (filters.type) params.append('type', filters.type);

  const query = params.toString();
  const response = await api.get(`/expenses${query ? `?${query}` : ''}`);
  return response.data;
};

export const getExpensesSummary = async () => {
  const response = await api.get('/expenses-summary');
  return response.data;
};

export const getBudgets = async () => {
  const response = await api.get('/budgets');
  return response.data;
};

export const getSavingsGoals = async () => {
  const response = await api.get('/goals');
  return response.data;
};

export const createTransaction = async (payload) => {
  const response = await api.post('/expenses', payload);
  return response.data;
};

export const listCategories = async () => {
  const response = await api.get('/categories');
  return response.data;
};

export const createCategory = async (payload) => {
  const response = await api.post('/categories', payload);
  return response.data;
};

export default api;
