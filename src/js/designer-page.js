//=require ../plugins/peppermint/peppermint.js

document.addEventListener("DOMContentLoaded", function() {

	const searchContainer = null;
	const offcanvas = document.getElementById('navbarNavDropdown');
	var navbarMenu = bootstrap.Offcanvas.getInstance(offcanvas);
	if (!navbarMenu) navbarMenu = new bootstrap.Offcanvas(offcanvas);

	//=include components/_init.js
	//=include components/_lazyLoad.js
	lazyloadInit();
	//=include components/_ajax.js
	//=include components/_alert.js
	//=include components/_sendMessage.js

	const navLinks = document.querySelectorAll('a.nav-link');
	navLinks.forEach( (item) => {
		item.addEventListener('click', (e) => {
			navbarMenu.hide();
		});
	});

	const container = document.querySelector('.peppermint');
	const slidesContainer = container.querySelector('.portfolio-slides');
	var slidesCount = slidesContainer.childElementCount || null;
	var slider = null;

	if ( slidesCount == null || slidesCount == 1 || (window.innerWidth > 576 && slidesCount == 2) || (window.innerWidth > 1200 && slidesCount == 3) ) {
		//container.classList.add('two-slides');
		container.classList.remove('peppermint', 'peppermint-inactive');
	}
	else
	{
		slider = Peppermint( container, {
			dots: true,
			//touchSpeed: 300,
			speed: Math.round(window.innerWidth/0.8),
			slideshow: true,
			slideshowInterval: 5000,
			stopSlideshowAfterInteraction: true,
			startSlide: 0,
			disableIfOneSlide: true,
			slidesContainer: slidesContainer,
			onSetup: function(n) {
				const rightArrow = container.querySelector('.arrow-right');
				const leftArrow = container.querySelector('.arrow-left');
				rightArrow && rightArrow.addEventListener('click', slider.next, false);
				leftArrow && leftArrow.addEventListener('click', slider.prev, false);
				if ((window.innerWidth > 576 && window.innerWidth <= 1200 && slidesCount > 2) ||
					(window.innerWidth > 1200 && slidesCount > 3)) {
					slider.slideTo(1);
				}
			},
			onSlideChange: function(index) {
				if ((window.innerWidth > 576 && window.innerWidth <= 1200 && slidesCount < 4) ||
					(window.innerWidth > 1200 && slidesCount < 5)) {
					slider.stop();
				}
			}
		});

		if (slider) {
			window.addEventListener('resize', function(){
				slider.recalcWidth();
			});
		}
	}


});
