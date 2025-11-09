import React, { useState, useEffect } from 'react';
import { listCategories, createCategory } from '../services/api';

const Categories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: '',
    type: 'expense',
    description: '',
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await listCategories();
      setCategories(data);
      setError('');
    } catch (err) {
      setError('Не удалось загрузить категории: ' + err.message);
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
      setError('Введите название категории');
      return;
    }

    try {
      setSaving(true);
      await createCategory({
        name: form.name.trim(),
        type: form.type,
        description: form.description,
      });
      setForm({ name: '', type: 'expense', description: '' });
      await loadCategories();
    } catch (err) {
      setError('Не удалось создать категорию: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const renderList = (type) => {
    const filtered = categories.filter(cat => cat.type === type);
    if (filtered.length === 0) {
      return <p className="muted">Пока нет категорий.</p>;
    }

    return (
      <div className="table-container">
        <table className="expenses-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Описание</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(cat => (
              <tr key={cat.id}>
                <td>{cat.name}</td>
                <td>{cat.description || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  if (loading) {
    return <div className="loading">Загрузка категорий...</div>;
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>Новая категория</h3>
        <form className="category-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Название</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Например, Кофе"
            />
          </div>
          <div className="form-row">
            <label>Тип</label>
            <select name="type" value={form.type} onChange={handleChange}>
              <option value="expense">Расход</option>
              <option value="income">Доход</option>
            </select>
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
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Категории расходов</h3>
        {renderList('expense')}
      </div>

      <div className="card">
        <h3>Категории доходов</h3>
        {renderList('income')}
      </div>
    </div>
  );
};

export default Categories;
