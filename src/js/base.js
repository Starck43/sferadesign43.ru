import {initComponents} from './components/init.js';
import {Navbar} from "./components/navbar.js";
import {AlertManager} from "./components/alert.js";

import {lazyloadInit} from './utils/lazyload.js';
import { ajaxSend } from './utils/ajax.js';

document.addEventListener("DOMContentLoaded", async () => {
    // Инициализация основных компонентов
    initComponents();

    // Navbar offcanvas инициализируется отдельно через Navbar класс
    const navbarElement = document.querySelector('.navbar');
    if (navbarElement) {
        new Navbar(navbarElement);
    }

    // Инициализация модальных окон если они есть на странице
    if (document.querySelector('.modal')) {
        // Глобальная переменная для хранения всех экземпляров модальных окон
        window.modalInstances = new Map();
        const {initModals, cleanupModals} = await import('./components/modal.js');
        initModals();
        window.addEventListener('beforeunload', cleanupModals);
    }

    // Делаем глобально доступными
    window.ajaxSend = ajaxSend;
    window.Alert = AlertManager;

    // Инициализация lazy loading для изображений
    lazyloadInit();

    // Поддержка нативного lazy loading
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll("img:not(.lazyload)");
        images.forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            }
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
                img.removeAttribute('data-srcset');
            }
            if (img.complete && img.naturalHeight !== 0) {
                img.classList.add('lazyloaded');
            }
        });
    }
});
