/**
 * Проверка появления элемента в видимой области экрана
 * @param {HTMLElement} el - элемент для проверки
 * @param {boolean} onlyVisible - проверять только видимые элементы
 * @param {boolean} fullInView - элемент должен быть полностью в области видимости
 * @returns {boolean}
 */
export function isInViewport(el, onlyVisible = false, fullInView = false) {
    if (!el) return false;
    
    if (onlyVisible && (el.style.visibility === 'hidden' || el.style.display === 'none')) {
        return false;
    }

    const { top: t, bottom: b, height: h } = el.getBoundingClientRect();
    
    if (fullInView) {
        return (
            t >= 0 &&
            b <= (window.innerHeight || document.documentElement.clientHeight)
        );
    }
    
    return (t <= window.innerHeight && t + h >= 0);
}

/**
 * Плавная прокрутка к указанной позиции
 * @param {number} pos - позиция для прокрутки
 * @param {number} offset - смещение
 */
export function smoothScroll(pos, offset = 0) {
    window.scrollTo({
        top: pos - offset,
        behavior: "smooth"
    });
}
