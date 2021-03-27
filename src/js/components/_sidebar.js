	/*
	 * Sidebar Events
	 */

	const sidebar = document.querySelector('.sidebar-primary');
	//const navbar = document.querySelector('nav.navbar');

/*	window.setTimeout( () => {
		navbar.style.visibility = 'visible';
	}, 300);*/

	function showSidebar(e) {
		e.preventDefault();
		sidebar.style.top = (window.innerWidth < 992) ? navbar.clientHeight + 'px' : '';
		sidebar.classList.toggle('show');
		document.body.classList.add('modal-open');
		alertContainer.classList.remove('hidden');

		alertContainer && alertContainer.addEventListener('click', closeSidebar, {passive: true});
		window.addEventListener('keydown', (e)=>{
			(e.keyCode == 27) && closeSidebar();
		});
	}

	// закрытие сайдбара
	function closeSidebar() {
		sidebar.classList.remove('show');
		alertContainer.classList.add('hidden');
		alertContainer && alertContainer.removeEventListener('click', closeSidebar);
		document.body.classList.remove('modal-open');
		window.removeEventListener('keydown', (e)=>{});
	}

	// нажатие на кнопку активации сайдбара (для мобильных устройств)
	const showSidebarBtn = document.querySelector('.sidebar-show-link');
	showSidebarBtn && showSidebarBtn.addEventListener('click', showSidebar, {passive: true});

	// Добавим кнопку закрытия сайдбара, если есть вложенные элементы
	if (sidebar.firstElementChild) {
		var btn_html = '<button type="button" class="sidebar-close btn-close d-lg-none" data-bs-dismiss="alert" aria-label="Закрыть"></button>';
		sidebar.insertAdjacentHTML("afterbegin",btn_html);

		// нажатие на кнопку закрытия сайдбара
		const closeSidebarBtn = sidebar.querySelector('.sidebar-close');
		closeSidebarBtn && closeSidebarBtn.addEventListener('click', closeSidebar, {passive: true});
	}

