import React, { useState, useEffect } from 'react';
import { getExpenses } from '../services/api';
import './Expenses.css';

const Expenses = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    category: '',
  });

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExpenses(userId, filters);
      setExpenses(data);
    } catch (err) {
      setError('Ошибка загрузки расходов: ' + err.message);
      console.error('Error loading expenses:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleApplyFilters = () => {
    loadData();
  };

  const handleResetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      category: '',
    });
    setTimeout(() => loadData(), 100);
  };

  if (loading) {
    return <div className="loading">Загрузка расходов...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div>
      <div className="card">
        <h3>Фильтры</h3>
        <div className="filters">
          <div className="filter-group">
            <label>С даты:</label>
            <input
              type="date"
              name="startDate"
              value={filters.startDate}
              onChange={handleFilterChange}
            />
          </div>
          <div className="filter-group">
            <label>По дату:</label>
            <input
              type="date"
              name="endDate"
              value={filters.endDate}
              onChange={handleFilterChange}
            />
          </div>
          <div className="filter-group">
            <label>Категория:</label>
            <input
              type="text"
              name="category"
              value={filters.category}
              onChange={handleFilterChange}
              placeholder="Название категории"
            />
          </div>
          <div className="filter-buttons">
            <button className="btn btn-primary" onClick={handleApplyFilters}>
              Применить
            </button>
            <button className="btn btn-secondary" onClick={handleResetFilters}>
              Сбросить
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Расходы ({expenses.length})</h3>
        {expenses.length === 0 ? (
          <p>Нет расходов для отображения.</p>
        ) : (
          <div className="table-container">
            <table className="expenses-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Категория</th>
                  <th>Сумма</th>
                  <th>Описание</th>
                  <th>Пользователь</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr key={expense.id}>
                    <td>{new Date(expense.date).toLocaleDateString('ru-RU')}</td>
                    <td>
                      <span className="category-badge">{expense.category}</span>
                    </td>
                    <td className="amount">{expense.amount.toFixed(2)} ₽</td>
                    <td>{expense.description || '-'}</td>
                    <td>{expense.user_name || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Expenses;
