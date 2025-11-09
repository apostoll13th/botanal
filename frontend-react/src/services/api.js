import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getUserInfo = async (userId) => {
  const response = await api.get(`/user/${userId}`);
  return response.data;
};

export const getExpenses = async (userId, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  if (filters.category) params.append('category', filters.category);
  if (filters.type) params.append('type', filters.type);

  const response = await api.get(`/expenses/${userId}?${params.toString()}`);
  return response.data;
};

export const getExpensesSummary = async (userId) => {
  const response = await api.get(`/expenses-summary/${userId}`);
  return response.data;
};

export const getBudgets = async (userId) => {
  const response = await api.get(`/budgets/${userId}`);
  return response.data;
};

export const getSavingsGoals = async (userId) => {
  const response = await api.get(`/goals/${userId}`);
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

export const upsertUser = async (payload) => {
  const response = await api.post('/users', payload);
  return response.data;
};

export default api;
