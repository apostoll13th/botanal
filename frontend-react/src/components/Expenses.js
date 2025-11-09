import React, { useState, useEffect } from 'react';
import {
  getExpenses,
  createTransaction,
  listCategories,
  createCategory as apiCreateCategory,
} from '../services/api';
import './Expenses.css';

const defaultDate = () => new Date().toISOString().slice(0, 10);

const Expenses = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    category: '',
    type: 'expense',
  });
  const [transactionForm, setTransactionForm] = useState({
    amount: '',
    category: '',
    date: defaultDate(),
    description: '',
    transactionType: 'expense',
  });
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    type: 'expense',
    description: '',
  });
  const [savingTransaction, setSavingTransaction] = useState(false);
  const [savingCategory, setSavingCategory] = useState(false);

  useEffect(() => {
    loadData();
    loadCategories();
  }, [userId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExpenses(userId, filters);
      setExpenses(data);
    } catch (err) {
      setError('Ошибка загрузки расходов: ' + err.message);
      console.error('Error loading expenses:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await listCategories();
      setCategories(data);
    } catch (err) {
      console.error('Ошибка загрузки категорий:', err);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleApplyFilters = () => {
    loadData();
  };

  const handleResetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      category: '',
      type: 'expense',
    });
    setTimeout(() => loadData(), 100);
  };

  const handleTransactionChange = (e) => {
    const { name, value } = e.target;
    if (name === 'transactionType') {
      setTransactionForm(prev => ({
        ...prev,
        transactionType: value,
        category: '',
      }));
      return;
    }
    setTransactionForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCreateTransaction = async (e) => {
    e.preventDefault();
    if (!transactionForm.amount || !transactionForm.category) {
      setError('Укажите сумму и категорию');
      return;
    }

    try {
      setSavingTransaction(true);
      setError(null);

      await createTransaction({
        user_id: Number(userId),
        amount: Number(transactionForm.amount),
        category: transactionForm.category,
        date: transactionForm.date,
        description: transactionForm.description,
        transaction_type: transactionForm.transactionType,
      });

      setTransactionForm({
        amount: '',
        category: '',
        date: defaultDate(),
        description: '',
        transactionType: transactionForm.transactionType,
      });

      await loadData();
      await loadCategories();
    } catch (err) {
      setError('Не удалось сохранить операцию: ' + err.message);
      console.error('Error creating transaction:', err);
    } finally {
      setSavingTransaction(false);
    }
  };

  const handleCategoryChange = (e) => {
    const { name, value } = e.target;
    setCategoryForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!categoryForm.name) {
      setError('Введите название категории');
      return;
    }

    try {
      setSavingCategory(true);
      setError(null);
      await apiCreateCategory({
        name: categoryForm.name,
        type: categoryForm.type,
        description: categoryForm.description,
      });
      setCategoryForm({
        name: '',
        type: categoryForm.type,
        description: '',
      });
      await loadCategories();
    } catch (err) {
      setError('Не удалось сохранить категорию: ' + err.message);
      console.error('Error creating category:', err);
    } finally {
      setSavingCategory(false);
    }
  };

  const filteredCategories = categories.filter(cat => cat.type === transactionForm.transactionType);

  if (loading) {
    return <div className="loading">Загрузка расходов...</div>;
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>Фильтры</h3>
        <div className="filters">
          <div className="filter-group">
            <label>С даты:</label>
            <input
              type="date"
              name="startDate"
              value={filters.startDate}
              onChange={handleFilterChange}
            />
          </div>
          <div className="filter-group">
            <label>По дату:</label>
            <input
              type="date"
              name="endDate"
              value={filters.endDate}
              onChange={handleFilterChange}
            />
          </div>
          <div className="filter-group">
            <label>Категория:</label>
            <input
              type="text"
              name="category"
              value={filters.category}
              onChange={handleFilterChange}
              placeholder="Название категории"
            />
          </div>
          <div className="filter-group">
            <label>Тип операции:</label>
            <select
              name="type"
              value={filters.type}
              onChange={handleFilterChange}
            >
              <option value="expense">Расход</option>
              <option value="income">Доход</option>
              <option value="all">Все</option>
            </select>
          </div>
          <div className="filter-buttons">
            <button className="btn btn-primary" onClick={handleApplyFilters}>
              Применить
            </button>
            <button className="btn btn-secondary" onClick={handleResetFilters}>
              Сбросить
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Новая операция</h3>
        <form className="transaction-form" onSubmit={handleCreateTransaction}>
          <div className="form-row">
            <label>Тип:</label>
            <select
              name="transactionType"
              value={transactionForm.transactionType}
              onChange={handleTransactionChange}
            >
              <option value="expense">Расход</option>
              <option value="income">Доход</option>
            </select>
          </div>
          <div className="form-row">
            <label>Сумма:</label>
            <input
              type="number"
              name="amount"
              min="0"
              step="0.01"
              value={transactionForm.amount}
              onChange={handleTransactionChange}
              placeholder="0.00"
            />
          </div>
          <div className="form-row">
            <label>Категория:</label>
            <select
              name="category"
              value={transactionForm.category}
              onChange={handleTransactionChange}
            >
              <option value="">Выберите категорию</option>
              {filteredCategories.map(cat => (
                <option key={cat.id} value={cat.name}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-row">
            <label>Дата:</label>
            <input
              type="date"
              name="date"
              value={transactionForm.date}
              onChange={handleTransactionChange}
            />
          </div>
          <div className="form-row">
            <label>Описание:</label>
            <input
              type="text"
              name="description"
              value={transactionForm.description}
              onChange={handleTransactionChange}
              placeholder="Комментарий (необязательно)"
            />
          </div>
          <div className="form-row">
            <button className="btn btn-primary" type="submit" disabled={savingTransaction}>
              {savingTransaction ? 'Сохранение...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Категории</h3>
        <form className="category-form" onSubmit={handleCreateCategory}>
          <div className="form-row">
            <label>Название:</label>
            <input
              type="text"
              name="name"
              value={categoryForm.name}
              onChange={handleCategoryChange}
              placeholder="Например, Продукты"
            />
          </div>
          <div className="form-row">
            <label>Тип:</label>
            <select
              name="type"
              value={categoryForm.type}
              onChange={handleCategoryChange}
            >
              <option value="expense">Расход</option>
              <option value="income">Доход</option>
            </select>
          </div>
          <div className="form-row">
            <label>Описание:</label>
            <input
              type="text"
              name="description"
              value={categoryForm.description}
              onChange={handleCategoryChange}
              placeholder="Короткое описание"
            />
          </div>
          <div className="form-row">
            <button className="btn btn-secondary" type="submit" disabled={savingCategory}>
              {savingCategory ? 'Сохранение...' : 'Добавить категорию'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Операции ({expenses.length})</h3>
        {expenses.length === 0 ? (
          <p>Нет операций для отображения.</p>
        ) : (
          <div className="table-container">
            <table className="expenses-table">
              <thead>
                <tr>
                  <th>Тип</th>
                  <th>Дата</th>
                  <th>Категория</th>
                  <th>Сумма</th>
                  <th>Описание</th>
                  <th>Пользователь</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr key={expense.id}>
                    <td>
                      <span className={`type-badge ${expense.transaction_type === 'income' ? 'income' : 'expense'}`}>
                        {expense.transaction_type === 'income' ? 'Доход' : 'Расход'}
                      </span>
                    </td>
                    <td>{new Date(expense.date).toLocaleDateString('ru-RU')}</td>
                    <td>
                      <span className="category-badge">{expense.category}</span>
                    </td>
                    <td className={`amount ${expense.transaction_type === 'income' ? 'income' : ''}`}>
                      {expense.amount.toFixed(2)} ₽
                    </td>
                    <td>{expense.description || '-'}</td>
                    <td>{expense.user_name || '-'}</td>
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

export default Expenses;
