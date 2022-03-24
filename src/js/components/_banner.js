	/*
	* Вывод баннера на странице exhibition_detail.html
	*/

	var container = document.querySelector('.banner-container');
	if (container) {
		var slidesCount = 0;
		container.classList.add('slider-container', 'peppermint', 'peppermint-inactive');
		var bannerSlider = Peppermint( container, {
			//dots: true,
			//touchSpeed: 300,
			speed: window.innerWidth/1.5,
			slideshow: true,
			slideshowInterval: 5000,
			stopSlideshowAfterInteraction: true,
			startSlide: 0,
			disableIfOneSlide: true,
			slidesContainer: document.querySelector('#banners-block'),
			onSetup: function(n) {
				container.classList.remove('peppermint-inactive');
				if (n > 1 && !is_mobile) {
					const banner_rightArrow = container.querySelector('.arrow-right');
					const banner_leftArrow = container.querySelector('.arrow-left');
					banner_rightArrow && banner_rightArrow.addEventListener('click', bannerSlider.next, false);
					banner_leftArrow && banner_leftArrow.addEventListener('click', bannerSlider.prev, false);
				}
			}
		});

		window.addEventListener('resize', function(){
			bannerSlider.recalcWidth();
		});
	}