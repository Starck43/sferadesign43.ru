
	// Функция проверки загрузки первого изображения
	const portfolioImages = document.querySelectorAll('.portfolio-list img');
	var preloader = document.querySelector('.portfolio-preloader');

	portfolioImages.forEach(img => {
		img.onload = function(){
			if (preloader) {
				preloader.remove();
				preloader = null;
			}
		}
	});

