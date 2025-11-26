/**
 * Offcanvas component - sliding side panel
 */
import {OverlayFactory} from "./overlay.js";

export class Offcanvas {
    constructor(offcanvasSelector) {
        this.offcanvas = typeof offcanvasSelector === 'string'
            ? document.querySelector(offcanvasSelector)
            : offcanvasSelector;

        if (!this.offcanvas) return;

        // Используем OverlayFactory для создания универсального overlay
        this.overlay = OverlayFactory.offcanvas(this.offcanvas);

        this.isOpen = false;
        this.closeHandlers = [];

        this.init();
    }

    init() {
        // Find close buttons
        const closeBtns = this.offcanvas.querySelectorAll('[data-dismiss="offcanvas"]');
        closeBtns.forEach(btn => {
            const handler = (e) => {
                e.preventDefault();
                this.hide();
            };
            btn.addEventListener('click', handler);
            this.closeHandlers.push({element: btn, handler, type: 'click'});
        });

        // Close on ESC key
        const escHandler = (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.hide();
            }
        };
        document.addEventListener('keydown', escHandler);
        this.closeHandlers.push({element: document, handler: escHandler, type: 'keydown'});
    }

    show() {
        this.overlay.show();
        this.isOpen = true;
    }

    hide() {
        this.overlay.hide();
        this.isOpen = false;
    }

    toggle() {
        this.overlay.toggle();
        this.isOpen = !this.isOpen;
    }

    destroy() {
        this.closeHandlers.forEach(({element, handler, type}) => {
            element.removeEventListener(type, handler);
        });
        this.closeHandlers = [];

        this.overlay.destroy();
    }
}

/**
 * Глобальная функция для очистки backdrop при уходе со страницы
 */
export function cleanupOffcanvasBackdrop() {
    const backdrop = document.querySelector('.offcanvas-backdrop');
    if (backdrop && backdrop.parentNode) {
        backdrop.parentNode.removeChild(backdrop);
    }
    delete window.offcanvasBackdrop;
}
