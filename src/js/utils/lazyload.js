/**
 * Инициализация lazy loading для изображений с плавным появлением
 * Использует IntersectionObserver для оптимальной производительности
 */

/**
 * Загружает изображение и добавляет класс после успешной загрузки
 */
function loadImage(img) {
    // Если уже загружено, сразу добавляем класс
    if (img.complete && img.naturalHeight !== 0) {
        img.classList.add('lazyloaded');
        img.classList.remove('lazyload');
        if (img.dataset.src) img.removeAttribute('data-src');
        if (img.dataset.srcset) img.removeAttribute('data-srcset');
        return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
        img.onload = function() {
            img.classList.add('lazyloaded');
            img.classList.remove('lazyload');
            if (img.dataset.src) img.removeAttribute('data-src');
            if (img.dataset.srcset) img.removeAttribute('data-srcset');
            resolve();
        };
        
        img.onerror = function() {
            img.classList.add('lazyerror');
            img.classList.remove('lazyload');
            console.warn('Failed to load image:', img.src || img.dataset.src);
            reject(new Error('Image load failed'));
        };
    });
}

/**
 * Инициализация изображения для загрузки
 */
function initImageLoad(img) {
    // Если есть data-src, устанавливаем его как основной src
    if (img.dataset.src) {
        if (!img.src || img.src !== img.dataset.src) {
            img.src = img.dataset.src;
        }
    }
    
    // Если есть data-srcset, устанавливаем его
    if (img.dataset.srcset) {
        if (!img.srcset || img.srcset !== img.dataset.srcset) {
            img.srcset = img.dataset.srcset;
        }
    }
    
    // Устанавливаем нативный lazy loading если браузер поддерживает
    if ('loading' in HTMLImageElement.prototype && !img.hasAttribute('loading')) {
        img.setAttribute('loading', 'lazy');
    }
    
    return loadImage(img);
}

export function lazyloadInit() {
    const images = document.querySelectorAll("img.lazyload:not(.lazyloaded)");
    
    if (images.length === 0) {
        return;
    }
    
    // Сначала обрабатываем изображения, которые уже загружены (имеют src)
    images.forEach(img => {
        if (img.src && !img.dataset.src && img.complete && img.naturalHeight !== 0) {
            img.classList.add('lazyloaded');
            img.classList.remove('lazyload');
        }
    });
    
    // Проверяем поддержку IntersectionObserver
    if ('IntersectionObserver' in window && 
        'IntersectionObserverEntry' in window && 
        'intersectionRatio' in window.IntersectionObserverEntry.prototype) {
        
        // Используем IntersectionObserver для оптимальной производительности
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.intersectionRatio > 0) {
                    const img = entry.target;
                    
                    // Начинаем загрузку когда изображение входит в viewport
                    initImageLoad(img).catch(() => {
                        // Обработка ошибки уже в loadImage
                    });
                    
                    // Прекращаем наблюдение за этим изображением
                    observer.unobserve(img);
                }
            });
        }, {
            // Загружаем изображения немного раньше чем они появятся на экране
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        // Наблюдаем за всеми изображениями
        images.forEach(img => {
            observer.observe(img);
        });
    } else {
        // Fallback: загружаем все изображения сразу
        images.forEach(img => {
            initImageLoad(img).catch(() => {
                // Обработка ошибки уже в loadImage
            });
        });
    }
}
