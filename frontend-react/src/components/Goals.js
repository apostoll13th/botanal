import React, { useState, useEffect } from 'react';
import { getSavingsGoals, createGoal } from '../services/api';
import './Goals.css';

const Goals = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [goals, setGoals] = useState([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: '',
    description: '',
    target_amount: '',
    current_amount: '',
    target_date: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSavingsGoals();
      setGoals(data);
    } catch (err) {
      setError('Ошибка загрузки целей: ' + err.message);
      console.error('Error loading goals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError('Введите название цели');
      return;
    }
    if (!form.target_amount || Number(form.target_amount) <= 0) {
      setError('Введите сумму цели');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await createGoal({
        name: form.name.trim(),
        description: form.description.trim(),
        target_amount: Number(form.target_amount),
        current_amount: Number(form.current_amount || 0),
        target_date: form.target_date,
      });
      setForm({
        name: '',
        description: '',
        target_amount: '',
        current_amount: '',
        target_date: '',
      });
      await loadData();
    } catch (err) {
      setError('Не удалось сохранить цель: ' + err.message);
    } finally {
      setSaving(false);
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

  return (
    <div>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>Новая цель</h3>
        <form className="category-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Название</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Например, Ремонт"
            />
          </div>
          <div className="form-row">
            <label>Описание</label>
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Необязательно"
            />
          </div>
          <div className="form-row">
            <label>Цель, ₽</label>
            <input
              type="number"
              name="target_amount"
              min="0"
              step="0.01"
              value={form.target_amount}
              onChange={handleChange}
            />
          </div>
          <div className="form-row">
            <label>Уже накоплено, ₽</label>
            <input
              type="number"
              name="current_amount"
              min="0"
              step="0.01"
              value={form.current_amount}
              onChange={handleChange}
            />
          </div>
          <div className="form-row">
            <label>Срок</label>
            <input
              type="date"
              name="target_date"
              value={form.target_date}
              onChange={handleChange}
            />
          </div>
          <div className="form-row">
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Ваши цели экономии ({goals.length})</h3>
      </div>

      {goals.length === 0 ? (
        <div className="card">
          <p>Нет созданных целей экономии.</p>
        </div>
      ) : (
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
      )}
    </div>
  );
};

export default Goals;
