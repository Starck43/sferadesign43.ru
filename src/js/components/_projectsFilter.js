
	// Событие нажатия на кнопку фильтрации
	const filterForm = document.querySelector('form[name=projects-filter]');

	if (filterForm) {
		const filterCheckboxes = filterForm.querySelectorAll('input[type=checkbox]');
		const filterLink = document.querySelector('.filter-link');
		const sidebar = document.querySelector('#sidebar');
		const closeBtn = sidebar.querySelector('.sidebar-close');
		const submitBtn = filterForm.querySelector('[type=submit]');
		var projectsGrid = document.querySelector('.projects-list');


		function closeSidebar() {
			sidebar.classList.remove('active');
			alertContainer.classList.add('hidden');
			alertContainer.removeEventListener('click', closeSidebar);
			window.removeEventListener('keydown', (e)=>{});
		}


		function submitFilter(el) {
			let url = el.action;
			let method = el.method;
			let params = new URLSearchParams(new FormData(el)).toString();
			if (params == '') {
				projectsGrid.classList.remove('filtered');
				submitBtn.disabled = true;
				//params = 'filter-group=0';
				//el.setAttribute('value', 0);
				window.location.reload();
			} else{
				projectsGrid.classList.add('filtered');
				submitBtn.disabled = false;
			}
			ajaxSend(url, params, method, projectsRender);
			//closeSidebar();
		}


		closeBtn.addEventListener('click', closeSidebar, {passive: true});
		filterLink.addEventListener('click', function (e) {
			e.preventDefault();
			sidebar.style.top = navbar.clientHeight + 'px';
			sidebar.classList.toggle('active');
			alertContainer.classList.remove('hidden');
			alertContainer.addEventListener('click', closeSidebar, {passive: true});
			window.addEventListener('keydown', (e)=>{
				(e.keyCode == 27) && closeSidebar();
			});
		}, {passive: true});


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

	} // is filter-form


	const projectsRender = function(data){
		var projects_list = data['projects_list'];
		var html = '';
		for (var i in projects_list) {

			var id = projects_list[i]['id'],
				title = projects_list[i]['title'],
				fullimage = data['media_url']+projects_list[i]['cover'],
				thumb_xs = data['media_url']+projects_list[i]['thumb_xs'],
				thumb_sm = data['media_url']+projects_list[i]['thumb_sm'],
				thumb_xs_w = projects_list[i]['thumb_xs_w'],
				thumb_sm_w = projects_list[i]['thumb_sm_w'],
				author = projects_list[i]['owner__name'],
				score = (projects_list[i]['average']) ? projects_list[i]['average'].toFixed(1) : null,
				url = data['projects_url']+projects_list[i]['owner__slug']+'/project-'+projects_list[i]['project_id']+'/';

			html +='<a id="project-'+id+'" class="grid-cell" href="'+url+'" title="'+title+'">\
					<figure>\
						<img class="project-cover lazyload"\
							data-src="'+fullimage+'"\
							data-srcset="'+thumb_xs+' ' + thumb_xs_w+'w, '+ thumb_sm+' '+thumb_sm_w + 'w"\
							loading="lazy"\
							title="'+title+'"\
							alt="'+(title ? title+'. ' : '')+'Автор проекта: '+author+'">\
						<figcaption class="img-title centered">\
							<h2 class="project-title">'+title+'</h2>'+
							(author ? '<div class="subtitle">'+author+'</div>' : '')+
							(score ?
							'<div class="portfolio-rate centered">\
								<span class="rate-counter">'+score+'</span>\
								<svg class="rate-star"><use xlink:href="#star-icon"></use></svg>\
							</div>' : '')+
						'</figcaption>\
					</figure>\
				</a>';
		}

		projectsGrid.innerHTML = html;
		(async () => {
			if ('loading' in HTMLImageElement.prototype) {
				const images = document.querySelectorAll("img.lazyload");
				images.forEach(img => {
					if (img.dataset.src) {
						img.src = img.dataset.src;
						img.srcset = img.dataset.srcset;
					}
					img.classList.add('lazyloaded');
					img.classList.remove('lazyload');
				});

			} else {
				lazySizes.init();
			}
		})();
	}


	loadNewProjects = function(e) {
		e.preventDefault();
		let url = this.href,
			params = 'page=2';

		ajaxSend(url, params, 'get', projectsRender);
	}

	const preloader = document.querySelector('#preloader');
	preloader.addEventListener('click', loadNewProjects);

