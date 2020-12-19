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
	var siblingEl = navbar.nextElementSibling;
	siblingEl.style.marginTop = navbar.clientHeight + 'px';
}

document.addEventListener("DOMContentLoaded", function() {
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

	const firstImg = document.querySelector('.portfolio-list img');
	const preloader = document.querySelector('.portfolio-preloader');
	if (preloader) {
		firstImg.onload = function(){
		//display ok
			preloader && preloader.remove();
		}
	}


	const burger = document.querySelector('.navbar-toggler');
	burger.addEventListener('click', function (e) {
		const container = document.querySelector('.container');
		var navbarNavDropdown =  document.querySelector('.navbar-collapse');

		if (container && e.currentTarget.ariaExpanded == "true") {
			navbarNavDropdown.style.maxHeight = navbarNavDropdown.scrollHeight + 'px';
			container.addEventListener('click', containerListener, false);
		}
		if (container && e.currentTarget.ariaExpanded == "false") {
			navbarNavDropdown.style.maxHeight = 0;
			container.removeEventListener('click', containerListener, false);
		}
	})

	var containerListener = function(e) {
		console.log('click container');
		burger.click();
	}
/*	filterItems.on('click', '.filter__title', function(e) {
		if ( $(this).hasClass(collapsed) || $(this).hasClass(expanded) ) {
			$(this).toggleClass(collapsed).toggleClass(expanded);
			$(this).parent().siblings('.filter__inner').slideToggle(300);
		}
	});*/

});