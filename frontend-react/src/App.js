import React, { useState, useEffect } from 'react';
import './App.css';
import { getUserInfo, upsertUser } from './services/api';
import Overview from './components/Overview';
import Expenses from './components/Expenses';
import Budgets from './components/Budgets';
import Goals from './components/Goals';

function App() {
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState('Загрузка...');
  const [activeTab, setActiveTab] = useState('overview');
  const [nameInput, setNameInput] = useState('');
  const [savingName, setSavingName] = useState(false);

  useEffect(() => {
    // Получаем user_id из URL
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('user_id');

    if (!id) {
      alert('Не указан user_id. Используйте URL вида: http://localhost:8080/?user_id=123456');
      return;
    }

    setUserId(id);

    // Загружаем информацию о пользователе
    getUserInfo(id)
      .then(data => {
        setUserName(data.user_name || 'Пользователь');
        setNameInput(data.user_name || '');
      })
      .catch(error => {
        console.error('Ошибка загрузки данных пользователя:', error);
        setUserName('Пользователь');
      });
  }, []);

  const renderContent = () => {
    if (!userId) return null;

    switch (activeTab) {
      case 'overview':
        return <Overview userId={userId} />;
      case 'expenses':
        return <Expenses userId={userId} />;
      case 'budgets':
        return <Budgets userId={userId} />;
      case 'goals':
        return <Goals userId={userId} />;
      default:
        return <Overview userId={userId} />;
    }
  };

  const handleSaveName = async (e) => {
    e.preventDefault();
    if (!userId || !nameInput.trim()) {
      return;
    }

    try {
      setSavingName(true);
      await upsertUser({
        user_id: Number(userId),
        user_name: nameInput.trim(),
      });
      setUserName(nameInput.trim());
    } catch (err) {
      console.error('Не удалось сохранить имя пользователя:', err);
      alert('Не удалось сохранить имя пользователя');
    } finally {
      setSavingName(false);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>Личный кабинет</h1>
        <div className="user-info">
          <form className="user-form" onSubmit={handleSaveName}>
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              placeholder="Имя пользователя"
            />
            <button type="submit" disabled={savingName}>
              {savingName ? 'Сохранение...' : 'Сохранить'}
            </button>
          </form>
        </div>
      </header>

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
          Расходы
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
      </nav>

      <main className="content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
