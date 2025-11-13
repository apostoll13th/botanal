import React, { useState, useEffect } from 'react';
import './App.css';
import {
  login as apiLogin,
  setAuthToken,
  clearAuthToken,
  getCurrentUser,
  getUserProfile,
} from './services/api';
import Overview from './components/Overview';
import Expenses from './components/Expenses';
import Budgets from './components/Budgets';
import Goals from './components/Goals';
import Categories from './components/Categories';
import Users from './components/Users';
import Memos from './components/Memos';
import Wishlist from './components/Wishlist';
import ThemeToggle from './components/ThemeToggle';
import InstallPWA from './components/InstallPWA';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [authToken, setToken] = useState('');
  const [authUser, setAuthUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(true);
  const [loginForm, setLoginForm] = useState({ login: '', password: '' });

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setAuthToken(storedToken);
      setToken(storedToken);
      bootstrapSession();
    } else {
      setAuthLoading(false);
    }
  }, []);

  const bootstrapSession = async () => {
    try {
      const user = await getCurrentUser();
      setAuthUser(user);
      const profileData = await getUserProfile();
      setProfile(profileData);
    } catch (err) {
      console.error('Не удалось восстановить сессию:', err);
      handleLogout();
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);
    try {
      const data = await apiLogin(loginForm.login, loginForm.password);
      localStorage.setItem('authToken', data.token);
      setAuthToken(data.token);
      setToken(data.token);
      setAuthUser(data.user);
      const profileData = await getUserProfile();
      setProfile(profileData);
      setLoginForm({ login: '', password: '' });
    } catch (err) {
      console.error('Ошибка входа:', err);
      setAuthError('Неверный логин или пароль');
      clearAuthToken();
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    clearAuthToken();
    setToken('');
    setAuthUser(null);
    setProfile(null);
    setActiveTab('overview');
  };

  const renderContent = () => {
    if (!authToken) {
      return (
        <div className="card empty-state">
          <h3>Вход в аналитический кабинет</h3>
          <p>Используйте корпоративный логин и пароль, указанные в codex.md</p>
          <form className="login-form" onSubmit={handleLogin}>
            <input
              type="text"
              placeholder="Логин"
              value={loginForm.login}
              onChange={(e) => setLoginForm({ ...loginForm, login: e.target.value })}
              autoComplete="username"
            />
            <input
              type="password"
              placeholder="Пароль"
              value={loginForm.password}
              onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
              autoComplete="current-password"
            />
            <button type="submit" disabled={authLoading}>
              {authLoading ? 'Входим...' : 'Войти'}
            </button>
            {authError && <div className="error">{authError}</div>}
          </form>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return <Overview />;
      case 'expenses':
        return <Expenses />;
      case 'budgets':
        return <Budgets />;
      case 'goals':
        return <Goals />;
      case 'categories':
        return <Categories />;
      case 'memos':
        return <Memos />;
      case 'wishlist':
        return <Wishlist />;
      case 'users':
        return <Users currentUser={authUser} />;
      default:
        return <Overview />;
    }
  };

  const displayName =
    (profile && profile.user_name) ||
    (authUser && (authUser.full_name || authUser.login)) ||
    'Пользователь';

  return (
    <div className="App">
      <header className="header">
        <div className="flex items-center justify-between w-full">
          <div className="header-left">
            <h1>💰 Семейный бюджет</h1>
          </div>
          <div className="flex items-center gap-3">
            <InstallPWA />
            <ThemeToggle />
            {authToken && (
              <div className="user-info">
                <div className="user-meta">
                  <div className="user-details">
                    <span className="user-name">{displayName}</span>
                    {authUser && authUser.role && (
                      <span className="user-role-badge">{authUser.role === 'admin' ? '👑 Админ' : authUser.role}</span>
                    )}
                  </div>
                  <button className="logout-btn" onClick={handleLogout}>
                    Выйти
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {authToken && (
        <nav className="tabs">
          <button
            className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Обзор
          </button>
          <button
            className={`tab-button ${activeTab === 'expenses' ? 'active' : ''}`}
            onClick={() => setActiveTab('expenses')}
          >
            Операции
          </button>
          <button
            className={`tab-button ${activeTab === 'budgets' ? 'active' : ''}`}
            onClick={() => setActiveTab('budgets')}
          >
            Бюджеты
          </button>
          <button
            className={`tab-button ${activeTab === 'goals' ? 'active' : ''}`}
            onClick={() => setActiveTab('goals')}
          >
            Цели
          </button>
          <button
            className={`tab-button ${activeTab === 'categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('categories')}
          >
            Категории
          </button>
          <button
            className={`tab-button ${activeTab === 'memos' ? 'active' : ''}`}
            onClick={() => setActiveTab('memos')}
          >
            Мемосы
          </button>
          <button
            className={`tab-button ${activeTab === 'wishlist' ? 'active' : ''}`}
            onClick={() => setActiveTab('wishlist')}
          >
            Список желаний
          </button>
          {authUser && authUser.role === 'admin' && (
            <button
              className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              Пользователи
            </button>
          )}
        </nav>
      )}

      <main className="content">
        {authLoading ? <div className="loading">Загрузка...</div> : renderContent()}
      </main>
    </div>
  );
}

export default App;
