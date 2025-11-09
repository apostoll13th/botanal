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

export default api;
