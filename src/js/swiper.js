document.addEventListener('DOMContentLoaded', async () => {
    if (document.querySelector('[data-swiper-type]')) {
        const {initSliders} = await import('./components/slider.js');
        initSliders();
    }
});
