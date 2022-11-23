
	var scrollDown = document.querySelector('.scroll-down');
	var scrollUp = document.querySelector('#back2top');

	document.onscroll = function(e) { // закрытие окна поиска по скролу

		if (scrollDown) {
			if (window.pageYOffset >= window.innerHeight  ) {
				scrollDown.remove();
				scrollDown = null;
			}
		}

		if (scrollUp) {
			if (window.pageYOffset <= window.innerHeight) {
				if (! scrollUp.classList.contains('disable')) {
					scrollUp.classList.add('disable');
					scrollUp.style.transform = `translateY(4vh)`;
				}
			} else
				if (scrollUp.classList.contains('disable')) {
					scrollUp.classList.remove('disable');
					scrollUp.style.transform = `translateY(0)`;
				}
		}

		if (searchContainer) {
			searchContainer.classList.contains('active') && searchContainer.classList.remove('active');
		}
	};


	const loadingElements = document.querySelectorAll('.loading');
	loadingElements.forEach( function(item) {
		item.classList.remove('loading');
		item.classList.add('loaded');
	});

	 // Скролинг с позиционированием элемента вверху экрана
	function smoothScroll(pos, offset=0) {
		window.scrollTo({
			top: pos - offset, //+ window.scrollY
			behavior: "smooth"
		});
	}

	scrollUp && scrollUp.addEventListener('click', function (e) {
		e.preventDefault();
		smoothScroll(0, 0); // скролл вверх до блока навигации
	});

	scrollDown && scrollDown.addEventListener('click', function (e) {
		e.preventDefault();
		smoothScroll(0, -window.innerHeight); // скролл вниз на высоту экрана
	});
