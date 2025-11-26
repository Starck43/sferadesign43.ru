import imagesLoaded from 'imagesloaded';
import Isotope from 'isotope-layout';
import { initComponents } from './components/init.js';
import { lazyloadInit } from './utils/lazyload.js';


document.addEventListener("DOMContentLoaded", () => {
    // Инициализация компонентов
    initComponents();
    lazyloadInit();

    // Настройка высоты контента
    const header = document.getElementById('header');
    const content = document.getElementById('content');
    if (header && content) {
        content.style.minHeight = `calc(100vh - ${header.clientHeight}px)`;
    }

    const container = document.querySelector('.masonry-portfolio');
    if (!container) return;

    let grid;

    // Инициализация Isotope после загрузки изображений
    imagesLoaded(container, () => {
        grid = new Isotope(container, {
            itemSelector: '.grid-item',
            columnWidth: '.grid-sizer',
            gutter: '.gutter-sizer',
            percentPosition: true,
            visibleStyle: { transform: 'translateY(0)', opacity: 1 },
            hiddenStyle: { transform: 'translateY(100px)', opacity: 0 },
        });
    }).on("always", () => {
        container?.classList.add('loaded');
    });

    // Обработка кликов по кнопкам фильтрации
    const filtersElem = document.querySelector('.filters-group');
    if (filtersElem) {
        filtersElem.addEventListener('click', (event) => {
            if (!event.target.matches('button')) return;

            const filterValue = event.target.getAttribute('data-filter');
            if (grid) {
                grid.arrange({ filter: filterValue });
            }
        });
    }

    // Управление активной кнопкой в группах фильтров
    const buttonGroups = document.querySelectorAll('.button-group');
    buttonGroups.forEach((buttonGroup) => {
        radioButtonGroup(buttonGroup, filtersElem);
    });

    /**
     * Обработка группы кнопок как радио-кнопок
     */
    function radioButtonGroup(buttonGroup, filtersElem) {
        buttonGroup.addEventListener('click', (e) => {
            if (!e.target.matches('button')) return;

            const checkedButton = filtersElem?.querySelector('.is-checked');
            checkedButton?.classList.remove('is-checked');
            e.target.classList.add('is-checked');
        });
    }
});
