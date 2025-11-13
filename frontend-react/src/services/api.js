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

export const createBudget = async (payload) => {
  const response = await api.post('/budgets', payload);
  return response.data;
};

export const getSavingsGoals = async () => {
  const response = await api.get('/goals');
  return response.data;
};

export const createGoal = async (payload) => {
  const response = await api.post('/goals', payload);
  return response.data;
};

export const createTransaction = async (payload) => {
  const response = await api.post('/expenses', payload);
  return response.data;
};

export const deleteExpense = async (id) => {
  const response = await api.delete(`/expenses/${id}`);
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

export const getAppUsers = async () => {
  const response = await api.get('/admin/users');
  return response.data;
};

export const createAppUser = async (payload) => {
  const response = await api.post('/admin/users', payload);
  return response.data;
};

export const updateAppUser = async (id, payload) => {
  const response = await api.put(`/admin/users/${id}`, payload);
  return response.data;
};

export const deleteAppUser = async (id) => {
  await api.delete(`/admin/users/${id}`);
};

// Memos API
export const getMemos = async () => {
  const response = await api.get('/memos');
  return response.data;
};

export const createMemo = async (payload) => {
  const response = await api.post('/memos', payload);
  return response.data;
};

export const updateMemo = async (id, payload) => {
  const response = await api.put(`/memos/${id}`, payload);
  return response.data;
};

export const deleteMemo = async (id) => {
  const response = await api.delete(`/memos/${id}`);
  return response.data;
};

// Wishlist API
export const getWishlist = async () => {
  const response = await api.get('/wishlist');
  return response.data;
};

export const createWishlistItem = async (payload) => {
  const response = await api.post('/wishlist', payload);
  return response.data;
};

export const updateWishlistItem = async (id, payload) => {
  const response = await api.put(`/wishlist/${id}`, payload);
  return response.data;
};

export const deleteWishlistItem = async (id) => {
  const response = await api.delete(`/wishlist/${id}`);
  return response.data;
};

export default api;
