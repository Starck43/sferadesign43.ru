	/*
	 *	Projects Filter - Фильтрация проектов с обработчиками
	 */

	const filterForm = document.querySelector('form[name=projects-filter]');
	var contentBlock = document.querySelector('#projectGrid');

	if (filterForm) {
		const filterCheckboxes = filterForm.querySelectorAll('input[type=checkbox]');
		const submitBtn = filterForm.querySelector('[type=submit]');

		// запуск фильтрации контента в селекторе contentBlock
		function submitFilter(el) {
			nextPage = null; // блокируем пролистывание до окончания выполнения запроса в ajaxSend()

			let url = el.action;
			let method = el.method;
			let params = new URLSearchParams(new FormData(el)).toString();
			if (params == '') {
				// если аттрибуты сброшены
				contentBlock.classList.remove('filtered');
				submitBtn.disabled = true;
			} else {
				contentBlock.classList.add('filtered');
				submitBtn.disabled = false;
			}

			document.addEventListener('scroll', jsonRequest);
			ajaxSend(url, 'page=1&'+params, method, contentRender);
			//closeSidebar();
		}


		// сброс положений аттрибутов фильтра
		function clearCheckboxes() {
			let i = filterCheckboxes.length-1;
			for(;i>=0;i--){
				filterCheckboxes[i]['checked'] = false;
			}
		}

		// если при загрузке страницы найдены аттрибуты фильтра
		filterCheckboxes.forEach( (checkbox) => {
			checkbox['checked'] = false;
			if (checkbox.checked) submitBtn.disabled = false;
			// повесим событие на нажатие на аттрибут
			checkbox.addEventListener('change',(e)=>{
				 submitFilter(filterForm);
			});
		});

		// нажатие на кнопку сброса фильтров
		filterForm.addEventListener('submit', function (e) {
			e.preventDefault();
			clearCheckboxes();
			submitFilter(this);
		});

	}
