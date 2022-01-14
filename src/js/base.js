
// Проверка появления элемента в видимой области экрана
function isInViewport(el, onlyVisible=false, fullInView=false) {
	if (onlyVisible && (el.style.visibility == 'hidden' || el.style.display == 'none')) return false;

	const {top:t, bottom:b, height:h} = el.getBoundingClientRect();
	if (fullInView){
		return (
			t >= 0 &&
			b <= (window.innerHeight || document.documentElement.clientHeight)
		);
	} else {
		return (t <= window.innerHeight && t + h >= 0);
	}

}

function toggleNavItems(link) {
	link && link.forEach( (e) => {
		if (window.innerWidth < 992) {
			( e.classList.contains('dropdown-toggle')) && e.classList.remove('hidden');
			(!e.classList.contains('dropdown-toggle')) && e.classList.add('hidden');
		} else {
			( e.classList.contains('dropdown-toggle')) && e.classList.add('hidden');
			(!e.classList.contains('dropdown-toggle')) && e.classList.remove('hidden');
		}
	});
}

// Вычисление высоты верхнего блока навигации
function navbarOffset(elem) {
	// Добавим смещение следущему после меню элементу
	if (!elem.classList.contains('expanded')) {
		elem.nextElementSibling.style.marginTop = elem.clientHeight + 'px';
	}
}

 // Скролинг с позиционированием элемента вверху экрана
function scroll2Top(pos, offset=0) {
	window.scrollTo({
		top: (pos + window.scrollY - offset),
		behavior: "smooth"
	});
}


document.addEventListener("DOMContentLoaded", function() {
	const burger = document.querySelector('.navbar-toggler');
	const navbar = document.querySelector('nav.navbar');

	navbarOffset(navbar);

	if ('loading' in HTMLImageElement.prototype) {
		var images = document.querySelectorAll("img");
		const desktop = document.querySelector('html').classList.contains('desktop');
		images.forEach(img => {
			var preserveLazyload = (img.classList.contains('image-img') && desktop);
			if (!preserveLazyload) {
				if (img.dataset.src) 	img.removeAttribute('data-src');
				if (img.dataset.srcset) img.removeAttribute('data-srcset');
				if (! img.classList.contains('lasyloaded')) img.classList.add('lazyloaded');
				img.classList.remove('lazyload');
			}
		});
	}

	const loadingElements = document.body.querySelectorAll('.loading');
	loadingElements.forEach( function(item) {

		item.classList.remove('loading');
		item.classList.add('loaded');
	});

	//обработаем нажатие на '+/-' у заголовка групп фильтрации checkbox для размертывания/свертывания
	const collapsedBlock = document.querySelectorAll('.collapsed')
	collapsedBlock.forEach( (item) => {
		item.addEventListener('click', (e) => {

			if (e.currentTarget.classList.contains('collapsed')) {
				e.currentTarget.classList.remove('collapsed');
				e.currentTarget.classList.add('expanded');
			} else
			if (e.currentTarget.classList.contains('expanded')) {
				e.currentTarget.classList.remove('expanded');
				e.currentTarget.classList.add('collapsed');
			}
		}, {passive: true});
	});


	// Сворачивание мобильного меню по нажатию вне области его контейнера
	burger.addEventListener('click', function (e) {
		const container = document.querySelector('.container');
		var navbarNavDropdown =  document.querySelector('.navbar-collapse');

		if (container && (this.getAttribute('aria-expanded') == "true" || this.ariaExpanded == "true")) {
			document.body.classList.add('modal-open');
			this.parentNode.parentNode.classList.add('expanded');
			navbarNavDropdown.style.maxHeight = navbarNavDropdown.scrollHeight + 'px';
			container.addEventListener('click', containerListener, false);
		}
		if (container && (this.getAttribute('aria-expanded') == "false" || this.ariaExpanded == "false")) {
			document.body.classList.remove('modal-open');
			this.parentNode.parentNode.classList.remove('expanded');
			navbarNavDropdown.style.maxHeight = 0;
			container.removeEventListener('click', containerListener, false);
		}
	}, {passive: true});

	var containerListener = function(e) {
		burger.click();
	}

	// Обработчик нажатия на кнопу поиска
	const searchContainer = document.querySelector('#searchContainer');
	const searchInput = searchContainer.querySelector('[type=search]');
	const clearInput = searchContainer.querySelector('.clear-input');
	const searchLink = document.querySelectorAll('.nav-search-link');
	searchLink.forEach( (item) => {
		item.addEventListener('click', (e) => {
			e.preventDefault();

			searchContainer.classList.toggle('active');
			if (searchContainer.classList.contains('active')) {
				if (searchInput.value) {
					clearInput.classList.add('show');
				}
				searchInput.focus();
			} else
				searchInput.blur();
		});
	});

	// Обработчик очистки содержимого поля для текста
	clearInput.addEventListener('click', (e) => {
		searchInput.value = '';
		searchInput.focus();
		e.target.classList.remove('show');
	});
	// Обработчик нажатия на строку поиска в меню
	searchInput.addEventListener('input', (e) => {
		var input = this.activeElement;
		if (input.textLength > 0 && ! clearInput.classList.contains('show')) {
			clearInput.classList.add('show');
		}
		if (input.textLength == 0 &&  clearInput.classList.contains('show')) {
			clearInput.classList.remove('show');
		}
	});


	const exhibitionsLink = document.querySelectorAll('.exh-nav-item .nav-link');
	(window.innerWidth >= 992) && toggleNavItems(exhibitionsLink);

	window.addEventListener('resize', function(){
		navbarOffset(navbar);
		toggleNavItems(exhibitionsLink);
		if (window.innerWidth >= 992) {
			burger.classList.contains('collapsed') && burger.classList.remove('collapsed');
			if (burger.getAttribute('aria-expanded') == 'true' && document.body.classList.contains('modal-open')) {
				document.body.classList.remove('modal-open');
			}
			document.body.classList.remove('modal-open');
			burger.nextElementSibling.style.maxHeight = '';
		} else {
			if (burger.getAttribute('aria-expanded') == 'false' && document.body.classList.contains('modal-open')) {
				document.body.classList.remove('modal-open');
			} else
			if (burger.getAttribute('aria-expanded') == 'true' && !document.body.classList.contains('modal-open')) {
				document.body.classList.add('modal-open');
			}
		}
	});

	document.onkeydown = function(e) { // закрытие окна поиска по клавише escape
		e = e || window.event;
		(e.keyCode == 27) && searchContainer.classList.remove('active');
	};


	// обработчик раскрытия всего содержимого при нажатии на кнопку "Читать далее" при наличии блока описания
	const excerptBlock = document.querySelector('.description');
	if (excerptBlock) {
		var excerptBlock_h = excerptBlock.scrollHeight;
		if (excerptBlock_h/300 > 1.2) {
			//excerptBlock.style.height = (excerptBlock_h+30) + 'px';
			let div = document.createElement('a');
			div.className = "read-more-link";
			//div.innerHTML = "Read more";
			excerptBlock.append(div);
			excerptBlock.classList.add('brief');
		}

		excerptBlock.lastElementChild && excerptBlock.lastElementChild.addEventListener('click', (e) => {
			//var parentBlock = e.target.parentNode;
			excerptBlock.classList.toggle('brief');
			excerptBlock_h = excerptBlock.scrollHeight + 30;
			excerptBlock.style.height = ((excerptBlock.classList.contains('brief')) ? 300 : excerptBlock_h) + 'px';
		});
	}


	var siteFooter = document.querySelector('#site-footer');
	var toTopLink = document.querySelector('#back2top');
	document.onscroll = function(e) { // закрытие окна поиска по скролу
		searchContainer.classList.contains('active') && searchContainer.classList.remove('active');
		if (toTopLink) {
			if (window.pageYOffset <= window.innerHeight - navbar.clientHeight) {
				if (! toTopLink.classList.contains('disable')) {
					toTopLink.classList.add('disable');
					toTopLink.style.transform = `translateY(${siteFooter.clientHeight*2}px)`;
				}
			} else
				if (toTopLink.classList.contains('disable')) {
					toTopLink.classList.remove('disable');
					toTopLink.style.transform = `translateY(${-siteFooter.clientHeight}px)`;
				}
		}
	};

	toTopLink.addEventListener('click', function (e) {
		e.preventDefault();
		scroll2Top(-window.scrollY, navbar.clientHeight); // скролл вверх ло блока навигации
	});

	//= components/_sidebar.js


});