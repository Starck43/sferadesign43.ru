
// ../plugins/img-touch-canvas/img-touch-zoom.js


function imgLoaded(imgElement) {
	return imgElement.complete && imgElement.naturalHeight !== 0;
}

document.addEventListener("DOMContentLoaded", function() {

	const overlay = document.querySelector('#overlay');
	const portfolio = document.querySelectorAll('.image-link');
	const portfolioArray = Array.prototype.slice.call(portfolio);
	var slider = null;
	var imageIndex = 0;
	var ontouchPosY = null; // remember Y position on touch start
	var gesturableImg = null;


	portfolio.length && portfolio.forEach( (link) => {

		link.addEventListener('click', (e) => {
			e.preventDefault();
			//e.stopImmediatePropagation();

			if (!is_mobile || is_mobile && e.currentTarget.classList.contains('gallery-photo')) {
				imageIndex = portfolioArray.indexOf(e.currentTarget);
				if (imageIndex > -1) {
					slider && slider.slideTo(imageIndex,0);
					overlay.classList.add('show');
					document.body.classList.add('modal-open');
				}
			}

		});

	});


	if (portfolio.length && (!is_mobile || portfolio[0].classList.contains('gallery-photo'))) {

		overlay && overlay.classList.add('slider-container', 'peppermint', 'peppermint-inactive');
		slider = Peppermint( overlay, {
			dots: true,
			speed: 300,
			touchSpeed: 300,
	/*		slideshow: false,
			speed: 600,
			slideshowInterval: 5000,
			stopSlideshowAfterInteraction: true,*/
			//slide number to start with
			startSlide: imageIndex,
			disableIfOneSlide: false,
			slidesContainer: overlay.querySelector('#slides-block'),
			onSetup: function(n) {
				if (n > 1) {
					const slider_rightArrow = overlay.querySelector('.arrow-right');
					const slider_leftArrow = overlay.querySelector('.arrow-left');
					slider_rightArrow.addEventListener('click', slider.next, false); //клик по `#rightArrow` переключит на следующий слайд
					slider_leftArrow.addEventListener('click', slider.prev, false); //клик по `#leftArrow` переключит на предыдущий слайд
				}
				// для мобильных устройств добавим зум
				if (is_mobile) {
					Array.from(this.slidesContainer.children).forEach(function(el) {
						new PinchZoom.default(el, {
							setOffsetsOnce: true,
							draggableUnzoomed: false,
						});
					});
				}
			}
		});

	}

	var banner = document.querySelector('.banner-container');
	if (banner) {
		banner.classList.add('slider-container', 'peppermint', 'peppermint-inactive');
		banner_slider = Peppermint( banner, {
			//dots: true,
			//speed: 300,
			//touchSpeed: 300,
			slideshow: true,
			speed: 600,
			slideshowInterval: 4000,
			stopSlideshowAfterInteraction: true,
			startSlide: 0,
			//disableIfOneSlide: false,
			slidesContainer: document.querySelector('#banners-block'),
			onSetup: function(n) {
				if (n > 1 && !is_mobile) {
					const banner_rightArrow = banner.querySelector('.arrow-right');
					const banner_leftArrow = banner.querySelector('.arrow-left');
					banner_rightArrow && banner_rightArrow.addEventListener('click', banner_slider.next, false); //клик по `#rightArrow` переключит на следующий слайд
					banner_leftArrow && banner_leftArrow.addEventListener('click', banner_slider.prev, false); //клик по `#leftArrow` переключит на предыдущий слайд
				}
			}
		});

	}

	// Функции фиксации оверлея экрана при касаниях для мобильных устройств
	function disableRubberBand(event) {
		var clientY = event.targetTouches[0].clientY - ontouchPosY;
		((overlay.scrollTop === 0 && clientY > 0) || (isOverlayTotallyScrolled() && clientY < 0)) && event.preventDefault();
	}

	function isOverlayTotallyScrolled() {
		return overlay.scrollHeight - overlay.scrollTop <= overlay.clientHeight;
	}

	// скрытие окна по нажатию на close-button или на оверлей
	overlay.addEventListener('click', (e) => {
		e.preventDefault();
		(e.target.id == 'close-button' || e.target.parentNode.id == 'close-button'
		|| e.target.classList.contains('slide-wrapper') )
		&& closeOverlay(overlay);
	});

	overlay.addEventListener('touchstart', function (event) {
		if (event.targetTouches.length === 1) {
			ontouchPosY = event.targetTouches[0].clientY; // detect single touch
		}
	}, false);

	overlay.addEventListener('touchmove', function (event) {
		(event.targetTouches.length === 1) && disableRubberBand(event); // detect single touch
	}, false);

	document.onkeydown = function(e) { // закрытие оверлея по клавише escape
		e = e || window.event;
		(e.keyCode == 27) && closeOverlay(overlay);
	};

	closeOverlay = function(el) {
		el.classList.remove('show');
		document.body.classList.remove('modal-open');
	}

});
