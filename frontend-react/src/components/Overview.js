import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Pie, Line } from 'react-chartjs-2';
import { getExpensesSummary } from '../services/api';

// Регистрируем компоненты Chart.js
ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const Overview = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExpensesSummary();
      setSummary(data);
    } catch (err) {
      setError('Ошибка загрузки данных: ' + err.message);
      console.error('Error loading summary:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Загрузка данных...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!summary || summary.categories.length === 0) {
    return (
      <div className="card">
        <p>Нет данных о расходах за последние 30 дней.</p>
      </div>
    );
  }

  // Данные для круговой диаграммы
  const categoryChartData = {
    labels: summary.categories.map(c => c.category),
    datasets: [
      {
        data: summary.categories.map(c => c.amount),
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)',
          'rgba(199, 199, 199, 0.8)',
          'rgba(83, 102, 255, 0.8)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(199, 199, 199, 1)',
          'rgba(83, 102, 255, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  // Данные для линейного графика
  const dailyChartData = {
    labels: summary.daily.map(d => new Date(d.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })),
    datasets: [
      {
        label: 'Расходы по дням',
        data: summary.daily.map(d => d.amount),
        borderColor: 'rgba(102, 126, 234, 1)',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  return (
    <div>
      <div className="summary-cards">
        <div className="card">
          <h3>Расходы за 30 дней</h3>
          <p className="total-amount">{summary.total.toFixed(2)} ₽</p>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Расходы по категориям</h3>
          <Pie data={categoryChartData} options={chartOptions} />
        </div>

        <div className="chart-container">
          <h3>Динамика расходов</h3>
          <Line data={dailyChartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};

export default Overview;
