/**
 * Collapse component - toggle visibility of content sections
 */

export class Collapse {
    constructor(element) {
        this.element = element;
        this.isAnimating = false;
        this.isShown = element.classList.contains('show');
    }

    toggle() {
        if (this.isShown) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        if (this.isAnimating || this.isShown) return;

        this.isAnimating = true;
        this.element.style.height = '0';
        this.element.classList.remove('collapse');
        this.element.classList.add('collapsing');
        
        const height = this.element.scrollHeight;
        
        requestAnimationFrame(() => {
            this.element.style.height = height + 'px';
        });

        const onTransitionEnd = () => {
            this.element.removeEventListener('transitionend', onTransitionEnd);
            this.element.classList.remove('collapsing');
            this.element.classList.add('collapse', 'show');
            this.element.style.height = '';
            this.isAnimating = false;
            this.isShown = true;
        };

        this.element.addEventListener('transitionend', onTransitionEnd);
    }

    hide() {
        if (this.isAnimating || !this.isShown) return;

        this.isAnimating = true;
        this.element.style.height = this.element.scrollHeight + 'px';
        
        requestAnimationFrame(() => {
            this.element.classList.remove('collapse', 'show');
            this.element.classList.add('collapsing');
            
            requestAnimationFrame(() => {
                this.element.style.height = '0';
            });
        });

        const onTransitionEnd = () => {
            this.element.removeEventListener('transitionend', onTransitionEnd);
            this.element.classList.remove('collapsing');
            this.element.classList.add('collapse');
            this.element.style.height = '';
            this.isAnimating = false;
            this.isShown = false;
        };

        this.element.addEventListener('transitionend', onTransitionEnd);
    }
}
