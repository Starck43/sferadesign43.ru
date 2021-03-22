	// Update LazyLoad Images
	function lazyloadInit() {
		(async () => {
			if ('loading' in HTMLImageElement.prototype) {
				const images = document.querySelectorAll("img:not(.lazyloaded)");
				images.forEach(img => {
					if (img.dataset.src) {
						img.src = img.dataset.src;
						if (img.dataset.srcset) img.srcset = img.dataset.srcset;
					}
					if (! img.hasAttribute('loading')) img.setAttribute('loading','lazy');

					img.onload = function() {
						if (img.dataset.src) 	img.removeAttribute('data-src');
						if (img.dataset.srcset) img.removeAttribute('data-srcset');
						img.classList.add('lazyloaded');
						img.classList.remove('lazyload');
					};
				});

			} else {
				lazySizes.init();
			}
		})();
	}