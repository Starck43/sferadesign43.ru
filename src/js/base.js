
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

function navbarOffset() {
	// Добавим смещение следущему после меню элементу
	const navbar = document.querySelector('.navbar');
	if (!navbar.classList.contains('expanded')) {
		var siblingEl = navbar.nextElementSibling;
		siblingEl.style.marginTop = navbar.clientHeight + 'px';
	}
}

document.addEventListener("DOMContentLoaded", function() {
	const burger = document.querySelector('.navbar-toggler');

	navbarOffset();

	const images = document.querySelectorAll("img:not(.lazyload)");
	images.forEach(img => {
		if ('loading' in HTMLImageElement.prototype)
			img.setAttribute('loading','lazy');
		else
			img.classList.add('lazyload');
	});

	const exhibitionsLink = document.querySelectorAll('.exh-nav-item .nav-link');
	(window.innerWidth >= 992) && toggleNavItems(exhibitionsLink);

	window.addEventListener('resize', function(){
		navbarOffset();
		toggleNavItems(exhibitionsLink);
		if (window.innerWidth >= 992) {
			burger.classList.contains('collapsed') && burger.classList.remove('collapsed');
			burger.nextElementSibling.style.maxHeight = '';
		}

	});

	loadingElements = document.body.querySelectorAll('.loading');
	loadingElements.forEach( function(item) {
		item.classList.remove('loading');
		item.classList.add('loaded');
	});

	//обработаем нажатие на '+/-' у заголовка групп фильтрации checkbox для размертывания/свертывания
	const collapsedBlock = document.querySelectorAll('.collapsed')
	collapsedBlock.forEach( (item) => {
		item.addEventListener('click', (e) => {
/*			for (let sibling of e.target.siblingNode) {
				sibling.classList.remove('collapsed');
				sibling.classList.remove('collapsed');
			}*/
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

	// Сворачивание мобильного меню по нажатию вне области его контейнера
	burger.addEventListener('click', function (e) {
		const container = document.querySelector('.container');
		var navbarNavDropdown =  document.querySelector('.navbar-collapse');

		if (container && (this.getAttribute('aria-expanded') == "true" || this.ariaExpanded == "true")) {
			this.parentNode.parentNode.classList.add('expanded');
			navbarNavDropdown.style.maxHeight = navbarNavDropdown.scrollHeight + 'px';
			container.addEventListener('click', containerListener, false);
		}
		if (container && (this.getAttribute('aria-expanded') == "false" || this.ariaExpanded == "false")) {
			this.parentNode.parentNode.classList.remove('expanded');
			navbarNavDropdown.style.maxHeight = 0;
			container.removeEventListener('click', containerListener, false);
		}
	})

	var containerListener = function(e) {
		burger.click();
	}

	const searchLink = document.querySelectorAll('.nav-search-link');
	const searchContainer = document.querySelector('#searchContainer');
	searchLink.forEach( (item) => {
		item.addEventListener('click', (e) => {
			searchContainer.classList.toggle('active');
		}, {passive: true});
	})


	document.onkeydown = function(e) { // закрытие окна поиска по клавише escape
		e = e || window.event;
		(e.keyCode == 27) && searchContainer.classList.remove('active');
	};

	document.onscroll = function(e) { // закрытие окна поиска по скролу
		searchContainer.classList.contains('active') && searchContainer.classList.remove('active');
	};

/*	filterItems.on('click', '.filter__title', function(e) {
		if ( $(this).hasClass(collapsed) || $(this).hasClass(expanded) ) {
			$(this).toggleClass(collapsed).toggleClass(expanded);
			$(this).parent().siblings('.filter__inner').slideToggle(300);
		}
	});*/

});