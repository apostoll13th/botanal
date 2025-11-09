import React, { useState, useEffect } from 'react';
import { getSavingsGoals } from '../services/api';
import './Goals.css';

const Goals = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [goals, setGoals] = useState([]);

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSavingsGoals(userId);
      setGoals(data);
    } catch (err) {
      setError('Ошибка загрузки целей: ' + err.message);
      console.error('Error loading goals:', err);
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return '#4caf50';
    if (percentage >= 75) return '#8bc34a';
    if (percentage >= 50) return '#ff9800';
    return '#667eea';
  };

  if (loading) {
    return <div className="loading">Загрузка целей...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (goals.length === 0) {
    return (
      <div className="card">
        <p>Нет созданных целей экономии.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h3>Ваши цели экономии ({goals.length})</h3>
      </div>

      <div className="goals-grid">
        {goals.map((goal) => (
          <div key={goal.id} className="goal-card">
            <div className="goal-header">
              <div className="goal-icon">🎯</div>
              <div className="goal-info">
                <h4>{goal.name}</h4>
                {goal.description && goal.description !== goal.name && (
                  <p className="goal-description">{goal.description}</p>
                )}
              </div>
            </div>

            <div className="goal-amounts">
              <div className="amount-display">
                <div className="current-amount">
                  <span className="label">Накоплено</span>
                  <span className="value">{goal.current_amount.toFixed(2)} ₽</span>
                </div>
                <div className="target-amount">
                  <span className="label">Цель</span>
                  <span className="value">{goal.target_amount.toFixed(2)} ₽</span>
                </div>
              </div>

              <div className="remaining-amount">
                Осталось: <strong>{(goal.target_amount - goal.current_amount).toFixed(2)} ₽</strong>
              </div>
            </div>

            <div className="progress-section">
              <div className="progress-bar-container">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${Math.min(goal.percentage, 100)}%`,
                    backgroundColor: getProgressColor(goal.percentage),
                  }}
                >
                  {goal.percentage >= 10 && (
                    <span className="progress-text">{goal.percentage.toFixed(0)}%</span>
                  )}
                </div>
              </div>
              {goal.percentage < 10 && (
                <span className="progress-percentage" style={{ color: getProgressColor(goal.percentage) }}>
                  {goal.percentage.toFixed(1)}%
                </span>
              )}
            </div>

            {goal.target_date && (
              <div className="target-date">
                📅 Срок: {new Date(goal.target_date).toLocaleDateString('ru-RU')}
              </div>
            )}

            {goal.percentage >= 100 && (
              <div className="success-badge">
                ✅ Цель достигнута!
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Goals;
