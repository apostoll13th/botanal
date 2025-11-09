import React, { useState, useEffect } from 'react';
import { getBudgets, createBudget, listCategories } from '../services/api';
import './Budgets.css';

const Budgets = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    category: '',
    amount: '',
    period: 'monthly',
  });

  useEffect(() => {
    loadData();
    loadCategories();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getBudgets();
      setBudgets(data);
    } catch (err) {
      setError('Ошибка загрузки бюджетов: ' + err.message);
      console.error('Error loading budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await listCategories();
      setCategories(data.filter(cat => cat.type === 'expense'));
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.category) {
      setError('Выберите категорию');
      return;
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setError('Введите положительную сумму');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await createBudget({
        category: form.category,
        amount: Number(form.amount),
        period: form.period,
      });
      setForm({ category: '', amount: '', period: form.period });
      await loadData();
    } catch (err) {
      setError('Не удалось сохранить бюджет: ' + err.message);
    } finally {
      setSaving(false);
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

  return (
    <div>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>Новый бюджет</h3>
        <form className="category-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Категория</label>
            <select name="category" value={form.category} onChange={handleChange}>
              <option value="">Выберите категорию</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.name}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-row">
            <label>Сумма</label>
            <input
              type="number"
              name="amount"
              min="0"
              step="0.01"
              value={form.amount}
              onChange={handleChange}
            />
          </div>
          <div className="form-row">
            <label>Период</label>
            <select name="period" value={form.period} onChange={handleChange}>
              <option value="daily">День</option>
              <option value="weekly">Неделя</option>
              <option value="monthly">Месяц</option>
            </select>
          </div>
          <div className="form-row">
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Ваши бюджеты ({budgets.length})</h3>
      </div>

      {budgets.length === 0 ? (
        <div className="card">
          <p>Нет установленных бюджетов.</p>
        </div>
      ) : (
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
                  <span
                    className="value remaining"
                    style={{ color: budget.remaining >= 0 ? '#4caf50' : '#f44336' }}
                  >
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
      )}
    </div>
  );
};

export default Budgets;
