	/*
	 *	Articles Filter - Фильтрация статей с обработчиками
	 */

	const sidebar = document.querySelector('#sidebar');
	const filterForm = sidebar.querySelector('form[name=articles-filter]');
	var contentBlock = document.querySelector('#articleList');

	if (filterForm) {
		const filterAttributes = filterForm.querySelectorAll('input[name=article-category]');

		// запуск фильтрации контента в селекторе contentBlock
		function submitFilter(el) {
			nextPage = null; // блокируем пролистывание до окончания выполнения запроса в ajaxSend()

			let url = el.action;
			let method = el.method;
			let params = new URLSearchParams(new FormData(el)).toString();
			ajaxSend(url, 'page=1&'+params, method, contentRender);
			document.addEventListener('scroll', jsonRequest);
			//closeSidebar();
		}

		// изменение положения сайдбара по прейкпоинту
		function resizeSidebar(breakpoint=992) {
			if (window.innerWidth < breakpoint && sidebar.classList.contains('left-side')) {
				sidebar.classList.remove('left-side');
			}
			if (window.innerWidth >= breakpoint && ! sidebar.classList.contains('left-side')) {
				sidebar.classList.add('left-side');
			}
		}

		// обработка нажатия на аттрибут фильтра
		filterAttributes.forEach( (radio) => {
			radio.addEventListener('change',(e)=>{
				 submitFilter(filterForm);
			});
		});

		// при изменении ширины меньше 992px, переместим сайдбар вверх
		window.addEventListener('resize', resizeSidebar);
		// проверим положение сайдбара при загрузке страницы
		resizeSidebar(992);
		sidebar.classList.add('show');

	}
