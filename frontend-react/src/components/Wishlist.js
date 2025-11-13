import React, { useState, useEffect } from 'react';
import { getWishlist, createWishlistItem, updateWishlistItem, deleteWishlistItem } from '../services/api';
import './Wishlist.css';

const Wishlist = () => {
  const [items, setItems] = useState([]);
  const [newItem, setNewItem] = useState({
    title: '',
    description: '',
    url: '',
    imageUrl: '',
    priority: 0,
  });
  const [editingItem, setEditingItem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, active, completed

  useEffect(() => {
    loadWishlist();
  }, []);

  const loadWishlist = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWishlist();
      setItems(data);
    } catch (err) {
      setError('Не удалось загрузить список желаний');
      console.error('Error loading wishlist:', err);
    } finally {
      setLoading(false);
    }
  };

  const addItem = async () => {
    if (!newItem.title.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const payload = {
        title: newItem.title.trim(),
        description: newItem.description.trim() || null,
        url: newItem.url.trim() || null,
        image_url: newItem.imageUrl.trim() || null,
        priority: newItem.priority,
      };
      await createWishlistItem(payload);
      setNewItem({ title: '', description: '', url: '', imageUrl: '', priority: 0 });
      await loadWishlist();
    } catch (err) {
      setError('Не удалось создать элемент');
      console.error('Error creating wishlist item:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateItem = async (id, updates) => {
    setLoading(true);
    setError(null);
    try {
      await updateWishlistItem(id, updates);
      setEditingItem(null);
      await loadWishlist();
    } catch (err) {
      setError('Не удалось обновить элемент');
      console.error('Error updating wishlist item:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleCompleted = async (item) => {
    await handleUpdateItem(item.id, { is_completed: !item.is_completed });
  };

  const handleDeleteItem = async (id) => {
    if (!window.confirm('Удалить этот элемент из списка желаний?')) return;

    setLoading(true);
    setError(null);
    try {
      await deleteWishlistItem(id);
      await loadWishlist();
    } catch (err) {
      setError('Не удалось удалить элемент');
      console.error('Error deleting wishlist item:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterItems = () => {
    switch (filter) {
      case 'active':
        return items.filter(item => !item.is_completed);
      case 'completed':
        return items.filter(item => item.is_completed);
      default:
        return items;
    }
  };

  const getPriorityLabel = (priority) => {
    if (priority >= 3) return { text: 'Высокий', class: 'high' };
    if (priority >= 1) return { text: 'Средний', class: 'medium' };
    return { text: 'Низкий', class: 'low' };
  };

  const getCurrentItem = (id) => {
    return items.find(item => item.id === id);
  };

  return (
    <div className="wishlist-container">
      <div className="wishlist-header">
        <h2>🎁 Список желаний</h2>
        <p className="subtitle">Храните свои желания, идеи и планы</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="wishlist-input-section">
        <input
          type="text"
          placeholder="Название (обязательно)..."
          value={newItem.title}
          onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
          className="wishlist-title-input"
          disabled={loading}
        />
        <textarea
          placeholder="Описание..."
          value={newItem.description}
          onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
          className="wishlist-description-input"
          rows="2"
          disabled={loading}
        />
        <input
          type="url"
          placeholder="Ссылка (URL)..."
          value={newItem.url}
          onChange={(e) => setNewItem({ ...newItem, url: e.target.value })}
          className="wishlist-url-input"
          disabled={loading}
        />
        <input
          type="url"
          placeholder="Ссылка на картинку (URL)..."
          value={newItem.imageUrl}
          onChange={(e) => setNewItem({ ...newItem, imageUrl: e.target.value })}
          className="wishlist-image-input"
          disabled={loading}
        />
        <div className="priority-selector">
          <label>Приоритет:</label>
          <select
            value={newItem.priority}
            onChange={(e) => setNewItem({ ...newItem, priority: parseInt(e.target.value) })}
            className="priority-select"
            disabled={loading}
          >
            <option value={0}>Низкий</option>
            <option value={1}>Средний</option>
            <option value={3}>Высокий</option>
          </select>
        </div>
        <button onClick={addItem} className="add-wishlist-btn" disabled={loading}>
          {loading ? 'Сохранение...' : 'Добавить в список'}
        </button>
      </div>

      <div className="filter-buttons">
        <button
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          Все ({items.length})
        </button>
        <button
          className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
          onClick={() => setFilter('active')}
        >
          Активные ({items.filter(i => !i.is_completed).length})
        </button>
        <button
          className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
          onClick={() => setFilter('completed')}
        >
          Исполненные ({items.filter(i => i.is_completed).length})
        </button>
      </div>

      <div className="wishlist-grid">
        {loading && items.length === 0 ? (
          <div className="empty-state">
            <p>Загрузка...</p>
          </div>
        ) : filterItems().length === 0 ? (
          <div className="empty-state">
            <p>Список пуст. Добавьте свои желания!</p>
          </div>
        ) : (
          filterItems().map(item => (
            <div key={item.id} className={`wishlist-card ${item.is_completed ? 'completed' : ''}`}>
              {editingItem === item.id ? (
                <WishlistEditForm
                  item={getCurrentItem(item.id)}
                  onSave={(updates) => handleUpdateItem(item.id, updates)}
                  onCancel={() => setEditingItem(null)}
                  loading={loading}
                />
              ) : (
                <>
                  {item.image_url && (
                    <div className="wishlist-image">
                      <img src={item.image_url} alt={item.title} />
                    </div>
                  )}
                  <div className="wishlist-content">
                    <div className="wishlist-card-header">
                      <h3>{item.title}</h3>
                      <span className={`priority-badge ${getPriorityLabel(item.priority).class}`}>
                        {getPriorityLabel(item.priority).text}
                      </span>
                    </div>
                    {item.description && (
                      <p className="wishlist-description">{item.description}</p>
                    )}
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="wishlist-link"
                      >
                        🔗 Перейти по ссылке
                      </a>
                    )}
                    <div className="wishlist-actions">
                      <button
                        onClick={() => toggleCompleted(item)}
                        className={`complete-btn ${item.is_completed ? 'completed' : ''}`}
                        title={item.is_completed ? 'Отметить как активное' : 'Отметить как исполненное'}
                        disabled={loading}
                      >
                        {item.is_completed ? '↩️ Вернуть' : '✓ Исполнено'}
                      </button>
                      <button
                        onClick={() => setEditingItem(item.id)}
                        className="edit-btn"
                        title="Редактировать"
                        disabled={loading}
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteItem(item.id)}
                        className="delete-btn"
                        title="Удалить"
                        disabled={loading}
                      >
                        🗑️
                      </button>
                    </div>
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

// Separate component for editing wishlist item
const WishlistEditForm = ({ item, onSave, onCancel, loading }) => {
  const [title, setTitle] = useState(item.title);
  const [description, setDescription] = useState(item.description || '');
  const [url, setUrl] = useState(item.url || '');
  const [imageUrl, setImageUrl] = useState(item.image_url || '');
  const [priority, setPriority] = useState(item.priority);

  const handleSave = () => {
    const updates = {};
    if (title !== item.title) updates.title = title;
    if (description !== (item.description || '')) updates.description = description || null;
    if (url !== (item.url || '')) updates.url = url || null;
    if (imageUrl !== (item.image_url || '')) updates.image_url = imageUrl || null;
    if (priority !== item.priority) updates.priority = priority;

    if (Object.keys(updates).length > 0) {
      onSave(updates);
    } else {
      onCancel();
    }
  };

  return (
    <div className="wishlist-edit-form">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="wishlist-title-input"
        placeholder="Название"
        disabled={loading}
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="wishlist-description-input"
        placeholder="Описание"
        rows="2"
        disabled={loading}
      />
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="wishlist-url-input"
        placeholder="Ссылка"
        disabled={loading}
      />
      <input
        type="url"
        value={imageUrl}
        onChange={(e) => setImageUrl(e.target.value)}
        className="wishlist-image-input"
        placeholder="Ссылка на картинку"
        disabled={loading}
      />
      <div className="priority-selector">
        <label>Приоритет:</label>
        <select
          value={priority}
          onChange={(e) => setPriority(parseInt(e.target.value))}
          className="priority-select"
          disabled={loading}
        >
          <option value={0}>Низкий</option>
          <option value={1}>Средний</option>
          <option value={3}>Высокий</option>
        </select>
      </div>
      <div className="wishlist-edit-actions">
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

export default Wishlist;
