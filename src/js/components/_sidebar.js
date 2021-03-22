	/*
	 * Sidebar Events
	 */

	const sidebar = document.querySelector('#sidebar');
	const navbar = document.querySelector('nav.navbar');

/*	window.setTimeout( () => {
		navbar.style.visibility = 'visible';
	}, 300);*/

	// закрытие сайдбара
	function closeSidebar() {
		sidebar.classList.remove('active');
		alertContainer.classList.add('hidden');
		alertContainer && alertContainer.removeEventListener('click', closeSidebar);
		document.body.classList.remove('modal-open');
		window.removeEventListener('keydown', (e)=>{});
	}

	// нажатие на кнопку активации сайдбара (для мобильных устройств)
	const activeSidebarBtn = document.querySelector('.filter-link');
	activeSidebarBtn.addEventListener('click', function (e) {
		e.preventDefault();
		sidebar.style.top = (window.innerWidth < 992) ? navbar.clientHeight + 'px' : '';
		sidebar.classList.toggle('active');
		document.body.classList.add('modal-open');
		alertContainer.classList.remove('hidden');

		alertContainer && alertContainer.addEventListener('click', closeSidebar, {passive: true});
		window.addEventListener('keydown', (e)=>{
			(e.keyCode == 27) && closeSidebar();
		});
	}, {passive: true});

	// нажатие на кнопку закрытия сайдбара (для мобильных устройств)
	const closeSidebarBtn = sidebar.querySelector('.sidebar-close');
	closeSidebarBtn.addEventListener('click', closeSidebar, {passive: true});

