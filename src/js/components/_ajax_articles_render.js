
	const navbar = document.querySelector('nav.navbar');
	var preloader = document.querySelector('#preloader');
	var currentPage = 1, nextPage = true;

	function contentRender(data){
		var article_list = data['articles'];
		var html = '';
		for (var i in article_list) {
			// усечем контент, если он превышает 350 символов
			var id = article_list[i]['id'];
			var person = (article_list[i]['person']) ? `<span>автор: </span><a class="article-author" href="${article_list[i]['person_url']}"><i><b>${article_list[i]['person']}</b></i></a>` : '';
			var content = truncateHTML(article_list[i]['content'], 350, { keepImageTag: true, ellipsis: '...' });
			var date = new Date(article_list[i]['modified_date']).toLocaleDateString();
			html += `<article id="article-${id}" class="article-content">\
				<h2 class="article-title"><a href="${id}">${article_list[i]['title']}</a></h2>\
				${person}\
				<div class="modified-date">${date}</div>\
				<div class="article-text">${content}<span>[<u><i><a href="${id}" class="link-dark">читать полностью</a></i></u>]</span></div>\
			</article>`;
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

				//smoothScroll(contentBlock.getBoundingClientRect().top, navbar.clientHeight); // сдвинем контент вверх экрана
				smoothScroll(0, navbar.clientHeight); // сдвинем контент вверх экрана

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


