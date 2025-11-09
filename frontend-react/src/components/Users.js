import React, { useState, useEffect } from 'react';
import {
  getAppUsers,
  createAppUser,
  updateAppUser,
  deleteAppUser,
} from '../services/api';

const Users = ({ currentUser }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form, setForm] = useState({
    login: '',
    password: '',
    full_name: '',
    role: 'analyst',
    telegram_user_id: '',
  });

  const isAdmin = currentUser && currentUser.role === 'admin';

  useEffect(() => {
    if (isAdmin) {
      loadUsers();
    } else {
      setLoading(false);
    }
  }, [isAdmin]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await getAppUsers();
      setUsers(data);
      setError('');
    } catch (err) {
      setError('Не удалось загрузить пользователей: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const resetForm = () => {
    setEditingUser(null);
    setForm({
      login: '',
      password: '',
      full_name: '',
      role: 'analyst',
      telegram_user_id: '',
    });
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setForm({
      login: user.login,
      password: '',
      full_name: user.full_name || '',
      role: user.role,
      telegram_user_id: String(user.telegram_user_id),
    });
  };

  const handleDelete = async (user) => {
    if (!window.confirm(`Удалить пользователя ${user.login}?`)) return;
    try {
      await deleteAppUser(user.id);
      await loadUsers();
    } catch (err) {
      setError('Не удалось удалить пользователя: ' + err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.login.trim()) {
      setError('Введите логин');
      return;
    }
    if (!editingUser && !form.password.trim()) {
      setError('Введите пароль');
      return;
    }
    if (!form.telegram_user_id.trim()) {
      setError('Укажите Telegram user_id');
      return;
    }

    const payload = {
      login: form.login.trim(),
      password: form.password.trim(),
      full_name: form.full_name.trim(),
      role: form.role,
      telegram_user_id: Number(form.telegram_user_id),
    };

    try {
      setSaving(true);
      if (editingUser) {
        if (!payload.password) {
          delete payload.password;
        }
        await updateAppUser(editingUser.id, payload);
      } else {
        await createAppUser(payload);
      }
      resetForm();
      await loadUsers();
    } catch (err) {
      setError('Ошибка сохранения пользователя: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="card">
        <p>Доступ к управлению пользователями есть только у администраторов.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="loading">Загрузка пользователей...</div>;
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>{editingUser ? `Редактирование: ${editingUser.login}` : 'Новый пользователь'}</h3>
        <form className="category-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Логин</label>
            <input
              type="text"
              name="login"
              value={form.login}
              onChange={handleChange}
              placeholder="Например, finance_manager"
            />
          </div>
          <div className="form-row">
            <label>Пароль {editingUser && <small>(оставьте пустым, чтобы не менять)</small>}</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Сильный пароль"
            />
          </div>
          <div className="form-row">
            <label>Полное имя</label>
            <input
              type="text"
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              placeholder="Необязательно"
            />
          </div>
          <div className="form-row">
            <label>Роль</label>
            <select name="role" value={form.role} onChange={handleChange}>
              <option value="admin">Администратор</option>
              <option value="analyst">Аналитик</option>
            </select>
          </div>
          <div className="form-row">
            <label>Telegram user_id</label>
            <input
              type="number"
              name="telegram_user_id"
              value={form.telegram_user_id}
              onChange={handleChange}
              placeholder="Например, 123456789"
            />
          </div>
          <div className="form-row">
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : (editingUser ? 'Обновить' : 'Создать')}
            </button>
            {editingUser && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={resetForm}
                disabled={saving}
              >
                Отмена
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Существующие пользователи</h3>
        {users.length === 0 ? (
          <p>Пользователи еще не добавлены.</p>
        ) : (
          <div className="table-container">
            <table className="expenses-table">
              <thead>
                <tr>
                  <th>Логин</th>
                  <th>Имя</th>
                  <th>Роль</th>
                  <th>Telegram ID</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id}>
                    <td>{user.login}</td>
                    <td>{user.full_name || '-'}</td>
                    <td>{user.role}</td>
                    <td>{user.telegram_user_id}</td>
                    <td className="actions">
                      <button className="btn btn-secondary" onClick={() => handleEdit(user)}>
                        Изменить
                      </button>
                      {user.login !== currentUser.login && (
                        <button className="btn btn-danger" onClick={() => handleDelete(user)}>
                          Удалить
                        </button>
                      )}
                    </td>
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

export default Users;
