/**
 * Отправка AJAX запроса
 * @param {string} url - URL для запроса
 * @param {string} params - параметры запроса
 * @param {string} method - метод запроса
 * @param {Function} renderFunc - функция для рендеринга результата
 * @param {HTMLElement} alertModal - модальное окно для отображения ошибок
 */
export function ajaxSend(url, params = '', method = 'post', renderFunc = defaultRender, alertModal = null) {
    // Формируем URL для GET запросов
    const requestUrl = method.toLowerCase() === 'get' ? `${url}?${params}` : url;

    // Конфигурация запроса
    const requestConfig = {
        method: method,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    };

    // Для POST запросов добавляем тело
    if (method.toLowerCase() === 'post') {
        requestConfig.headers['Content-Type'] = 'application/x-www-form-urlencoded';
        requestConfig.body = params;
    }

    // Отправляем запрос
    fetch(requestUrl, requestConfig)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(json => {
            if (typeof renderFunc === 'function') {
                console.log('📞 Calling render function');
                renderFunc(json);
            } else {
                console.warn('❌ Render function not provided');
                defaultRender(json);
            }
        })
        .catch((error) => {
            console.error('AJAX Error:', error);
            handleAjaxError(error, alertModal);
        });
}

/**
 * Обработчик ошибок AJAX
 */
function handleAjaxError(error, alertModal = null) {
    const errorMessage = getErrorMessage(error);

    if (alertModal) {
        // Используем переданное модальное окно для ошибок
        const alertBlock = alertModal.querySelector('.message-status');
        if (alertBlock) {
            alertBlock.classList.add('error');
            alertBlock.textContent = errorMessage;
        }
    } else {
        // Используем глобальную систему уведомлений
        showGlobalError(errorMessage);
    }
}

/**
 * Получение понятного сообщения об ошибке
 */
function getErrorMessage(error) {
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        return 'Ошибка сети: невозможно подключиться к серверу';
    } else if (error.message.includes('HTTP error! status: 403')) {
        return 'У вас нет прав для этого действия';
    } else if (error.message.includes('HTTP error! status: 404')) {
        return 'Страница не найдена';
    } else if (error.message.includes('HTTP error')) {
        return `Ошибка сервера: ${error.status}`;
    } else if (error.message.includes('Доступ запрещен')) {
        return 'У вас нет прав для этого действия';
    } else {
        return error.message || 'Неизвестная ошибка';
    }
}

/**
 * Показ ошибки через глобальную систему уведомлений
 */
function showGlobalError(message) {
    if (window.Alert) {
        window.Alert.error(`<h3>Ошибка!</h3><p>${message}</p>`);
    } else {
        // Fallback: простой alert если система уведомлений не загружена
        console.error('AJAX Error:', message);
        alert(`Ошибка: ${message}`);
    }
}

/**
 * Функция по умолчанию для рендеринга
 */
function defaultRender(json) {
    console.log('AJAX Response (no render function provided):', json);

    // Если в ответе есть сообщение, показываем его
    if (json.message && window.Alert) {
        const messageType = json.status === 'error' ? 'error' : 'success';
        window.Alert[messageType]?.(json.message);
    }
}

/**
 * Утилита для создания параметров из FormData
 */
export function createFormData(formElement) {
    return new URLSearchParams(new FormData(formElement)).toString();
}

/**
 * Утилита для создания параметров из объекта
 */
export function createParamsFromObject(obj) {
    return new URLSearchParams(obj).toString();
}

