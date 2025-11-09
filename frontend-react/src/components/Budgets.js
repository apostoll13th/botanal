import React, { useState, useEffect } from 'react';
import { getBudgets } from '../services/api';
import './Budgets.css';

const Budgets = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [budgets, setBudgets] = useState([]);

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getBudgets(userId);
      setBudgets(data);
    } catch (err) {
      setError('Ошибка загрузки бюджетов: ' + err.message);
      console.error('Error loading budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPeriodLabel = (period) => {
    const labels = {
      'daily': 'Ежедневно',
      'weekly': 'Еженедельно',
      'monthly': 'Ежемесячно',
    };
    return labels[period] || period;
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return '#f44336';
    if (percentage >= 80) return '#ff9800';
    return '#4caf50';
  };

  if (loading) {
    return <div className="loading">Загрузка бюджетов...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (budgets.length === 0) {
    return (
      <div className="card">
        <p>Нет установленных бюджетов.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h3>Ваши бюджеты ({budgets.length})</h3>
      </div>

      <div className="budgets-grid">
        {budgets.map((budget) => (
          <div key={budget.id} className="budget-card">
            <div className="budget-header">
              <h4>{budget.category}</h4>
              <span className="period-badge">{getPeriodLabel(budget.period)}</span>
            </div>

            <div className="budget-amounts">
              <div className="amount-item">
                <span className="label">Потрачено:</span>
                <span className="value spent">{budget.spent.toFixed(2)} ₽</span>
              </div>
              <div className="amount-item">
                <span className="label">Бюджет:</span>
                <span className="value total">{budget.amount.toFixed(2)} ₽</span>
              </div>
              <div className="amount-item">
                <span className="label">Остаток:</span>
                <span className="value remaining" style={{ color: budget.remaining >= 0 ? '#4caf50' : '#f44336' }}>
                  {budget.remaining.toFixed(2)} ₽
                </span>
              </div>
            </div>

            <div className="progress-container">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${Math.min(budget.percentage, 100)}%`,
                    backgroundColor: getProgressColor(budget.percentage),
                  }}
                />
              </div>
              <span className="percentage" style={{ color: getProgressColor(budget.percentage) }}>
                {budget.percentage.toFixed(1)}%
              </span>
            </div>

            {budget.percentage >= 80 && (
              <div className={`alert ${budget.percentage >= 100 ? 'alert-danger' : 'alert-warning'}`}>
                {budget.percentage >= 100
                  ? '⚠️ Бюджет превышен!'
                  : '⚠️ Приближаетесь к лимиту бюджета'}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Budgets;
