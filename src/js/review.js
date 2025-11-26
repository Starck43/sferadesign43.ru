// review.js - исправленная версия
import {createFormData} from './utils/ajax.js';
import {Modal} from './components/modal.js';
import {autoResizeTextarea, initAutoResizeTextareas} from "./utils/common.js";

document.addEventListener("DOMContentLoaded", () => {
	const reviewForm = document.querySelector('form[name=review]');
	const editModalContainer = document.getElementById('editCommentContainer');
	const deleteModalContainer = document.getElementById('deleteCommentContainer');

	if (!reviewForm) return;

	let targetLink = null;
	let editModalInstance = null;
	let deleteModalInstance = null;
	let currentCommentId = null;

	// Инициализация модальных окон
	function initModals() {
		if (editModalContainer && !editModalInstance) {
			editModalInstance = new Modal(editModalContainer);
		}

		if (deleteModalContainer && !deleteModalInstance) {
			deleteModalInstance = new Modal(deleteModalContainer);
			initDeleteModalHandlers();
		}
	}

	// Обработчики для модального окна удаления
	function initDeleteModalHandlers() {
		const confirmBtn = deleteModalContainer.querySelector('#confirmDelete');
		confirmBtn.addEventListener('click', handleDeleteConfirm);

		deleteModalContainer.querySelectorAll('button[data-dismiss="modal"]').forEach(btn => {
			btn.addEventListener('click', () => deleteModalInstance.hide());
		});
	}

	// Подтверждение удаления
	function handleDeleteConfirm() {
		if (!currentCommentId) return;

		const url = `/review/delete/${currentCommentId}/`;
		if (window.ajaxSend) {
			window.ajaxSend(url, '', 'post', (data) => {
				if (data.status === 'success') {
					const comment = document.getElementById(currentCommentId);
					if (comment) {
						comment.remove();
						deleteModalInstance.hide();
						if (window.Alert) {
							window.Alert.success('Комментарий успешно удален!', 3000, 'top-center');
						}
					}
				} else {
					deleteModalInstance.hide();
					if (window.Alert) {
						window.Alert.error(data.message || 'Ошибка при удалении комментария!', 0, 'top-center');
					}
				}
			});
		}
	}

	// Показать статус в модальном окне редактирования
	function showStatus(message, type = '') {
		const statusMsg = editModalContainer.querySelector('.message-status');
		if (statusMsg) {
			statusMsg.textContent = '';
			statusMsg.classList.remove('error', 'success');
			if (type && message) {
				statusMsg.classList.add(type);
				statusMsg.textContent = message;
			}
		}
	}

	// ========== ОСНОВНЫЕ ФУНКЦИОНАЛЬНОСТИ ==========

	// Добавление комментария
	function handleAddComment(e) {
		e.preventDefault();

		const params = createFormData(e.target);
		if (window.ajaxSend) {
			window.ajaxSend(e.target.action, params, 'post', (data) => {
				renderNewComment(data);
				clearForm();
			});
		}
	}

	// Рендер нового комментария
	function renderNewComment(data) {
		if (!data || !data.id) {
			console.error('Invalid comment data:', data);
			return;
		}

		const commentElement = createCommentElement(data);

		// ИСПРАВЛЕННЫЙ СЕЛЕКТОР КОНТЕЙНЕРА
		const container = document.querySelector('#commentsContainer') ||
			document.querySelector('.comments-container');

		if (targetLink && targetLink.parentNode.classList.contains('portfolio-comment')) {
			targetLink.parentNode.after(commentElement);
			commentElement.classList.add('subcomment');
		} else {
			const existingForm = container.querySelector('form[name=review]');
			if (existingForm) {
				existingForm.after(commentElement);
			} else {
				container.appendChild(commentElement);
			}
		}

		if (targetLink) {
			const existingReplyForm = targetLink.parentNode.querySelector('form[name=review]');
			existingReplyForm?.remove();
			targetLink = null;
		}

		// Авто-размер для новых textarea
		setTimeout(() => {
			document.querySelectorAll('textarea').forEach(textarea => {
				if (!textarea.hasAttribute('data-auto-resize-initialized')) {
					autoResizeTextarea(textarea);
					textarea.addEventListener('input', () => autoResizeTextarea(textarea));
					textarea.setAttribute('data-auto-resize-initialized', 'true');
				}
			});
		}, 50);

		showStatus('Комментарий успешно добавлен!', 'success');
	}

	// Создание элемента комментария
	function createCommentElement(data) {
		const article = document.createElement('article');
		article.className = 'portfolio-comment';
		article.id = data.id;

		article.innerHTML = `
			<div class="comment-block">
				<h3 class="comment-block-author">${data.author || 'Аноним'}</h3>
				<div class="comment-block-datetime">${data.posted_date || new Date().toLocaleDateString('ru-RU')}</div>
				<p class="comment-block-text">${data.message}</p>
			</div>
			<a class="reply-link" 
			   data-id="${data.id}" 
			   data-parent="${data.parent || ''}" 
			   data-group="${data.group || data.id}" 
			   data-author="${data.author || 'Аноним'}"
			>
				<svg class="btn-xs"><use xlink:href="#reply-icon"></use></svg>
				<span>Ответить</span>
			</a>
		`;
		addCommentControls(article, data);

		const replyLink = article.querySelector('.reply-link');
		if (replyLink) {
			replyLink.addEventListener('click', handleReply);
		}

		return article;
	}

	// Добавление кнопок управления к комментарию
	function addCommentControls(commentElement, data) {
		const editLinkTemplate = document.querySelector('.edit-instance-link');
		const deleteLinkTemplate = document.querySelector('.delete-instance-link');

		if (editLinkTemplate) {
			const editLink = editLinkTemplate.cloneNode(true);
			editLink.classList = 'edit-link';
			editLink.href = `/review/edit/${data.id}/`;
			editLink.setAttribute('data-author-reply', data.author || '');
			editLink.addEventListener('click', handleEdit);
			commentElement.appendChild(editLink);
		}

		if (deleteLinkTemplate && (!data.reply_count || data.reply_count === 0)) {
			const deleteLink = deleteLinkTemplate.cloneNode(true);
			deleteLink.classList = 'delete-link';
			deleteLink.href = `/review/delete/${data.id}/`;
			deleteLink.addEventListener('click', handleDelete);
			commentElement.appendChild(deleteLink);
		}
	}

	// Ответ на комментарий
	function handleReply(e) {
		e.preventDefault();
		targetLink = e.currentTarget;
		showReplyForm(targetLink);
	}

	// Показать форму ответа
	function showReplyForm(target) {
		const existingForm = target.parentNode.querySelector('form[name=review]');
		if (existingForm) {
			existingForm.remove();
			return;
		}

		const form = reviewForm.cloneNode(true);
		const parentInput = form.querySelector('.parent-control');
		const groupInput = form.querySelector('.group-control');
		const textarea = form.querySelector('textarea');

		parentInput.value = target.dataset.id;
		groupInput.value = target.dataset.group;
		textarea.placeholder = target.dataset.author
			? `Ваш ответ для ${target.dataset.author}...`
			: 'Ваш комментарий...';

		target.parentNode.appendChild(form);

		// Авто-размер для формы ответа
		autoResizeTextarea(textarea);
		textarea.addEventListener('input', () => autoResizeTextarea(textarea));

		form.addEventListener('submit', handleAddComment);

		setTimeout(() => textarea.focus(), 10);
	}

	// Редактирование комментария
	function handleEdit(e) {
		e.preventDefault();
		currentCommentId = e.currentTarget.href.split('/').filter(Boolean).pop();

		if (window.ajaxSend) {
			window.ajaxSend(e.currentTarget.href, '', 'get', renderEditForm);
		}
	}

	function renderEditForm(data) {
		if (!data || !data.form) {
			console.error('Invalid edit form data:', data);
			return;
		}

		const form = document.createElement('form');
		form.method = 'post';
		form.action = data.action;
		form.name = 'edit';
		form.id = 'editCommentForm';
		form.classList = 'review-form';
		form.innerHTML = data.form;

		const subTitle = data.author_reply
			? `Ответ для <i>${data.author_reply}</i>`
			: '';

		const modalBody = editModalContainer.querySelector('.modal-body');
		modalBody.innerHTML = '';

		if (subTitle) {
			const subTitleEl = document.createElement('div');
			subTitleEl.className = 'sub-title';
			subTitleEl.innerHTML = subTitle;
			modalBody.appendChild(subTitleEl);
		}

		modalBody.appendChild(form);

		const modalTitle = editModalContainer.querySelector('.modal-title');
		if (modalTitle) {
			modalTitle.textContent = 'Изменить комментарий';
		}

		const saveButton = editModalContainer.querySelector('button[type="submit"]');
		if (saveButton) {
			saveButton.type = 'submit';
			saveButton.form = 'editCommentForm';
			saveButton.textContent = 'Сохранить';
		}

		form.addEventListener('submit', (e) => {
			e.preventDefault();

			const params = createFormData(e.target);
			if (window.ajaxSend) {
				window.ajaxSend(e.target.action, params, 'post', (responseData) => {
					if (responseData.status === 'success') {
						updateCommentInDOM(responseData);
						showStatus('Комментарий успешно обновлен!', 'success');

						// Обновляем форму с новым текстом
						const textarea = form.querySelector('textarea');
						if (textarea) {
							textarea.value = responseData.message;
							autoResizeTextarea(textarea);
						}
					} else {
						showStatus('Ошибка при обновлении комментария!', 'error');
					}
				});
			}
		});

		editModalInstance.show();
		showStatus('');

		// Авто-размер при открытии
		setTimeout(() => {
			const textarea = form.querySelector('textarea');
			if (textarea) {
				autoResizeTextarea(textarea);
				textarea.focus();
				textarea.value = textarea.value.trim().replace(/\s+/g, ' ');
				textarea.setSelectionRange(textarea.value.length, textarea.value.length);
				textarea.addEventListener('input', () => autoResizeTextarea(textarea));
			}
		}, 100);
	}

	// Обновление комментария в DOM
	function updateCommentInDOM(data) {
		const comment = document.getElementById(data.id);
		if (comment) {
			const textBlock = comment.querySelector('.comment-block-text');
			if (textBlock) {
				textBlock.textContent = data.message;
			}
		}
	}

	// Удаление комментария
	function handleDelete(e) {
		e.preventDefault();
		currentCommentId = e.currentTarget.href.split('/').filter(Boolean).pop();
		deleteModalInstance.show();
	}

	// Очистка основной формы
	function clearForm() {
		const textarea = reviewForm.querySelector('textarea');
		const parentInput = reviewForm.querySelector('.parent-control');
		const groupInput = reviewForm.querySelector('.group-control');

		if (textarea) {
			textarea.value = '';
			autoResizeTextarea(textarea); // Сбрасываем размер
		}
		if (parentInput) parentInput.value = '';
		if (groupInput) groupInput.value = '';
	}

	// ========== ИНИЦИАЛИЗАЦИЯ ==========

	function init() {
		initModals();
		initAutoResizeTextareas();

		// Авто-размер для основной формы
		const mainTextarea = reviewForm.querySelector('textarea');
		if (mainTextarea) {
			autoResizeTextarea(mainTextarea);
			mainTextarea.addEventListener('input', () => autoResizeTextarea(mainTextarea));
		}

		reviewForm.addEventListener('submit', handleAddComment);

		document.querySelectorAll('.reply-link').forEach(link => {
			link.addEventListener('click', handleReply);
		});

		document.querySelectorAll('.edit-link').forEach(link => {
			link.addEventListener('click', handleEdit);
		});

		document.querySelectorAll('.delete-link').forEach(link => {
			link.addEventListener('click', handleDelete);
		});

		editModalContainer.querySelectorAll('button[data-dismiss="modal"]').forEach(btn => {
			btn.addEventListener('click', () => {
				editModalInstance.hide();
				showStatus('');
			});
		});
	}

	init();
});
