import React, { useState, useEffect } from 'react';
import './Memos.css';

const Memos = () => {
  const [memos, setMemos] = useState([]);
  const [newMemo, setNewMemo] = useState({ title: '', content: '' });
  const [editingMemo, setEditingMemo] = useState(null);
  const [filter, setFilter] = useState('all'); // all, today, week, month

  useEffect(() => {
    // Load memos from localStorage for now
    // TODO: Implement API endpoints in backend
    const savedMemos = localStorage.getItem('memos');
    if (savedMemos) {
      setMemos(JSON.parse(savedMemos));
    }
  }, []);

  useEffect(() => {
    // Save memos to localStorage
    localStorage.setItem('memos', JSON.stringify(memos));
  }, [memos]);

  const addMemo = () => {
    if (!newMemo.title.trim() && !newMemo.content.trim()) return;

    const memo = {
      id: Date.now(),
      title: newMemo.title || 'Без названия',
      content: newMemo.content,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setMemos([memo, ...memos]);
    setNewMemo({ title: '', content: '' });
  };

  const updateMemo = (id, updates) => {
    setMemos(memos.map(memo =>
      memo.id === id
        ? { ...memo, ...updates, updatedAt: new Date().toISOString() }
        : memo
    ));
    setEditingMemo(null);
  };

  const deleteMemo = (id) => {
    if (window.confirm('Удалить эту запись?')) {
      setMemos(memos.filter(memo => memo.id !== id));
    }
  };

  const filterMemos = () => {
    const now = new Date();
    const startOfDay = new Date(now.setHours(0, 0, 0, 0));
    const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()));
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

    switch (filter) {
      case 'today':
        return memos.filter(m => new Date(m.createdAt) >= startOfDay);
      case 'week':
        return memos.filter(m => new Date(m.createdAt) >= startOfWeek);
      case 'month':
        return memos.filter(m => new Date(m.createdAt) >= startOfMonth);
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

  return (
    <div className="memos-container">
      <div className="memos-header">
        <h2>📝 Мемосы (Дневник)</h2>
        <p className="subtitle">Ведите личные заметки и дневник</p>
      </div>

      <div className="memo-input-section">
        <input
          type="text"
          placeholder="Заголовок..."
          value={newMemo.title}
          onChange={(e) => setNewMemo({ ...newMemo, title: e.target.value })}
          className="memo-title-input"
        />
        <textarea
          placeholder="Напишите что-то..."
          value={newMemo.content}
          onChange={(e) => setNewMemo({ ...newMemo, content: e.target.value })}
          className="memo-content-input"
          rows="4"
        />
        <button onClick={addMemo} className="add-memo-btn">
          Добавить запись
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
        {filterMemos().length === 0 ? (
          <div className="empty-state">
            <p>Пока нет записей. Начните вести дневник!</p>
          </div>
        ) : (
          filterMemos().map(memo => (
            <div key={memo.id} className="memo-card">
              {editingMemo === memo.id ? (
                <div className="memo-edit-form">
                  <input
                    type="text"
                    value={memo.title}
                    onChange={(e) => updateMemo(memo.id, { title: e.target.value })}
                    className="memo-title-input"
                  />
                  <textarea
                    value={memo.content}
                    onChange={(e) => updateMemo(memo.id, { content: e.target.value })}
                    className="memo-content-input"
                    rows="4"
                  />
                  <button onClick={() => setEditingMemo(null)} className="save-btn">
                    Сохранить
                  </button>
                </div>
              ) : (
                <>
                  <div className="memo-header">
                    <h3>{memo.title}</h3>
                    <div className="memo-actions">
                      <button
                        onClick={() => setEditingMemo(memo.id)}
                        className="edit-btn"
                        title="Редактировать"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteMemo(memo.id)}
                        className="delete-btn"
                        title="Удалить"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  <p className="memo-content">{memo.content}</p>
                  <div className="memo-footer">
                    <span className="memo-date">{formatDate(memo.createdAt)}</span>
                    {memo.updatedAt !== memo.createdAt && (
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

export default Memos;
