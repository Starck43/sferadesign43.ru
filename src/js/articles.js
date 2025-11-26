import { lazyloadInit } from './utils/lazyload.js';
import { truncateHTML } from './utils/truncate.js';
import { isInViewport, smoothScroll } from './utils/viewport.js';
import {createFormData} from "./utils/ajax.js";

document.addEventListener("DOMContentLoaded", () => {
	/*
	 * Articles Filter - Фильтрация статей с обработчиками
	 */
	const sidebar = document.querySelector('.sidebar-primary');
	const filterForm = sidebar?.querySelector('form[name=articles-filter]');
	const contentBlock = document.querySelector('#articleList');
	const navbar = document.querySelector('nav.navbar');
	let preloader = document.querySelector('#preloader');
	let currentPage = 1;
	let nextPage = true;

	// Рендер контента статей
	function contentRender(data) {
		const article_list = data['articles'];
		let html = '';
		
		for (let i in article_list) {
			const id = article_list[i]['id'];
			const person = article_list[i]['person'] 
				? `<span>автор: </span><a class="article-author" href="${article_list[i]['person_url']}"><i><b>${article_list[i]['person']}</b></i></a>` 
				: '';
			const content = truncateHTML(article_list[i]['content'], 350, { keepImageTag: true, ellipsis: '...' });
			const date = new Date(article_list[i]['modified_date']).toLocaleDateString();
			
			html += `<article id="article-${id}" class="article-content">
				<h2 class="article-title"><a href="${id}">${article_list[i]['title']}</a></h2>
				${person}
				<div class="modified-date">${date}</div>
				<div class="article-text">${content}<span>[<u><i><a href="${id}" class="link-dark">читать полностью</a></i></u>]</span></div>
			</article>`;
		}

		if (html) {
			nextPage = data['next_page'];
			currentPage = data['current_page'];

			if (currentPage === 1) {
				const clone = preloader.cloneNode(true);
				contentBlock.innerHTML = html;
				contentBlock.append(clone);
				preloader = clone;
				
				if (nextPage) {
					preloader.classList.remove('hidden');
					preloader.classList.add('show');
				}

				smoothScroll(0, navbar?.clientHeight || 0);
			} else {
				preloader.insertAdjacentHTML('beforebegin', html);
			}

			jsonRequest();
			lazyloadInit();
		} else {
			nextPage = false;
		}

		if (nextPage === false) {
			document.removeEventListener('scroll', jsonRequest);
			preloader.classList.remove('show');
			window.setTimeout(() => {
				preloader.classList.add('hidden');
			}, 200);
		}
	}

	// AJAX запрос следующей страницы
	function jsonRequest() {
		if (nextPage && isInViewport(preloader, true)) {
			nextPage = null;
			const url = preloader.href;
			let params = 'page=' + String(currentPage + 1);
			
			if (filterForm) {
				const filters = createFormData(filterForm);
				params += '&' + filters;
			}
			
			window.ajaxSend(url, params, 'get', contentRender);
		}
	}

	if (filterForm) {
		const filterAttributes = filterForm.querySelectorAll('input[name=article-category]');

		// Запуск фильтрации контента
		function submitFilter(el) {
			nextPage = null;
			const url = el.action;
			const method = el.method;
			const params = createFormData(el);
			
			window.ajaxSend(url, 'page=1&' + params, method, contentRender);
			document.addEventListener('scroll', jsonRequest);
		}

		// Изменение положения сайдбара по breakpoint
		function resizeSidebar(breakpoint = 992) {
			if (window.innerWidth < breakpoint && sidebar.classList.contains('left-side')) {
				sidebar.classList.remove('left-side');
			}
			if (window.innerWidth >= breakpoint && !sidebar.classList.contains('left-side')) {
				sidebar.classList.add('left-side');
			}
		}

		// Обработка нажатия на атрибут фильтра
		filterAttributes.forEach((radio) => {
			radio.addEventListener('change', (e) => {
				submitFilter(filterForm);
				filterAttributes.forEach(el => {
					el.nextElementSibling.classList.remove('active');
				});
				e.target.nextElementSibling.classList.add('active');
			});
		});

		window.addEventListener('resize', resizeSidebar);
		resizeSidebar(992);
	}

	// Инициализация прелоадера
	if (preloader) {
		document.addEventListener('scroll', jsonRequest);
		preloader.addEventListener('click', (e) => {
			e.preventDefault();
			jsonRequest();
		});
	}
});
