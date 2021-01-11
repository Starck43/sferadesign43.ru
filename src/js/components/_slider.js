/*
* Формирование слайдера на страницах: exhibition_detail.html и portfolio_detail.html
*/
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

			// Показывать оверлей со слайдером для десктопных экранов или для всех, если это фото с выставки
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
