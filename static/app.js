// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Проверка прав доступа администратора
const ADMIN_PASSWORD = "sadcat";
const ADMIN_USERNAMES = []; // Будет заполнено сервером
let isAdmin = false;

// Проверяем параметры URL и Telegram WebApp
function checkAdminAccess() {
    // ВАЖНО: Если список администраторов не настроен (пустой), очищаем sessionStorage и запрещаем доступ
    if (!ADMIN_USERNAMES || ADMIN_USERNAMES.length === 0) {
        sessionStorage.removeItem('admin_authenticated');
        isAdmin = false;
        applyAdminAccess();
        return;
    }
    
    isAdmin = false; // Сбрасываем статус администратора
    
    // Проверяем параметр из URL (для админа из бота)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('admin') === 'true') {
        isAdmin = true;
    }

    // Проверяем username из Telegram WebApp
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const username = tg.initDataUnsafe.user.username;
        if (username) {
            // Проверяем, есть ли username в списке администраторов
            if (ADMIN_USERNAMES.includes(username.toLowerCase())) {
                isAdmin = true;
            }
        }
    }

    // Проверяем сохраненный пароль в sessionStorage (только если список администраторов настроен)
    if (sessionStorage.getItem('admin_authenticated') === 'true') {
        isAdmin = true;
    }

    // Применяем права доступа
    applyAdminAccess();
}

// Применение прав доступа к интерфейсу
function applyAdminAccess() {
    const manageTab = document.querySelector('[data-tab="manage"]');
    const adminTabContent = document.getElementById('admin');
    const adminLoginBtn = document.getElementById('adminLoginBtn');
    const adminLogoutBtn = document.getElementById('adminLogoutBtn');
    
    if (isAdmin) {
        // Показываем админ функции
        if (manageTab) manageTab.style.display = 'block'; // Используем 'block' вместо '' для переопределения CSS
        if (adminTabContent) adminTabContent.style.display = 'none'; // Скрываем вкладку Admin для авторизованных
        if (adminLoginBtn) adminLoginBtn.style.display = 'none';
        if (adminLogoutBtn) adminLogoutBtn.style.display = 'block'; // Показываем кнопку "Выйти"
        
        // Убираем классы скрытия админ элементов
        document.querySelectorAll('.admin-only').forEach(el => {
            // Для кнопок используем 'block', для других элементов - в зависимости от их типа
            if (el.classList.contains('tab-btn')) {
                el.style.display = 'block';
            } else {
                el.style.display = ''; // Для остальных элементов используем пустую строку (убираем inline стиль)
            }
        });
    } else {
        // Скрываем админ функции
        if (manageTab) manageTab.style.display = 'none';
        if (adminTabContent) adminTabContent.style.display = ''; // Показываем вкладку Admin для неавторизованных
        if (adminLoginBtn) adminLoginBtn.style.display = 'block'; // Показываем кнопку "Admin"
        if (adminLogoutBtn) adminLogoutBtn.style.display = 'none'; // Скрываем кнопку "Выйти"
        
        // Скрываем админ элементы
        document.querySelectorAll('.admin-only').forEach(el => {
            el.style.display = 'none';
        });
    }
}

// Функции для работы с формой входа
function checkAdminPassword() {
    const password = document.getElementById('adminPassword').value;
    const errorDiv = document.getElementById('adminError');
    
    if (password === ADMIN_PASSWORD) {
        isAdmin = true;
        sessionStorage.setItem('admin_authenticated', 'true');
        applyAdminAccess();
        showToast('✅ Вы вошли как администратор', 'success');
        
        // Очищаем поле пароля
        document.getElementById('adminPassword').value = '';
        errorDiv.style.display = 'none';
        
        // Переключаемся на главную вкладку (дашборд)
        const dashboardTab = document.querySelector('[data-tab="dashboard"]');
        if (dashboardTab) {
            dashboardTab.click();
        }
    } else {
        errorDiv.textContent = 'Неверный пароль';
        errorDiv.style.display = 'block';
        document.getElementById('adminPassword').value = '';
    }
}

function logoutAdmin() {
    isAdmin = false;
    sessionStorage.removeItem('admin_authenticated');
    applyAdminAccess();
    showToast('Вы вышли из режима администратора', 'info');
    
    // Переключаемся на дашборд, если были на вкладке управления
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab && activeTab.dataset.tab === 'manage') {
        document.querySelector('[data-tab="dashboard"]').click();
    }
}

// Обработчик нажатия Enter в поле пароля
document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('adminPassword');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                checkAdminPassword();
            }
        });
    }
});

// Перехватываем fetch для добавления заголовков (устаревший код, можно удалить)
const originalFetch = window.fetch;
window.fetch = function(...args) {
    // Если первый аргумент - строка (URL), добавляем заголовки
    if (typeof args[0] === 'string' || args[0] instanceof Request) {
        const options = args[1] || {};
        
        // Добавляем заголовок bypass-tunnel-reminder
        options.headers = options.headers || {};
        if (options.headers instanceof Headers) {
            options.headers.set('bypass-tunnel-reminder', 'true');
        } else {
            options.headers['bypass-tunnel-reminder'] = 'true';
        }
        
        args[1] = options;
    }
    
    return originalFetch.apply(this, args);
};

const API_BASE = '/api';

// Утилиты
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatUptime(seconds) {
    if (!seconds) return '-';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}д ${hours}ч`;
    if (hours > 0) return `${hours}ч ${minutes}м`;
    return `${minutes}м`;
}

// Переключение вкладок
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Пропускаем кнопки без data-tab (например, Admin, Выйти)
        if (!tabName) {
            return;
        }
        
        // Убираем активный класс со всех кнопок и контента
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Добавляем активный класс выбранным
        btn.classList.add('active');
        const tabContent = document.getElementById(tabName);
        if (tabContent) {
            tabContent.classList.add('active');
        } else {
            console.error(`Элемент с id="${tabName}" не найден`);
        }
        
        // Загружаем данные при переключении
        if (tabName === 'dashboard') {
            refreshDashboard();
        } else if (tabName === 'players') {
            refreshPlayers();
        } else if (tabName === 'map') {
            refreshMap();
        } else if (tabName === 'admin') {
            // Фокусируемся на поле пароля при открытии вкладки Admin
            const passwordInput = document.getElementById('adminPassword');
            if (passwordInput) {
                setTimeout(() => passwordInput.focus(), 100);
            }
        }
    });
});

// Обновление дашборда
async function refreshDashboard() {
    try {
        const response = await fetch(`${API_BASE}/server-info`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            const statusDot = document.querySelector('.status-dot');
            
            // Обновление статуса
            statusDot.classList.add('online');
            statusDot.classList.remove('offline');
            document.querySelector('#statusIndicator span:last-child').textContent = 'Онлайн';
            
            // Обновление статистики
            // Проверяем разные возможные структуры данных
            let playersCount = 0;
            if (data.players_count !== undefined) {
                playersCount = data.players_count;
            } else if (data.players && Array.isArray(data.players)) {
                playersCount = data.players.length;
            } else if (data.info && data.info.currentPlayers !== undefined) {
                playersCount = data.info.currentPlayers;
            }
            
            document.getElementById('playersCount').textContent = playersCount;
            
            // FPS - используем serverfps из метрик
            const fps = data.metrics?.serverfps || 
                       data.metrics?.fps || 
                       data.metrics?.serverFPS || 
                       data.metrics?.currentFPS ||
                       data.info?.fps ||
                       '-';
            document.getElementById('fps').textContent = typeof fps === 'number' ? fps.toFixed(1) : fps;
            
            // Uptime
            const uptime = data.metrics?.uptime || 
                          data.metrics?.serverUptime ||
                          data.info?.uptime;
            document.getElementById('uptime').textContent = formatUptime(uptime);
            
            // Обновление информации о сервере
            // Название - используем servername из info
            const serverName = data.info?.servername || 
                             data.info?.name || 
                             data.info?.serverName || 
                             '-';
            document.getElementById('serverName').textContent = serverName;
            
            document.getElementById('serverVersion').textContent = data.info?.version || '-';
            document.getElementById('serverDescription').textContent = data.info?.description || 
                                                                      data.info?.message || 
                                                                      '-';
        } else {
            throw new Error(result.error || 'Ошибка получения данных');
        }
    } catch (error) {
        console.error('Ошибка при обновлении дашборда:', error);
        const statusDot = document.querySelector('.status-dot');
        statusDot.classList.add('offline');
        statusDot.classList.remove('online');
        document.querySelector('#statusIndicator span:last-child').textContent = 'Офлайн';
        showToast('Ошибка подключения к серверу', 'error');
    }
}

// Обновление списка игроков
async function refreshPlayers() {
    const playersList = document.getElementById('playersList');
    playersList.innerHTML = '<div class="loading">Загрузка игроков...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/players`);
        const result = await response.json();
        
        if (result.success) {
            let players = result.data || [];
            
            // Обработка разных форматов ответа
            if (typeof players === 'object' && !Array.isArray(players)) {
                if (players.players) {
                    players = players.players;
                } else if (players.data) {
                    players = players.data;
                } else {
                    players = Object.values(players);
                }
            }
            
            if (!Array.isArray(players)) {
                players = [];
            }
            
            if (players.length === 0) {
                playersList.innerHTML = '<div class="empty-state">На сервере нет игроков</div>';
            } else {
                playersList.innerHTML = players.map(player => {
                    // Обработка разных форматов данных игрока
                    const playerName = player.name || 
                                     player.playerName || 
                                     player.username || 
                                     'Unknown';
                    const playerId = player.playerId || 
                                    player.userId || 
                                    player.steamId || 
                                    player.id || 
                                    'N/A';
                    
                    // Показываем кнопки управления только для администратора
                    const adminButtons = isAdmin ? `
                        <div class="player-actions admin-only">
                            <button class="btn-small btn-kick" onclick="kickPlayer('${playerId}')">Kick</button>
                            <button class="btn-small btn-ban" onclick="banPlayer('${playerId}')">Ban</button>
                        </div>
                    ` : '';
                    
                    return `
                        <div class="player-item">
                            <div class="player-info">
                                <div class="player-name">${escapeHtml(playerName)}</div>
                                <div class="player-id">ID: ${playerId}</div>
                            </div>
                            ${adminButtons}
                        </div>
                    `;
                }).join('');
            }
        } else {
            throw new Error(result.error || 'Ошибка получения данных');
        }
    } catch (error) {
        console.error('Ошибка при обновлении списка игроков:', error);
        playersList.innerHTML = '<div class="empty-state">Ошибка загрузки игроков</div>';
        showToast('Ошибка загрузки игроков', 'error');
    }
}

// Отправка объявления
async function sendAnnounce() {
    const message = document.getElementById('announceMessage').value.trim();
    
    if (!message) {
        showToast('Введите текст объявления', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/announce`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Объявление отправлено');
            document.getElementById('announceMessage').value = '';
        } else {
            throw new Error(result.error || 'Ошибка отправки');
        }
    } catch (error) {
        console.error('Ошибка при отправке объявления:', error);
        showToast('Ошибка отправки объявления', 'error');
    }
}

// Сохранение мира
async function saveWorld() {
    if (!confirm('Сохранить мир?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/save`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Мир сохранён');
        } else {
            throw new Error(result.error || 'Ошибка сохранения');
        }
    } catch (error) {
        console.error('Ошибка при сохранении мира:', error);
        showToast('Ошибка сохранения мира', 'error');
    }
}

// Остановка сервера
async function shutdownServer() {
    const waittime = parseInt(document.getElementById('shutdownWaitTime').value) || 10;
    const message = document.getElementById('shutdownMessage').value || '';
    
    if (!confirm(`Остановить сервер через ${waittime} секунд?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/shutdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ waittime, message })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`Сервер будет остановлен через ${waittime} секунд`);
        } else {
            throw new Error(result.error || 'Ошибка остановки');
        }
    } catch (error) {
        console.error('Ошибка при остановке сервера:', error);
        showToast('Ошибка остановки сервера', 'error');
    }
}

// Принудительная остановка сервера
async function forceStopServer() {
    if (!confirm('⚠️ ВНИМАНИЕ: Это немедленно остановит сервер без сохранения!\n\nВы уверены?')) return;
    
    try {
        // Примечание: В текущей версии API нет отдельного endpoint для force stop через REST API
        // Используем shutdown с минимальным временем ожидания
        const response = await fetch(`${API_BASE}/shutdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ waittime: 1, message: 'Принудительная остановка сервера' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Сервер принудительно остановлен');
        } else {
            throw new Error(result.error || 'Ошибка остановки');
        }
    } catch (error) {
        console.error('Ошибка при принудительной остановке:', error);
        showToast('Ошибка остановки сервера', 'error');
    }
}

// Переменные для автоматического выключения
let autoShutdownStatusInterval = null;

// Активация/деактивация автоматического выключения
async function toggleAutoShutdown() {
    const minutes = parseInt(document.getElementById('autoShutdownMinutes').value);
    
    if (!minutes || minutes < 1) {
        showToast('Укажите количество минут (минимум 1)', 'error');
        return;
    }
    
    try {
        // Получаем текущий статус
        const statusResponse = await fetch(`${API_BASE}/auto-shutdown/status`);
        const statusResult = await statusResponse.json();
        const isActive = statusResult.success && statusResult.data && statusResult.data.active;
        
        if (isActive) {
            // Деактивируем
            const response = await fetch(`${API_BASE}/auto-shutdown`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ active: false })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showToast('Автоматическое выключение отключено');
                updateAutoShutdownUI(false, null);
                if (autoShutdownStatusInterval) {
                    clearInterval(autoShutdownStatusInterval);
                    autoShutdownStatusInterval = null;
                }
            } else {
                throw new Error(result.error || 'Ошибка отключения');
            }
        } else {
            // Активируем
            const response = await fetch(`${API_BASE}/auto-shutdown`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ active: true, minutes: minutes })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showToast(`Автоматическое выключение активировано (${minutes} минут)`);
                updateAutoShutdownUI(true, minutes);
                // Запускаем периодическое обновление статуса
                if (autoShutdownStatusInterval) {
                    clearInterval(autoShutdownStatusInterval);
                }
                autoShutdownStatusInterval = setInterval(updateAutoShutdownStatus, 1000);
            } else {
                throw new Error(result.error || 'Ошибка активации');
            }
        }
    } catch (error) {
        console.error('Ошибка при управлении автоматическим выключением:', error);
        showToast('Ошибка управления автоматическим выключением', 'error');
    }
}

// Обновление UI автоматического выключения
function updateAutoShutdownUI(active, minutes) {
    const statusDiv = document.getElementById('autoShutdownStatus');
    const statusText = document.getElementById('autoShutdownStatusText');
    const toggleBtn = document.getElementById('autoShutdownToggle');
    const minutesInput = document.getElementById('autoShutdownMinutes');
    
    if (active) {
        statusDiv.style.display = 'block';
        statusText.textContent = 'Активно';
        toggleBtn.textContent = 'Отключить';
        toggleBtn.classList.add('btn-danger');
        toggleBtn.classList.remove('btn-primary');
        minutesInput.disabled = true;
    } else {
        statusDiv.style.display = 'none';
        toggleBtn.textContent = 'Активировать';
        toggleBtn.classList.remove('btn-danger');
        toggleBtn.classList.add('btn-primary');
        minutesInput.disabled = false;
    }
}

// Обновление статуса автоматического выключения
async function updateAutoShutdownStatus() {
    try {
        const response = await fetch(`${API_BASE}/auto-shutdown/status`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            const statusText = document.getElementById('autoShutdownStatusText');
            const timerText = document.getElementById('autoShutdownTimer');
            
            if (data.active) {
                statusText.textContent = 'Активно';
                if (data.remaining_seconds !== null && data.remaining_seconds !== undefined) {
                    const minutes = Math.floor(data.remaining_seconds / 60);
                    const seconds = data.remaining_seconds % 60;
                    timerText.textContent = `Осталось: ${minutes}:${String(seconds).padStart(2, '0')}`;
                } else {
                    timerText.textContent = 'Ожидание проверки...';
                }
                updateAutoShutdownUI(true, null);
            } else {
                updateAutoShutdownUI(false, null);
                if (autoShutdownStatusInterval) {
                    clearInterval(autoShutdownStatusInterval);
                    autoShutdownStatusInterval = null;
                }
            }
        }
    } catch (error) {
        console.error('Ошибка при обновлении статуса автоматического выключения:', error);
    }
}

// Инициализация статуса автоматического выключения при загрузке страницы
async function initAutoShutdownStatus() {
    try {
        const response = await fetch(`${API_BASE}/auto-shutdown/status`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.active) {
            updateAutoShutdownUI(true, result.data.minutes);
            if (autoShutdownStatusInterval) {
                clearInterval(autoShutdownStatusInterval);
            }
            autoShutdownStatusInterval = setInterval(updateAutoShutdownStatus, 1000);
        }
    } catch (error) {
        console.error('Ошибка при инициализации статуса автоматического выключения:', error);
    }
}

// Управление игроками
async function kickPlayer(userid) {
    if (!confirm('Выгнать этого игрока?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/kick`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ userid, message: 'Вы были исключены администратором' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Игрок исключён');
            refreshPlayers();
        } else {
            throw new Error(result.error || 'Ошибка исключения');
        }
    } catch (error) {
        console.error('Ошибка при исключении игрока:', error);
        showToast('Ошибка исключения игрока', 'error');
    }
}

async function banPlayer(userid) {
    if (!confirm('Забанить этого игрока?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/ban`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ userid })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Игрок забанен');
            refreshPlayers();
        } else {
            throw new Error(result.error || 'Ошибка бана');
        }
    } catch (error) {
        console.error('Ошибка при бане игрока:', error);
        showToast('Ошибка бана игрока', 'error');
    }
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Карта
let mapCanvas, mapCtx;
let mapPlayers = [];
let mapScale = 1; // Начальный масштаб будет вычислен автоматически при загрузке карты
let mapOffsetX = 0;
let mapOffsetY = 0;
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let dragStartOffsetX = 0;
let dragStartOffsetY = 0;
let mapImage = null;
let animationFrameId = null;
// Переменные для touch-жестов
let touchStartDistance = 0;
let touchStartScale = 1;
let touchStartCenterX = 0;
let touchStartCenterY = 0;
let touchStartOffsetX = 0;
let touchStartOffsetY = 0;
let isPinching = false;

// Инициализация карты
function initMap() {
    mapCanvas = document.getElementById('mapCanvas');
    if (!mapCanvas) return;
    
    // Скрываем canvas до полной загрузки
    mapCanvas.classList.remove('ready');
    
    mapCtx = mapCanvas.getContext('2d');
    
    // Функция для установки правильного размера canvas с учетом devicePixelRatio для улучшения качества
    const setCanvasSize = () => {
        const container = mapCanvas.parentElement;
        const containerWidth = container.clientWidth - 30;
        // Устанавливаем квадратный размер для сохранения пропорций 1:1
        const displaySize = Math.min(containerWidth, 400);
        
        // Получаем коэффициент масштабирования для высокого разрешения
        const dpr = window.devicePixelRatio || 1;
        
        // Устанавливаем внутреннее разрешение canvas (высокое качество)
        mapCanvas.width = displaySize * dpr;
        mapCanvas.height = displaySize * dpr;
        
        // Устанавливаем размер отображения (CSS размер)
        mapCanvas.style.width = displaySize + 'px';
        mapCanvas.style.height = displaySize + 'px';
        
        // Масштабируем контекст для правильной отрисовки
        // Сбрасываем трансформацию перед применением новой
        mapCtx.setTransform(1, 0, 0, 1, 0, 0);
        mapCtx.scale(dpr, dpr);
        
        // Перерисовываем карту после изменения размера
        if (mapImage && mapImage.complete) {
            drawMap();
        }
    };
    
    // Устанавливаем размер canvas сразу
    setCanvasSize();
    
    // Загрузка фонового изображения карты (сначала карта, потом игроки)
    loadMapImage();
    
    // Обработчики для масштабирования и перемещения (мышь)
    mapCanvas.addEventListener('mousedown', startDrag);
    // Используем document для mousemove, чтобы мышь могла выходить за края canvas
    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', endDrag);
    mapCanvas.addEventListener('mouseleave', endDrag);
    mapCanvas.addEventListener('wheel', onWheel);
    
    // Обработчики для touch-жестов (мобильные устройства)
    mapCanvas.addEventListener('touchstart', onTouchStart, { passive: false });
    mapCanvas.addEventListener('touchmove', onTouchMove, { passive: false });
    mapCanvas.addEventListener('touchend', onTouchEnd, { passive: false });
    mapCanvas.addEventListener('touchcancel', onTouchEnd, { passive: false });
    
    // Адаптивный размер
    window.addEventListener('resize', () => {
        if (mapCanvas) {
            setCanvasSize();
            // Перерисовываем карту после изменения размера
            if (mapImage && mapImage.complete) {
                drawMap();
            }
        }
    });
}

// Загрузка изображения карты
function loadMapImage() {
    mapImage = new Image();
    
    let extensions = ['jpg', 'png', 'jpeg'];
    let currentExt = 0;
    
    mapImage.onload = () => {
        console.log('Карта загружена:', mapImage.width, 'x', mapImage.height, 'соотношение:', (mapImage.width / mapImage.height).toFixed(2));
        console.log('Карта complete:', mapImage.complete, 'naturalWidth:', mapImage.naturalWidth, 'naturalHeight:', mapImage.naturalHeight);
        
        // Вычисляем начальный масштаб
        if (mapCanvas && mapImage.naturalWidth > 0 && mapImage.naturalHeight > 0) {
            const dpr = window.devicePixelRatio || 1;
            const container = mapCanvas.parentElement;
            if (container) {
                const containerWidth = container.clientWidth - 30;
                const displaySize = Math.min(containerWidth, 400);
                const canvasWidth = displaySize;
                const canvasHeight = displaySize;
                
                const worldMin = -1000;
                const worldMax = 1000;
                const worldSize = worldMax - worldMin;
                
                const canvasSize = Math.min(canvasWidth, canvasHeight);
                const imageSize = Math.max(mapImage.naturalWidth, mapImage.naturalHeight);
                
                mapScale = worldSize / imageSize;
                mapScale = Math.max(0.1, Math.min(5, mapScale));
                
                console.log('Начальный масштаб вычислен:', mapScale.toFixed(3));
            }
        }
        
        // Используем двойной requestAnimationFrame для гарантии правильной инициализации с devicePixelRatio
        // Это гарантирует, что браузер успел правильно определить devicePixelRatio
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                // Отрисовываем карту (drawMap всегда переустанавливает canvas с правильным devicePixelRatio)
                drawMap();
                
                // Показываем карту только после полной отрисовки с правильным качеством
                if (mapCanvas) {
                    mapCanvas.classList.add('ready');
                }
                
                // После загрузки карты загружаем игроков
                refreshMapPlayers();
            });
        });
    };
    
    mapImage.onerror = () => {
        currentExt++;
        if (currentExt < extensions.length) {
            // Пробуем следующее расширение
            console.log(`Пробуем загрузить map.${extensions[currentExt]}...`);
            mapImage.src = `/static/map.${extensions[currentExt]}`;
        } else {
            // Все расширения не сработали, используем текстуру
            console.log('Локальная карта не найдена, используется текстура');
            mapImage = null;
            drawMap();
        }
    };
    
    // Начинаем с первого расширения (jpg, так как видел map.jpg в папке)
    mapImage.src = `/static/map.${extensions[currentExt]}`;
}

function startDrag(e) {
    e.preventDefault();
    isDragging = true;
    // Получаем позицию мыши относительно canvas
    const rect = mapCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Сохраняем начальную позицию мыши в координатах canvas
    dragStartX = mouseX;
    dragStartY = mouseY;
    
    // ВАЖНО: Сохраняем текущее смещение карты ПЕРЕД любыми вычислениями
    // Это гарантирует, что мы начинаем перетаскивание с реального текущего положения
    // Используем текущие значения напрямую, без дополнительных проверок
    // НЕ вызываем drawMap() или другие функции, которые могут изменить смещение
    dragStartOffsetX = mapOffsetX;
    dragStartOffsetY = mapOffsetY;
    
    // Отладочная информация для диагностики
    console.log('startDrag - сохранено смещение:', {
        mapOffsetX: mapOffsetX.toFixed(2),
        mapOffsetY: mapOffsetY.toFixed(2),
        dragStartOffsetX: dragStartOffsetX.toFixed(2),
        dragStartOffsetY: dragStartOffsetY.toFixed(2)
    });
    
    mapCanvas.style.cursor = 'grabbing';
}

function onDrag(e) {
    if (!isDragging) return;
    e.preventDefault();
    // Получаем текущую позицию мыши относительно canvas
    const rect = mapCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Вычисляем разницу в позиции мыши от начальной точки
    const deltaX = mouseX - dragStartX;
    const deltaY = mouseY - dragStartY;
    
    // Обновляем смещение карты
    // ВАЖНО: Карта должна двигаться в том же направлении, что и мышь
    // Если мышь двигается вправо (deltaX > 0), карта должна двигаться вправо
    // В drawMap() используется: centerX = width / 2 + mapOffsetX
    // Если mapOffsetX увеличивается, centerX увеличивается, карта двигается вправо
    // Поэтому добавляем deltaX к смещению (не вычитаем)
    let newOffsetX = dragStartOffsetX + deltaX;
    let newOffsetY = dragStartOffsetY + deltaY;
    
    // УБРАНЫ ограничения границ - карта может свободно перемещаться
    // Это позволяет сохранять позицию между перетаскиваниями
    
    // Устанавливаем новое смещение (не изменяя dragStartOffsetX/Y)
    mapOffsetX = newOffsetX;
    mapOffsetY = newOffsetY;
    
    // Отладочная информация для диагностики
    if (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10) {
        console.log('onDrag - установлено смещение:', {
            deltaX: deltaX.toFixed(2),
            deltaY: deltaY.toFixed(2),
            dragStartOffsetX: dragStartOffsetX.toFixed(2),
            dragStartOffsetY: dragStartOffsetY.toFixed(2),
            newOffsetX: newOffsetX.toFixed(2),
            newOffsetY: newOffsetY.toFixed(2),
            mapOffsetX: mapOffsetX.toFixed(2),
            mapOffsetY: mapOffsetY.toFixed(2)
        });
    }
    
    // НЕ вызываем constrainMapBounds() здесь, так как ограничения уже применены выше
    // constrainMapBounds() может изменить mapOffsetX/Y, что вызовет "прыжки"
    
    drawMap();
}

function endDrag() {
    if (!isDragging) return; // Защита от повторного вызова
    
    isDragging = false;
    mapCanvas.style.cursor = 'crosshair';
    
    // Отладочная информация для диагностики
    console.log('endDrag - финальное смещение:', {
        mapOffsetX: mapOffsetX.toFixed(2),
        mapOffsetY: mapOffsetY.toFixed(2)
    });
    
    // ВАЖНО: НЕ вызываем constrainMapBounds() здесь, так как это может изменить mapOffsetX/Y
    // и вызвать "прыжки" при следующем перетаскивании
    // Ограничения границ уже применены в onDrag()
    // drawMap() уже вызван в onDrag(), не нужно вызывать снова
}

function onWheel(e) {
    e.preventDefault();
    
    // Получаем позицию курсора относительно canvas
    const rect = mapCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const dpr = window.devicePixelRatio || 1;
    const canvasWidth = mapCanvas.width / dpr;
    const canvasHeight = mapCanvas.height / dpr;
    
    // Вычисляем точку на карте под курсором (в координатах карты)
    // Это нужно, чтобы эта точка оставалась под курсором при зуме
    const centerX = canvasWidth / 2;
    const centerY = canvasHeight / 2;
    
    // Позиция курсора относительно центра canvas с учетом текущего смещения
    const pointOnMapX = mouseX - centerX - mapOffsetX;
    const pointOnMapY = mouseY - centerY - mapOffsetY;
    
    // Сохраняем старый масштаб
    const oldScale = mapScale;
    
    // Изменяем масштаб
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    mapScale = Math.max(0.1, Math.min(5, mapScale * delta));
    
    // Вычисляем новое смещение так, чтобы точка под курсором оставалась на месте
    // При изменении масштаба координаты точки на карте масштабируются
    const scaleRatio = mapScale / oldScale;
    const newPointOnMapX = pointOnMapX * scaleRatio;
    const newPointOnMapY = pointOnMapY * scaleRatio;
    
    // Обновляем смещение так, чтобы точка под курсором оставалась на месте
    mapOffsetX = mouseX - centerX - newPointOnMapX;
    mapOffsetY = mouseY - centerY - newPointOnMapY;
    
    // УБРАНЫ ограничения границ - карта может свободно перемещаться
    // constrainMapBounds();
    drawMap();
}

// Touch-жесты для мобильных устройств
function onTouchStart(e) {
    if (e.touches.length === 2) {
        // Pinch-to-zoom
        isPinching = true;
        isDragging = false;
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        touchStartDistance = Math.sqrt(
            Math.pow(touch2.clientX - touch1.clientX, 2) +
            Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        touchStartScale = mapScale;
        
        // Вычисляем центр pinch-жеста
        const rect = mapCanvas.getBoundingClientRect();
        touchStartCenterX = ((touch1.clientX + touch2.clientX) / 2) - rect.left;
        touchStartCenterY = ((touch1.clientY + touch2.clientY) / 2) - rect.top;
        
        touchStartOffsetX = mapOffsetX;
        touchStartOffsetY = mapOffsetY;
    } else if (e.touches.length === 1) {
        // Одно касание - перетаскивание
        isDragging = true;
        isPinching = false;
        const touch = e.touches[0];
        const rect = mapCanvas.getBoundingClientRect();
        dragStartX = touch.clientX - rect.left;
        dragStartY = touch.clientY - rect.top;
        dragStartOffsetX = mapOffsetX;
        dragStartOffsetY = mapOffsetY;
        mapCanvas.style.cursor = 'grabbing';
    }
    e.preventDefault();
}

function onTouchMove(e) {
    if (isPinching && e.touches.length === 2) {
        // Pinch-to-zoom
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = Math.sqrt(
            Math.pow(touch2.clientX - touch1.clientX, 2) +
            Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        
        if (touchStartDistance > 0) {
            const scaleFactor = currentDistance / touchStartDistance;
            const oldScale = mapScale;
            mapScale = Math.max(0.1, Math.min(5, touchStartScale * scaleFactor));
            
            // Вычисляем центр pinch-жеста (точка между двумя пальцами)
            const rect = mapCanvas.getBoundingClientRect();
            const pinchCenterX = ((touch1.clientX + touch2.clientX) / 2) - rect.left;
            const pinchCenterY = ((touch1.clientY + touch2.clientY) / 2) - rect.top;
            
            const dpr = window.devicePixelRatio || 1;
            const canvasWidth = mapCanvas.width / dpr;
            const canvasHeight = mapCanvas.height / dpr;
            const canvasCenterX = canvasWidth / 2;
            const canvasCenterY = canvasHeight / 2;
            
            // Точка на карте под центром pinch (относительно центра canvas с учетом текущего смещения)
            const pointOnMapX = pinchCenterX - canvasCenterX - touchStartOffsetX;
            const pointOnMapY = pinchCenterY - canvasCenterY - touchStartOffsetY;
            
            // Масштабируем точку
            const scaleRatio = mapScale / oldScale;
            const newPointOnMapX = pointOnMapX * scaleRatio;
            const newPointOnMapY = pointOnMapY * scaleRatio;
            
            // Обновляем смещение так, чтобы точка под центром pinch оставалась на месте
            mapOffsetX = pinchCenterX - canvasCenterX - newPointOnMapX;
            mapOffsetY = pinchCenterY - canvasCenterY - newPointOnMapY;
            
            drawMap();
        }
    } else if (isDragging && e.touches.length === 1) {
        // Перетаскивание одним пальцем
        const touch = e.touches[0];
        const rect = mapCanvas.getBoundingClientRect();
        const currentX = touch.clientX - rect.left;
        const currentY = touch.clientY - rect.top;
        
        const deltaX = currentX - dragStartX;
        const deltaY = currentY - dragStartY;
        
        mapOffsetX = dragStartOffsetX + deltaX;
        mapOffsetY = dragStartOffsetY + deltaY;
        
        drawMap();
    }
    e.preventDefault();
}

function onTouchEnd(e) {
    isDragging = false;
    isPinching = false;
    mapCanvas.style.cursor = 'crosshair';
    drawMap();
}

// Функции зума для кнопок
function zoomIn() {
    zoomMap(1.2);
}

function zoomOut() {
    zoomMap(0.8);
}

function zoomMap(factor) {
    const oldScale = mapScale;
    mapScale = Math.max(0.1, Math.min(5, mapScale * factor));
    
    // Зум к центру видимой области (центр canvas)
    // Используем ту же логику, что и в onTouchMove() для pinch-to-zoom
    const dpr = window.devicePixelRatio || 1;
    const canvasWidth = mapCanvas.width / dpr;
    const canvasHeight = mapCanvas.height / dpr;
    const canvasCenterX = canvasWidth / 2;
    const canvasCenterY = canvasHeight / 2;
    
    // Центр canvas (используем как центр зума, как в pinch-to-zoom)
    const zoomCenterX = canvasCenterX;
    const zoomCenterY = canvasCenterY;
    
    // Сохраняем текущее смещение (как touchStartOffsetX в onTouchMove)
    const startOffsetX = mapOffsetX;
    const startOffsetY = mapOffsetY;
    
    // Точка на карте под центром зума (относительно центра canvas с учетом текущего смещения)
    // Используем ту же формулу, что и в onTouchMove: pointOnMapX = pinchCenterX - canvasCenterX - touchStartOffsetX
    const pointOnMapX = zoomCenterX - canvasCenterX - startOffsetX;
    const pointOnMapY = zoomCenterY - canvasCenterY - startOffsetY;
    
    // Масштабируем точку
    const scaleRatio = mapScale / oldScale;
    const newPointOnMapX = pointOnMapX * scaleRatio;
    const newPointOnMapY = pointOnMapY * scaleRatio;
    
    // Обновляем смещение так, чтобы точка под центром зума оставалась на месте
    // Используем ту же формулу, что и в onTouchMove: mapOffsetX = pinchCenterX - canvasCenterX - newPointOnMapX
    mapOffsetX = zoomCenterX - canvasCenterX - newPointOnMapX;
    mapOffsetY = zoomCenterY - canvasCenterY - newPointOnMapY;
    
    drawMap();
}

// Ограничение границ карты
function constrainMapBounds() {
    if (!mapCanvas || !mapImage || !mapImage.complete) return;
    
    // ВАЖНО: НЕ вызываем эту функцию во время перетаскивания, чтобы не сбрасывать смещение
    if (isDragging) return;
    
    const dpr = window.devicePixelRatio || 1;
    const canvasWidth = mapCanvas.width / dpr;
    const canvasHeight = mapCanvas.height / dpr;
    
    const worldMin = -1000;
    const worldMax = 1000;
    const worldSize = worldMax - worldMin;
    const canvasSize = Math.min(canvasWidth, canvasHeight);
    const pixelsPerUnit = (canvasSize * mapScale) / worldSize;
    
    const imageWidth = (mapImage.naturalWidth || mapImage.width) * pixelsPerUnit;
    const imageHeight = (mapImage.naturalHeight || mapImage.height) * pixelsPerUnit;
    
    // Вычисляем границы смещения
    const centerX = canvasWidth / 2;
    const centerY = canvasHeight / 2;
    
    // Вычисляем позицию карты
    const imageX = centerX + mapOffsetX - imageWidth / 2;
    const imageY = centerY + mapOffsetY - imageHeight / 2;
    
    // Ограничиваем смещения так, чтобы карта не выходила за границы canvas
    // Левая граница: imageX не должна быть меньше 0
    if (imageX < 0) {
        mapOffsetX -= imageX;
    }
    // Правая граница: imageX + imageWidth не должна быть больше canvasWidth
    if (imageX + imageWidth > canvasWidth) {
        mapOffsetX -= (imageX + imageWidth - canvasWidth);
    }
    
    // Верхняя граница: imageY не должна быть меньше 0
    if (imageY < 0) {
        mapOffsetY -= imageY;
    }
    // Нижняя граница: imageY + imageHeight не должна быть больше canvasHeight
    if (imageY + imageHeight > canvasHeight) {
        mapOffsetY -= (imageY + imageHeight - canvasHeight);
    }
    
    // ВАЖНО: НЕ сбрасываем смещение в 0, если карта меньше canvas
    // Это вызывает "прыжки" карты в центр после каждого перетаскивания
    // Оставляем смещение как есть, чтобы карта оставалась в том же положении
}

// Отрисовка карты
function drawMap() {
    if (!mapCanvas || !mapCtx) return;
    
    // ВАЖНО: Сохраняем смещение перед отрисовкой, чтобы оно не было потеряно
    // Это гарантирует, что смещение сохраняется между перетаскиваниями
    const savedOffsetX = mapOffsetX;
    const savedOffsetY = mapOffsetY;
    
    // Убеждаемся, что canvas правильно настроен с devicePixelRatio
    const dpr = window.devicePixelRatio || 1;
    const container = mapCanvas.parentElement;
    if (container) {
        const containerWidth = container.clientWidth - 30;
        const displaySize = Math.min(containerWidth, 400);
        
        // ВСЕГДА переустанавливаем размер canvas с правильным devicePixelRatio
        // Это гарантирует правильное качество при первой загрузке
        mapCanvas.width = displaySize * dpr;
        mapCanvas.height = displaySize * dpr;
        mapCanvas.style.width = displaySize + 'px';
        mapCanvas.style.height = displaySize + 'px';
        
        // ВСЕГДА сбрасываем трансформацию и применяем scale заново
        mapCtx.setTransform(1, 0, 0, 1, 0, 0);
        mapCtx.scale(dpr, dpr);
    }
    
    // Получаем размеры в логических пикселях (после масштабирования контекста)
    const width = mapCanvas.width / dpr;
    const height = mapCanvas.height / dpr;
    
    // Очистка canvas
    mapCtx.clearRect(0, 0, width, height);
    
    // Фон карты
    // Используем фиксированный диапазон координат от -1000 до 1000
    // (координаты уже преобразованы в этот диапазон при загрузке игроков)
    const worldMin = -1000;
    const worldMax = 1000;
    const worldSize = worldMax - worldMin; // 2000
    
    if (mapImage && mapImage.complete && mapImage.naturalWidth > 0) {
        // Отрисовка фонового изображения карты
        // Сохраняем соотношение сторон 1:1 (как в оригинальном файле)
        // Карта покрывает диапазон от -1000 до 1000 по обеим осям
        
        // Вычисляем масштаб для сохранения соотношения сторон 1:1
        // Карта покрывает диапазон от -1000 до 1000 (2000 единиц по каждой оси)
        // Определяем, сколько пикселей canvas нужно для отображения всего диапазона
        const canvasSize = Math.min(width, height);
        const scale = (canvasSize * mapScale) / worldSize; // Пикселей canvas на единицу мира
        
        // Размер карты в пикселях canvas
        // Используем naturalWidth/naturalHeight для получения исходного разрешения изображения
        // Сохраняем оригинальное соотношение сторон карты (1:1)
        const imageWidth = (mapImage.naturalWidth || mapImage.width) * scale;
        const imageHeight = (mapImage.naturalHeight || mapImage.height) * scale;
        
        // Центрируем карту (центр мира в координатах 0,0)
        const centerX = width / 2 + mapOffsetX;
        const centerY = height / 2 + mapOffsetY;
        
        const imageX = centerX - imageWidth / 2;
        const imageY = centerY - imageHeight / 2;
        
        // Сохраняем контекст для обрезки
        mapCtx.save();
        mapCtx.beginPath();
        mapCtx.rect(0, 0, width, height);
        mapCtx.clip();
        
        mapCtx.drawImage(
            mapImage,
            imageX,
            imageY,
            imageWidth,
            imageHeight
        );
        
        mapCtx.restore();
    } else {
        // Если изображение не загружено, создаем детальную текстуру карты
        // Градиентный фон, имитирующий ландшафт
        const gradient = mapCtx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(0.3, '#2a2a4e');
        gradient.addColorStop(0.5, '#1a2a3e');
        gradient.addColorStop(0.7, '#2a3a4e');
        gradient.addColorStop(1, '#1a1a2e');
        mapCtx.fillStyle = gradient;
        mapCtx.fillRect(0, 0, width, height);
        
        // Добавляем текстуру, имитирующую рельеф
        mapCtx.fillStyle = 'rgba(100, 150, 200, 0.1)';
        for (let x = 0; x < width; x += 30) {
            for (let y = 0; y < height; y += 30) {
                const noise = Math.sin(x * 0.01) * Math.cos(y * 0.01) * 5;
                if (noise > 0) {
                    mapCtx.fillRect(x, y, 15, 15);
                }
            }
        }
        
        // Добавляем "береговую линию"
        mapCtx.strokeStyle = 'rgba(150, 200, 255, 0.3)';
        mapCtx.lineWidth = 2;
        for (let i = 0; i < 5; i++) {
            mapCtx.beginPath();
            const y = height / 5 * (i + 1) + Math.sin(i) * 20;
            mapCtx.moveTo(0, y);
            for (let x = 0; x < width; x += 10) {
                mapCtx.lineTo(x, y + Math.sin(x * 0.05 + i) * 15);
            }
            mapCtx.stroke();
        }
    }
    
    // Сетка координат убрана по запросу пользователя
    
    // Отрисовка игроков
    // Используем тот же диапазон координат, что и для карты (уже объявлены выше)
    const worldRange = worldSize; // Используем worldSize, который уже объявлен
    
    let mapImageX = 0;
    let mapImageY = 0;
    let mapImageWidth = 0;
    let mapImageHeight = 0;
    
    if (mapImage && mapImage.complete && mapImage.naturalWidth > 0) {
        // Сохраняем позицию и размер карты для правильного позиционирования игроков
        // Используем тот же расчет, что и для отрисовки карты
        const canvasSize = Math.min(width, height);
        // Используем ТОЧНО тот же расчет, что и в drawMap (worldSize вместо worldRange)
        const scale = (canvasSize * mapScale) / worldSize;
        
        // Используем naturalWidth/naturalHeight для получения исходного разрешения изображения
        // ТОЧНО так же, как в drawMap
        mapImageWidth = (mapImage.naturalWidth || mapImage.width) * scale;
        mapImageHeight = (mapImage.naturalHeight || mapImage.height) * scale;
        
        const centerXPlayer = width / 2 + mapOffsetX;
        const centerYPlayer = height / 2 + mapOffsetY;
        mapImageX = centerXPlayer - mapImageWidth / 2;
        mapImageY = centerYPlayer - mapImageHeight / 2;
    }
    
    mapPlayers.forEach(player => {
        if (player.location_x === undefined || player.location_y === undefined) return;
        
        // Преобразование координат мира в координаты canvas
        // Используем тот же подход, что и в palserver-online-map
        const worldToCanvas = (worldCoord, isX) => {
            if (mapImage && mapImage.complete && mapImage.naturalWidth > 0) {
                // Нормализуем координату от 0 до 1 в диапазоне мира
                // worldMin = -1000, worldMax = 1000, worldRange = 2000
                const normalized = (worldCoord - worldMin) / worldRange;
                
                // Преобразуем в координаты canvas относительно карты
                if (isX) {
                    return mapImageX + (normalized * mapImageWidth);
                } else {
                    // Y координата инвертирована (в Palworld верх = положительные Y, на canvas верх = меньшие Y)
                    // Используем (1 - normalized) для инверсии
                    return mapImageY + ((1 - normalized) * mapImageHeight);
                }
            } else {
                // Если карты нет, используем простой масштаб
                const center = isX ? width / 2 : height / 2;
                const offset = isX ? mapOffsetX : mapOffsetY;
                const scale = (isX ? width : height) / worldRange;
                return center + (worldCoord * scale) + offset;
            }
        };
        
        // Вычисляем координаты игрока на canvas
        let x = worldToCanvas(player.location_x, true);
        let y = worldToCanvas(player.location_y, false);
        
        // Корректировка позиции: смещаем пропорционально масштабу карты
        // Смещение в игровых координатах (в единицах мира), которое будет масштабироваться
        const offsetX = 2; // пикселей при масштабе 1.0
        const offsetY = 4; // пикселей при масштабе 1.0
        
        // Вычисляем масштаб для преобразования смещения
        const canvasSize = Math.min(width, height);
        const worldSize = worldMax - worldMin; // 2000
        const pixelsPerUnit = (canvasSize * mapScale) / worldSize;
        
        // Применяем смещение пропорционально масштабу
        x += offsetX * (mapScale / 1.0);
        y += offsetY * (mapScale / 1.0);
        
        // Отладочная информация (можно убрать позже)
        if (player.name && (player.name.includes('PEPE') || player.name === '.end')) {
            console.log(`Игрок ${player.name}: world(${player.location_x}, ${player.location_y}) -> canvas(${x.toFixed(1)}, ${y.toFixed(1)})`);
        }
        
        // Проверка, находится ли точка в видимой области
        if (x < -10 || x > width + 10 || y < -10 || y > height + 10) return;
        
        // Отрисовка маркера игрока (уменьшен в 3 раза)
        mapCtx.fillStyle = '#0088cc';
        mapCtx.beginPath();
        mapCtx.arc(x, y, 2, 0, Math.PI * 2);
        mapCtx.fill();
        
        // Обводка
        mapCtx.strokeStyle = '#ffffff';
        mapCtx.lineWidth = 1;
        mapCtx.stroke();
        
        // Имя игрока
        if (player.name) {
            mapCtx.fillStyle = '#ffffff';
            // Размер шрифта относительно размера canvas (примерно 2.5% от ширины)
            const fontSize = Math.max(8, Math.min(12, width * 0.025));
            mapCtx.font = `${fontSize}px sans-serif`;
            mapCtx.textAlign = 'center';
            // Уменьшаем расстояние между точкой и ником
            const textOffset = fontSize + 1;
            mapCtx.fillText(player.name, x, y - textOffset);
        }
    });
    
    // Информация об игроках
    // Размер шрифта относительно размера canvas (примерно 2% от ширины)
    const infoFontSize = Math.max(8, Math.min(11, width * 0.02));
    // Используем одинаковый отступ со всех сторон (как нижний)
    const infoPadding = infoFontSize;
    
    // Измеряем ширину текста для правильного размера фона
    mapCtx.font = `${infoFontSize}px sans-serif`;
    mapCtx.textAlign = 'left';
    const text = `Игроков: ${mapPlayers.length}`;
    const textWidth = mapCtx.measureText(text).width;
    
    // Вычисляем размеры фона на основе реальной ширины текста
    // Добавляем одинаковые отступы со всех сторон
    const infoWidth = textWidth + infoPadding * 2;
    const infoHeight = infoFontSize + infoPadding * 2;
    
    // Позиция фона с одинаковыми отступами со всех сторон
    const infoX = infoPadding;
    const infoY = height - infoHeight - infoPadding;
    
    mapCtx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    mapCtx.fillRect(infoX, infoY, infoWidth, infoHeight);
    mapCtx.fillStyle = '#ffffff';
    // Текст позиционируется с учетом одинаковых отступов
    mapCtx.fillText(text, infoX + infoPadding, infoY + infoFontSize + infoPadding);
    
    // ВАЖНО: Восстанавливаем смещение после отрисовки, чтобы оно не было потеряно
    // Это гарантирует, что смещение сохраняется между перетаскиваниями
    mapOffsetX = savedOffsetX;
    mapOffsetY = savedOffsetY;
}

// Загрузка игроков для карты (вызывается после загрузки карты)
async function refreshMapPlayers() {
    const mapInfo = document.getElementById('mapInfo');
    if (mapInfo) {
        mapInfo.innerHTML = '<div class="loading">Загрузка игроков...</div>';
    }
    
    try {
        const response = await fetch(`${API_BASE}/players`);
        const result = await response.json();
        
        if (result.success) {
            let players = result.data || [];
            
            // Обработка разных форматов ответа
            if (typeof players === 'object' && !Array.isArray(players)) {
                if (players.players) {
                    players = players.players;
                } else if (players.data) {
                    players = players.data;
                } else {
                    players = Object.values(players);
                }
            }
            
            if (!Array.isArray(players)) {
                players = [];
            }
            
            // Фильтруем игроков с координатами и преобразуем их
            // API возвращает координаты в большом диапазоне (например, -358811), 
            // но реальные координаты в игре в диапазоне -1000 до 1000 (например, 241, -508)
            // Нужно преобразовать: делим на ~358 для получения правильного диапазона
            mapPlayers = players.filter(p => {
                if (p.location_x === undefined || p.location_y === undefined) return false;
                
                // Сохраняем оригинальные координаты для логирования
                const origX = p.location_x;
                const origY = p.location_y;
                
                // Преобразование координат из системы Unreal Engine в игровые координаты
                // Используем формулу из оригинального проекта palserver-online-map
                // Формула: x_loc = (location_y - offsetY) / scale, y_loc = (location_x + offsetX) / scale
                // Обратите внимание: X координата игрока берется из location_y API, Y координата из location_x API
                const offsetX = 123467.1611767;
                const offsetY = 157664.55791065;
                const scale = 462.962962963;
                
                // Преобразуем координаты по формуле из оригинального проекта
                // X координата игрока = (location_y - offsetY) / scale
                // Y координата игрока = (location_x + offsetX) / scale
                p.location_x = (origY - offsetY) / scale;
                p.location_y = (origX + offsetX) / scale;
                
                console.log(`Игрок ${p.name}: API координаты X:${origX.toFixed(1)}, Y:${origY.toFixed(1)} -> преобразованные X:${p.location_x.toFixed(1)}, Y:${p.location_y.toFixed(1)}`);
                
                return true;
            });
            
            // Отрисовываем карту с игроками
            // ВАЖНО: Сохраняем текущее смещение перед вызовом drawMap(), 
            // чтобы оно не было потеряно при обновлении игроков
            const savedOffsetX = mapOffsetX;
            const savedOffsetY = mapOffsetY;
            drawMap();
            // Восстанавливаем смещение после отрисовки
            mapOffsetX = savedOffsetX;
            mapOffsetY = savedOffsetY;
            
            // Обновление информации
            if (mapInfo) {
                if (mapPlayers.length === 0) {
                    mapInfo.innerHTML = '<div class="empty-state">Нет игроков с координатами на карте</div>';
                } else {
                    const playersList = mapPlayers.map(p => 
                        `${p.name || 'Unknown'} (Lv.${p.level || '?'}) - X:${Math.round(p.location_x)}, Y:${Math.round(p.location_y)}`
                    ).join('<br>');
                    mapInfo.innerHTML = `<div style="font-size: 11px; line-height: 1.6;">${playersList}</div>`;
                }
            }
        } else {
            throw new Error(result.error || 'Ошибка получения данных');
        }
    } catch (error) {
        console.error('Ошибка при загрузке игроков:', error);
        if (mapInfo) {
            mapInfo.innerHTML = '<div class="empty-state">Ошибка загрузки игроков</div>';
        }
        showToast('Ошибка загрузки игроков', 'error');
    }
}

// Обновление карты (публичная функция)
async function refreshMap() {
    // Инициализация карты, если еще не инициализирована
    if (!mapCanvas) {
        initMap();
    } else {
        // Если карта уже загружена, просто обновляем игроков
        if (mapImage && mapImage.complete) {
            await refreshMapPlayers();
        } else {
            // Если карта еще загружается, ждем её загрузки
            const checkImage = setInterval(() => {
                if (mapImage && mapImage.complete) {
                    clearInterval(checkImage);
                    refreshMapPlayers();
                }
            }, 100);
        }
    }
}


// Автообновление дашборда каждые 30 секунд
setInterval(() => {
    if (document.getElementById('dashboard').classList.contains('active')) {
        refreshDashboard();
    } else if (document.getElementById('map').classList.contains('active')) {
        refreshMap();
    }
}, 30000);

// Загрузка данных при открытии
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем права доступа администратора при загрузке страницы
    checkAdminAccess();
    
    refreshDashboard();
    initMap();
    initAutoShutdownStatus();
});

