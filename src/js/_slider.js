
// ../plugins/img-touch-canvas/img-touch-zoom.js
// ../plugins/peppermint/peppermint.js


document.addEventListener("DOMContentLoaded", function() {

/*	var elem = document.querySelector('.grid');
	var msnry = new Masonry( elem, {
			// options
			itemSelector: '.grid-item',
			columnWidth: 200
	});

	// element argument can be a selector string
	//   for an individual element
	var msnry = new Masonry( '.grid', {
	  // options
	});
*/
	const overlay = document.querySelector('#overlay');
	const portfolio = document.querySelectorAll('.portfolio .image-link');
	const portfolioArray = Array.prototype.slice.call(portfolio);
	var zoom, slider = null;
	var imageIndex,lastImageIndex = 0;
	var ontouchPosY = null; // remember Y position on touch start
	var gesturableImg = null;


	portfolio.forEach( (link) => {

		link.addEventListener('click', (e) => {
			e.preventDefault();
			e.stopImmediatePropagation();

			imageIndex = portfolioArray.indexOf(e.currentTarget);
			if (imageIndex > -1) {
				slider && slider.slideTo(imageIndex,0);
				overlay.classList.add('show');
				document.body.classList.add('modal-open');
			}

			if (is_mobile) {
				if (zoom && lastImageIndex != imageIndex){
					const canvas = overlay.querySelector('canvas');
					canvas.remove();
					zoom = null;
				}
				if (zoom == null){
					zoom = new Zoomage({
						container: overlay,
						maxZoom: 2,
						minZoom: 0.5,
						//enableGestureRotate: false,
						enableDesktop: true,
						dbclickZoomThreshold: 0.2,
					});
					var img = document.getElementById('image-'+imageIndex).parentNode.parentNode.href;
					zoom.load(img);

					var portfolioImg = document.getElementById('image-'+imageIndex).parentNode.parentNode.href;
					var zoomImg = document.createElement('canvas');
					zoomImg.id = 'canvas';
					zoomImg.style.width = '100%';
					zoomImg.style.height = '100%';
					overlay.prepend(zoomImg);

					zoom = new ImgTouchCanvas({
						canvas: zoomImg,
						path: portfolioImg,
						desktop: true
					});
				}

				overlay.classList.add('zoom-container');
			}
		});

	});

	if ( !is_mobile ) {
		overlay.classList.add('slider-container', 'peppermint', 'peppermint-inactive');
		slider = Peppermint( overlay, {
			dots: true,
	/*		slideshow: false,
			speed: 600,
			slideshowInterval: 5000,
			stopSlideshowAfterInteraction: true,*/
			//slide number to start with
			startSlide: imageIndex,
			disableIfOneSlide: false,
			slidesContainer: overlay.querySelector('.slides-block'),
			onSetup: function(n) {
				if (n > 1) {
					const rightArrow = document.querySelector('#arrow-right');
					const leftArrow = document.querySelector('#arrow-left');
					rightArrow.addEventListener('click', slider.next, false); //клик по `#rightArrow` переключит на следующий слайд
					leftArrow.addEventListener('click', slider.prev, false); //клик по `#leftArrow` переключит на предыдущий слайд
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

	closeOverlay = function(overlay) {
		lastImageIndex = imageIndex;
		overlay.classList.remove('show');
		document.body.classList.remove('modal-open');
	}

});
