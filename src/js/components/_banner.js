/*
* Вывод баннера на странице exhibition_detail.html
*/

	var banner = document.querySelector('.banner-container');
	if (banner) {
		banner.classList.add('slider-container', 'peppermint', 'peppermint-inactive');
		banner_slider = Peppermint( banner, {
			//dots: true,
			//touchSpeed: 300,
			speed: 150,
			slideshow: true,
			slideshowInterval: 4000,
			stopSlideshowAfterInteraction: true,
			startSlide: 0,
			disableIfOneSlide: true,
			slidesContainer: document.querySelector('#banners-block'),
			onSetup: function(n) {
				if (n > 1 && !is_mobile) {
					const banner_rightArrow = banner.querySelector('.arrow-right');
					const banner_leftArrow = banner.querySelector('.arrow-left');
					banner_rightArrow && banner_rightArrow.addEventListener('click', banner_slider.next, false);
					banner_leftArrow && banner_leftArrow.addEventListener('click', banner_slider.prev, false);
				}
			}
		});

	}