
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

// Разворачивание/сворачивание списка с выставками в меню
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

// Переключение класса для Burger menu
function toggleBurgerMenu(elem) {
	if (window.innerWidth >= 992) {
		if (elem.classList.contains('navbar-expand-lg') && elem.classList.contains('burger-menu')) {
			elem.classList.remove('burger-menu')
		}
	} else {
		if (elem.classList.contains('navbar-expand-lg') && ! elem.classList.contains('burger-menu')) {
			elem.classList.add('burger-menu')
		}
	}
}

// Вычисление высоты блоков навигации, заголовка, и контейнера
function navbarOffset(elem) {
	if (!elem) return

	const navHeight = elem.clientHeight;

	// Добавим смещение следущему после меню элементу
	const header = elem.nextElementSibling
	if (header) {
		header.style.marginTop = navHeight + 'px'
		const headerHeight = header.clientHeight

		const container = header.nextElementSibling
		if (container) {
			container.style.minHeight = `calc(100vh - ${navHeight}px - ${headerHeight}px)`
		}
	}

}


document.addEventListener("DOMContentLoaded", function() {
	//=require components/_init.js

	const navbar = document.querySelector('nav.navbar');
	const html = document.querySelector('html.sd43');
	html && navbarOffset(navbar);
	html && toggleBurgerMenu(navbar);

	const exhibitionsLink = document.querySelectorAll('.exh-nav-item .nav-link');
	(window.innerWidth >= 992) && toggleNavItems(exhibitionsLink);

	if ('loading' in HTMLImageElement.prototype) {
		var images = document.querySelectorAll("img");
		images.forEach(img => {
			var preserveLazyload = (img.classList.contains('image-img') && document.querySelector("html").classList.contains('desktop'));
			if (!preserveLazyload) {
				if (img.dataset.src) 	img.removeAttribute('data-src');
				if (img.dataset.srcset) img.removeAttribute('data-srcset');
				if (! img.classList.contains('lasyloaded')) img.classList.add('lazyloaded');
				img.classList.remove('lazyload');
			}
		});
	}


	//обработаем нажатие на '+/-' у заголовка групп фильтрации checkbox для развертывания/свертывания
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

	const menu = document.querySelector('#navbarNavDropdown');
	var menuCanvas = (menu) ? new bootstrap.Offcanvas(menu) : null;

	const sidebar = document.querySelector('#sidebarPrimary');
	var sidebarCanvas = (sidebar) ? new bootstrap.Offcanvas(sidebar) : null;

	// закрытие модальных окон при изменении размера окна
	window.addEventListener('resize', function(){
		html && navbarOffset(navbar);
		html && toggleBurgerMenu(navbar);
		toggleNavItems(exhibitionsLink);
		if (window.innerWidth >= 992) {
			if (menuCanvas && menu.classList.contains('show') ) {
				menuCanvas.hide();
			}
			if (sidebarCanvas && sidebar.classList.contains('show')) {
				sidebarCanvas.hide();
			}
		}
	});

	document.onkeydown = function(e) { // закрытие окна поиска по клавише escape
		e = e || window.event;
		(e.keyCode == 27) && searchContainer.classList.remove('active');
	};

});