
	var preloader = document.querySelector('#preloader');
	var currentPage = 1, nextPage = true;

	function contentRender(data){
		var projects_list = data['projects_list'];
		var html = '';
		for (var i in projects_list) {

			var id = projects_list[i]['id'],
				title = projects_list[i]['title'],
				thumb_mini = data['media_url']+projects_list[i]['thumb_mini'],
				thumb_xs = data['media_url']+projects_list[i]['thumb_xs'],
				thumb_sm = data['media_url']+projects_list[i]['thumb_sm'],
				thumb_xs_w = projects_list[i]['thumb_xs_w'],
				thumb_sm_w = projects_list[i]['thumb_sm_w'],
				author = projects_list[i]['owner__name'],
				score = (projects_list[i]['average']) ? projects_list[i]['average'].toFixed(1) : null,
				win_year = projects_list[i]['win_year'],
				url = data['projects_url']+projects_list[i]['owner__slug']+'/project-'+projects_list[i]['project_id']+'/';

			html +='<a id="project-'+id+'" class="grid-cell" href="'+url+'" title="'+title+'">\
					<figure>\
						<img class="project-cover lazyload"\
							src="'+thumb_mini+'"\
							data-src="'+thumb_sm+'"\
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
							(win_year ?
							'<div class="portfolio-award centered">\
								<svg class="award"><use xlink:href="#award-icon"></use></svg>\
								<span>'+win_year+'</span>\
							</div>' : '')+
						'</figcaption>\
					</figure>\
				</a>';
		}

		if (html) {
			nextPage = data['next_page'];
			currentPage = data['current_page'];

			if (currentPage == 1) {
				var clone = preloader.cloneNode(true);
				contentBlock.innerHTML = html;
				contentBlock.append(clone);
				preloader = clone;
				if (nextPage) {
					preloader.classList.remove('hidden');
					preloader.classList.add('show');
				}

			} else {
				// Вставим контент перед прелоадером
				preloader.insertAdjacentHTML('beforebegin', html);
			}
			jsonRequest(); // сразу подгрузим следующий контент, если прелоадер остался в зоне видимости
			lazyloadInit(); // обновим lazyload

		} else nextPage = false;


		if (nextPage == false) {
			document.removeEventListener('scroll', jsonRequest);
			preloader.classList.remove('show');
			window.setTimeout( () => {
				preloader.classList.add('hidden');
			}, 200);
		}
	}

	function lazyloadInit() {
		(async () => {
			if ('loading' in HTMLImageElement.prototype) {
				const images = document.querySelectorAll("img.lazyload");
				images.forEach(img => {
					if (img.dataset.src) {
						img.src = img.dataset.src;
						if (img.dataset.srcset)
							img.srcset = img.dataset.srcset;
					}
					img.onload = function() {
						img.removeAttribute('data-src');
						if (img.dataset.srcset)
							img.removeAttribute('data-srcset');
						img.classList.add('lazyloaded');
						img.classList.remove('lazyload');
					};
				});

			} else {
				lazySizes.init();
			}
		})();
	}

	function jsonRequest() {
		if (nextPage && isInViewport(preloader, true)) {
			nextPage = null; // До завершения запроса на сервере, статус след страницы установим в null, чтобы не выполнять новые ajax запросы
			let url = preloader.href;
			let params = 'page=' + String(currentPage+1);
			if (filterForm) {
				let filters = new URLSearchParams(new FormData(filterForm)).toString();
				params += '&'+filters;
			}
			ajaxSend(url, params, 'get', contentRender);
		}
	}

	if (preloader) {
		document.addEventListener('scroll', jsonRequest);
		preloader.addEventListener('click', (e) => {
			e.preventDefault();
			jsonRequest();
		});
	}


