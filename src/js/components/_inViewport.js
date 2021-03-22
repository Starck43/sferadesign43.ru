
	// Изменение статуса изображений при появлении их в видимой области экрана
	var images = document.querySelectorAll("img.image-img.lazyload");
	inViewport = function(){
		if (images.length == 0) {
			document.removeEventListener('scroll', inViewport);
		}
		else {
			var loaded = false;
			images.forEach(img => {
				if (isInViewport(img)) {
					loaded = true;
					img.classList.add('lazyloaded');
					img.classList.remove('lazyload');
					if (img.dataset.src) 	img.removeAttribute('data-src');
					if (img.dataset.srcset) img.removeAttribute('data-srcset');
				}
			});
			// если изображения появились в видимой области, то создадим список оставшихся не загруженных элементов
			if (loaded) images = document.querySelectorAll("img.image-img.lazyload");
		}
	}

	document.addEventListener('scroll', inViewport);
	inViewport(); // Инициализация функции



