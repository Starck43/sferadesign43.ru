
	// Событие нажатия на кнопку фильтрации
	const filterForm = document.querySelector('form[name=projects-filter]');
	var preloader = document.querySelector('#preloader');

	if (filterForm) {
		const filterCheckboxes = filterForm.querySelectorAll('input[type=checkbox]');
		const filterLink = document.querySelector('.filter-link');
		const sidebar = document.querySelector('#sidebar');
		const navbar = document.querySelector('nav.navbar');

		const closeBtn = sidebar.querySelector('.sidebar-close');
		const submitBtn = filterForm.querySelector('[type=submit]');
		var projectsGrid = document.querySelector('.projects-list');


		function closeSidebar() {
			sidebar.classList.remove('active');
			alertContainer.classList.add('hidden');
			alertContainer.removeEventListener('click', closeSidebar);
			document.body.classList.remove('modal-open');
			window.removeEventListener('keydown', (e)=>{});
		}


		closeBtn.addEventListener('click', closeSidebar, {passive: true});
		filterLink.addEventListener('click', function (e) {
			e.preventDefault();
			sidebar.style.top = navbar.clientHeight + 'px';
			sidebar.classList.toggle('active');
			document.body.classList.add('modal-open');
			alertContainer.classList.remove('hidden');
			alertContainer.addEventListener('click', closeSidebar, {passive: true});
			window.addEventListener('keydown', (e)=>{
				(e.keyCode == 27) && closeSidebar();
			});
		}, {passive: true});


		function submitFilter(el) {
			let url = el.action;
			let method = el.method;
			let params = new URLSearchParams(new FormData(el)).toString();
			if (params == '') {
				projectsGrid.classList.remove('filtered');
				submitBtn.disabled = true;
				//params = 'filter-group=0';
				//el.setAttribute('value', 0);
				//window.location.reload();
			} else {
				projectsGrid.classList.add('filtered');
				submitBtn.disabled = false;
			}

			params = 'page=1&' + params;
			if (preloader) {
				preloader.classList.remove('hidden');
				preloader.classList.add('show');
				nextPage = null;
				document.addEventListener('scroll', loadNewProjects, {passive: true});
			}
			ajaxSend(url, params, method, projectsRender);
			//closeSidebar();
		}


		if (filterCheckboxes.length > 0) {

			filterCheckboxes.forEach( (checkbox) => {
				if (checkbox.checked) submitBtn.disabled = false;
				checkbox.addEventListener('change',(e)=>{
					 submitFilter(filterForm);
				});
			});

		}

		filterForm.addEventListener('submit', function (e) {
			e.preventDefault();
			let i = filterCheckboxes.length-1;
			for(;i>=0;i--){
				filterCheckboxes[i]['checked'] = false;
			}
			submitFilter(this);
		});

	}
