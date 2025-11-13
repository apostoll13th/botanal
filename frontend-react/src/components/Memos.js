import React, { useState, useEffect } from 'react';
import { getMemos, createMemo, updateMemo, deleteMemo } from '../services/api';
import './Memos.css';

const Memos = () => {
  const [memos, setMemos] = useState([]);
  const [newMemo, setNewMemo] = useState({ title: '', content: '' });
  const [editingMemo, setEditingMemo] = useState(null);
  const [filter, setFilter] = useState('all'); // all, today, week, month
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMemos();
  }, []);

  const loadMemos = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMemos();
      setMemos(data);
    } catch (err) {
      setError('Не удалось загрузить записи');
      console.error('Error loading memos:', err);
    } finally {
      setLoading(false);
    }
  };

  const addMemo = async () => {
    if (!newMemo.content.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const payload = {
        title: newMemo.title.trim() || 'Без названия',
        content: newMemo.content.trim(),
      };
      await createMemo(payload);
      setNewMemo({ title: '', content: '' });
      await loadMemos(); // Reload to get the created memo with ID and timestamps
    } catch (err) {
      setError('Не удалось создать запись');
      console.error('Error creating memo:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMemo = async (id, updates) => {
    setLoading(true);
    setError(null);
    try {
      await updateMemo(id, updates);
      setEditingMemo(null);
      await loadMemos(); // Reload to get updated data
    } catch (err) {
      setError('Не удалось обновить запись');
      console.error('Error updating memo:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMemo = async (id) => {
    if (!window.confirm('Удалить эту запись?')) return;

    setLoading(true);
    setError(null);
    try {
      await deleteMemo(id);
      await loadMemos(); // Reload after deletion
    } catch (err) {
      setError('Не удалось удалить запись');
      console.error('Error deleting memo:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterMemos = () => {
    const now = new Date();
    const startOfDay = new Date(now.setHours(0, 0, 0, 0));
    const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()));
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

    switch (filter) {
      case 'today':
        return memos.filter(m => new Date(m.created_at) >= startOfDay);
      case 'week':
        return memos.filter(m => new Date(m.created_at) >= startOfWeek);
      case 'month':
        return memos.filter(m => new Date(m.created_at) >= startOfMonth);
      default:
        return memos;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getCurrentMemo = (id) => {
    return memos.find(m => m.id === id);
  };

  return (
    <div className="memos-container">
      <div className="memos-header">
        <h2>📝 Мемосы (Дневник)</h2>
        <p className="subtitle">Ведите личные заметки и дневник</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="memo-input-section">
        <input
          type="text"
          placeholder="Заголовок..."
          value={newMemo.title}
          onChange={(e) => setNewMemo({ ...newMemo, title: e.target.value })}
          className="memo-title-input"
          disabled={loading}
        />
        <textarea
          placeholder="Напишите что-то..."
          value={newMemo.content}
          onChange={(e) => setNewMemo({ ...newMemo, content: e.target.value })}
          className="memo-content-input"
          rows="4"
          disabled={loading}
        />
        <button onClick={addMemo} className="add-memo-btn" disabled={loading}>
          {loading ? 'Сохранение...' : 'Добавить запись'}
        </button>
      </div>

      <div className="filter-buttons">
        <button
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          Все
        </button>
        <button
          className={`filter-btn ${filter === 'today' ? 'active' : ''}`}
          onClick={() => setFilter('today')}
        >
          Сегодня
        </button>
        <button
          className={`filter-btn ${filter === 'week' ? 'active' : ''}`}
          onClick={() => setFilter('week')}
        >
          Неделя
        </button>
        <button
          className={`filter-btn ${filter === 'month' ? 'active' : ''}`}
          onClick={() => setFilter('month')}
        >
          Месяц
        </button>
      </div>

      <div className="memos-list">
        {loading && memos.length === 0 ? (
          <div className="empty-state">
            <p>Загрузка...</p>
          </div>
        ) : filterMemos().length === 0 ? (
          <div className="empty-state">
            <p>Пока нет записей. Начните вести дневник!</p>
          </div>
        ) : (
          filterMemos().map(memo => (
            <div key={memo.id} className="memo-card">
              {editingMemo === memo.id ? (
                <MemoEditForm
                  memo={getCurrentMemo(memo.id)}
                  onSave={(updates) => handleUpdateMemo(memo.id, updates)}
                  onCancel={() => setEditingMemo(null)}
                  loading={loading}
                />
              ) : (
                <>
                  <div className="memo-header">
                    <h3>{memo.title}</h3>
                    <div className="memo-actions">
                      <button
                        onClick={() => setEditingMemo(memo.id)}
                        className="edit-btn"
                        title="Редактировать"
                        disabled={loading}
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteMemo(memo.id)}
                        className="delete-btn"
                        title="Удалить"
                        disabled={loading}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  <p className="memo-content">{memo.content}</p>
                  <div className="memo-footer">
                    <span className="memo-date">{formatDate(memo.created_at)}</span>
                    {memo.updated_at !== memo.created_at && (
                      <span className="memo-updated">(обновлено)</span>
                    )}
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Separate component for editing memo
const MemoEditForm = ({ memo, onSave, onCancel, loading }) => {
  const [title, setTitle] = useState(memo.title);
  const [content, setContent] = useState(memo.content);

  const handleSave = () => {
    const updates = {};
    if (title !== memo.title) updates.title = title;
    if (content !== memo.content) updates.content = content;

    if (Object.keys(updates).length > 0) {
      onSave(updates);
    } else {
      onCancel();
    }
  };

  return (
    <div className="memo-edit-form">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="memo-title-input"
        disabled={loading}
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="memo-content-input"
        rows="4"
        disabled={loading}
      />
      <div className="memo-edit-actions">
        <button onClick={handleSave} className="save-btn" disabled={loading}>
          {loading ? 'Сохранение...' : 'Сохранить'}
        </button>
        <button onClick={onCancel} className="cancel-btn" disabled={loading}>
          Отмена
        </button>
      </div>
    </div>
  );
};

export default Memos;
