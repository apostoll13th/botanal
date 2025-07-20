// Конфигурация
const API_URL = 'http://localhost:5000/api';
let userId = null;
let categoryChart = null;
let dailyChart = null;

// Получение user_id из URL
function getUserIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('user_id');
}

// Инициализация приложения
async function init() {
    userId = getUserIdFromUrl();
    
    if (!userId) {
        alert('Не указан user_id. Используйте URL вида: http://localhost:3000/?user_id=123456');
        return;
    }
    
    // Загружаем информацию о пользователе
    await loadUserInfo();
    
    // Загружаем данные для текущей вкладки
    await loadOverviewData();
}

// Загрузка информации о пользователе
async function loadUserInfo() {
    try {
        const response = await fetch(`${API_URL}/user/${userId}`);
        const user = await response.json();
        
        document.getElementById('user-name').textContent = user.user_name || 'Пользователь';
    } catch (error) {
        console.error('Ошибка загрузки информации о пользователе:', error);
    }
}

// Переключение вкладок
function showTab(tabName) {
    // Скрываем все вкладки
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Убираем активный класс у всех кнопок
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Показываем выбранную вкладку
    document.getElementById(tabName).classList.add('active');
    
    // Делаем кнопку активной
    event.target.classList.add('active');
    
    // Загружаем данные для вкладки
    switch(tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'expenses':
            loadExpenses();
            break;
        case 'budgets':
            loadBudgets();
            break;
        case 'goals':
            loadGoals();
            break;
    }
}

// Загрузка данных для обзора
async function loadOverviewData() {
    try {
        const response = await fetch(`${API_URL}/expenses-summary/${userId}`);
        const data = await response.json();
        
        // Обновляем общую сумму
        document.getElementById('total-expenses').textContent = `${data.total.toFixed(2)} ₽`;
        
        // Создаем круговую диаграмму
        createCategoryChart(data.categories);
        
        // Создаем график динамики
        createDailyChart(data.daily);
        
    } catch (error) {
        console.error('Ошибка загрузки данных обзора:', error);
    }
}

// Создание круговой диаграммы категорий
function createCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    categoryChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.amount),
                backgroundColor: [
                    '#3498db',
                    '#2ecc71',
                    '#f39c12',
                    '#e74c3c',
                    '#9b59b6',
                    '#1abc9c',
                    '#34495e',
                    '#95a5a6'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value.toFixed(2)} ₽ (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Создание графика динамики расходов
function createDailyChart(dailyData) {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChart) {
        dailyChart.destroy();
    }
    
    // Заполняем пропущенные дни
    const filledData = fillMissingDays(dailyData);
    
    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: filledData.map(d => formatDate(d.date)),
            datasets: [{
                label: 'Расходы',
                data: filledData.map(d => d.amount),
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Расходы: ${context.parsed.y.toFixed(2)} ₽`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + ' ₽';
                        }
                    }
                }
            }
        }
    });
}

// Заполнение пропущенных дней
function fillMissingDays(dailyData) {
    if (dailyData.length === 0) return [];
    
    const result = [];
    const startDate = new Date(dailyData[0].date);
    const endDate = new Date();
    
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        const existing = dailyData.find(item => item.date === dateStr);
        
        result.push({
            date: dateStr,
            amount: existing ? existing.amount : 0
        });
    }
    
    return result;
}

// Форматирование даты
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

// Загрузка расходов
async function loadExpenses() {
    try {
        const response = await fetch(`${API_URL}/expenses/${userId}`);
        const expenses = await response.json();
        
        displayExpenses(expenses);
        
    } catch (error) {
        console.error('Ошибка загрузки расходов:', error);
    }
}

// Фильтрация расходов
async function filterExpenses() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const category = document.getElementById('category-filter').value;
    
    let url = `${API_URL}/expenses/${userId}?`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (category) url += `category=${category}&`;
    
    try {
        const response = await fetch(url);
        const expenses = await response.json();
        
        displayExpenses(expenses);
        
    } catch (error) {
        console.error('Ошибка фильтрации расходов:', error);
    }
}

// Отображение расходов в таблице
function displayExpenses(expenses) {
    const tbody = document.getElementById('expenses-tbody');
    
    if (expenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">Нет данных</td></tr>';
        return;
    }
    
    tbody.innerHTML = expenses.map(expense => `
        <tr>
            <td>${formatDate(expense.date)}</td>
            <td>${expense.category}</td>
            <td>${expense.amount.toFixed(2)} ₽</td>
            <td>${expense.description || '-'}</td>
        </tr>
    `).join('');
}

// Загрузка бюджетов
async function loadBudgets() {
    try {
        const response = await fetch(`${API_URL}/budgets/${userId}`);
        const budgets = await response.json();
        
        displayBudgets(budgets);
        
    } catch (error) {
        console.error('Ошибка загрузки бюджетов:', error);
    }
}

// Отображение бюджетов
function displayBudgets(budgets) {
    const container = document.getElementById('budgets-container');
    
    if (budgets.length === 0) {
        container.innerHTML = '<div class="loading">Бюджеты не установлены</div>';
        return;
    }
    
    container.innerHTML = budgets.map(budget => {
        const progressClass = budget.percentage > 90 ? 'danger' : 
                            budget.percentage > 70 ? 'warning' : '';
        
        const periodText = {
            'daily': 'День',
            'weekly': 'Неделя',
            'monthly': 'Месяц'
        }[budget.period] || budget.period;
        
        return `
            <div class="budget-card">
                <h4>${budget.category}</h4>
                <div class="progress-bar">
                    <div class="progress-fill ${progressClass}" style="width: ${Math.min(budget.percentage, 100)}%"></div>
                </div>
                <div class="budget-info">
                    <span>Потрачено: ${budget.spent.toFixed(2)} ₽</span>
                    <span>Лимит: ${budget.amount.toFixed(2)} ₽</span>
                </div>
                <div class="budget-info">
                    <span>Период: ${periodText}</span>
                    <span>${budget.percentage}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// Загрузка целей
async function loadGoals() {
    try {
        const response = await fetch(`${API_URL}/goals/${userId}`);
        const goals = await response.json();
        
        displayGoals(goals);
        
    } catch (error) {
        console.error('Ошибка загрузки целей:', error);
    }
}

// Отображение целей
function displayGoals(goals) {
    const container = document.getElementById('goals-container');
    
    if (goals.length === 0) {
        container.innerHTML = '<div class="loading">Цели не установлены</div>';
        return;
    }
    
    container.innerHTML = goals.map(goal => `
        <div class="goal-card">
            <h4>${goal.name}</h4>
            <p style="color: #666; font-size: 14px; margin-bottom: 10px;">${goal.description}</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(goal.percentage, 100)}%"></div>
            </div>
            <div class="goal-info">
                <span>Накоплено: ${goal.current_amount.toFixed(2)} ₽</span>
                <span>Цель: ${goal.target_amount.toFixed(2)} ₽</span>
            </div>
            <div class="goal-info">
                <span>${goal.percentage}%</span>
                ${goal.target_date ? `<span>До: ${formatDate(goal.target_date)}</span>` : ''}
            </div>
        </div>
    `).join('');
}

// Запуск приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', init);