
	var targetLink = null;

	// Рендер шаблона
	reviewRender = function(data) {
		var newNode = document.createElement('article'),
			datetime = new Date().toLocaleDateString();

		newNode.className = 'porfolio-comment';
		newNode.id = data['id'];

		if (targetLink.parentNode.classList.contains(newNode.className)) {
			toggleCommentForm(targetLink, true, true); //скроем форму ввода сообщения и почистим его область текста
			newNode.classList.add('subcomment');
			targetLink.parentNode.after(newNode);
			// если подкомментарий, то родителем будет являться текущий id родительского комментария
			group = data['group'];
		} else {
			toggleCommentForm(targetLink, true, false); //скроем форму ввода сообщения и почистим его область текста
			targetLink.after(newNode);
			group = data['id'];
		}

		var html = '<div class="comment-block">\
					<h3 class="comment-block-author">'+data['author']+'</h3>\
					<div class="comment-block-datetime">'+datetime+'</div>\
					<p class="comment-block-text">'+data['message']+'</p>\
				</div>\
				<a class="reply-link" data-id="'+data['id']+'" data-parent="'+data['parent']+'" data-group="'+group+'" data-author="'+data['author']+'">\
					<svg><use xlink:href="#reply-icon"></use></svg><span>Ответить</span></a>';

		newNode.innerHTML = html;

		// Cloning edit link for new comment
		var editLink = document.querySelector('.edit-instance-link');
		if (editLink) {
			editLink = editLink.cloneNode(true);
			editLink.classList = 'edit-link';
			editLink.href += String(data['id'])+'/';
			editLink.setAttribute('data-author-reply', data['author']);
			editLink.addEventListener('click', editCommentEvent);
			newNode.append(editLink);
		}

		// Cloning delete link for new comment
		var deleteLink = document.querySelector('.delete-instance-link');
		if (deleteLink) {
			deleteLink = deleteLink.cloneNode(true);
			deleteLink.classList = 'delete-link';
			deleteLink.href += String(data['id'])+'/';
			deleteLink.addEventListener('click', deleteCommentEvent);
			newNode.append(deleteLink);
		}

		if (data['reply_count'] > 0 ) {
			var parentComment = document.getElementById(String(data['parent']));
			if (parentComment) {
				deleteLink = parentComment.querySelector('.delete-link');
				if (deleteLink) deleteLink.remove();
			}
		}
		var message =  '<h3>Ваш комментарий успешно отправлен!</h3>\
						<p>"'+data['message']+'"</p>';
		alertHandler(message); // функция обработки сообщений

		changeCommentsCounter(+1);

		var replyLink = newNode.querySelector('.reply-link');

		replyLink && replyLink.addEventListener('click', replyCommentEvent, {passive: true});
	}

	// Нажатие на кнопку Ответить
	replyCommentEvent = function (e) {
		e.preventDefault();
		var link = this, //a.reply-link
			replyForm = link.parentNode.lastElementChild;

		// если в блоке комментария последний элемент не форма, то клонируем из review-form
		if (! replyForm.classList.contains('reply-form')) {
			var cloneForm = document.querySelector('.review-form').cloneNode(true);
			cloneForm.classList = 'reply-form form-control hidden';
			cloneForm.querySelector('[type=submit]').className = 'btn-link'; // заменим тип конпки на ссылку для ответов
			link.parentNode.append(cloneForm);

			var parentEl = cloneForm.querySelector('.parent-control');
			var groupEl = cloneForm.querySelector('.group-control');
			var textEl = cloneForm.querySelector('textarea');
			textEl.className = 'text-control';
			parentEl.value = Number(link.dataset.id);
			groupEl.value = Number(link.dataset.group);
			textEl.textContent = link.dataset.author + ', ';
			textEl.value = textEl.textContent;
			textEl.placeholder = 'Ваш ответ...';
			//textEl.blur();
			cloneForm.addEventListener('submit', submitCommentEvent); // Повесим событие на сохранение формы
			textEl.addEventListener('input', textareaResize);
			replyForm = cloneForm;
		}
		// Сделаем клон формы видимым без очистки содержимого поля ввода
		toggleCommentForm(replyForm, false, true);

	}


	// Событие нажатия на кнопку отправки сообщения на сервер (добавление)
	submitCommentEvent = function (e) {
		e.preventDefault();
		var textarea = this.querySelector('textarea');
		var message = (textarea.value == '') ? '<h3>Предупреждение!</h3><p>Вы отправляете пустой комментарий.</p>' : '<p>Отправка сообщения ...</p>';

		alertHandler(message); // функция вызова сообщений

		if (textarea.value) {
			targetLink = this;
			var params = new URLSearchParams(new FormData(this)).toString();
			ajaxSend(this.action, params, 'post', reviewRender);
		}
	}


	var modalContainer = document.getElementById('editCommentContainer'),
		statusMsg = modalContainer.querySelector('.message-status'),
		closeModal = modalContainer.querySelector('button.btn-cancel'),
		submitModal = modalContainer.querySelector('button[type=submit]');

	editCommentEvent = function (e) {
		e.preventDefault();
		targetLink = this;

		var replyName = this.getAttribute('data-author-reply');
		var subTitle = (replyName) ? 'Ответ на комментарий @<b>'+replyName+'</b>' : 'Ваш комментарий:';

		var form = document.createElement('form');
		var title = 'Редактирование комментария';

		form.classList = 'edit-comment-form';
		form.action = this.href;
		form.name = 'edit';
		form.method = 'post';
		formText = document.createElement('textarea');
		formText.classList = 'form-control';
		formText.name = 'message';
		formText.innerText = this.parentElement.querySelector('.comment-block-text').innerText;
		form.appendChild(formText);
		formText.blur();

		modalHandler(modalContainer, form, title, subTitle);

		formText.addEventListener('input', function (e) {
			if (this.value !== '' && this.classList.contains('warning')) {
				this.classList.remove('warning');
				statusMsg.textContent = '';
			}
			submitModal.disabled = (this.value) ? false : true;

			if (this.scrollHeight < document.body.clientHeight - 300) {
				this.style.height = "24px";
				this.style.height = (this.scrollHeight)+24+"px";
				this.style.resize = 'none';
				this.style.overflowY = 'hidden';
			} else {
				this.style.resize = 'vertical';
				this.style.overflowY = 'auto';
			}
		});

	}

	deleteCommentEvent = function (e) {
		e.preventDefault();
		targetLink = this;

		const title = 'Удалить комментарий?';
		var subTitle = 'Ваш комментарий:';
		var form = document.createElement('form');

		form.classList = 'delete-comment-form';
		form.name = 'delete';
		form.action = this.href;
		form.method = 'post';
		formText = document.createElement('textarea');
		formText.classList = 'form-control';
		formText.disabled = true;
		formText.innerText = this.parentElement.querySelector('.comment-block-text').innerText;
		form.appendChild(formText);
		submitModal.textContent = 'Удалить';

		modalHandler(modalContainer, form, title, subTitle);
	}


	submitModal.addEventListener('click', function (e){
		e.preventDefault();
		const csrf = 'csrfmiddlewaretoken', token = document.getElementsByName(csrf)[0].value;
		var params = csrf + '=' + token;
		var form =  modalContainer.querySelector('form');
		if (form.name == 'edit') {
			var msg = form.querySelector('textarea').value;
			params += '&message='+msg;
		}
		//var action = modalContainer.querySelector('form').action;
		ajaxSend(form.action, params, form.method, function(data){
			statusMsg.classList = 'message-status '+data['status'];
			statusMsg.textContent = data['message'];

			if (form.name == 'edit' && msg) {
				closeModal.classList.add('btn-primary');
				closeModal.textContent = 'Закрыть';
				formText.disabled = true;
				submitModal.classList = 'hidden';

				formText.classList.add(data['status']);
				var comment = targetLink.parentNode.querySelector('.comment-block-text');
				comment.innerText = msg;
			}

			if (form.name == 'delete' && data['status'] == 'success') {
				var modal = bootstrap.Modal.getInstance(modalContainer);
				modal.hide();
				// Добавим текст об удалении комментария на его место
				targetLink.parentNode.classList.add('deleted');
				targetLink.parentNode.innerHTML = data['message'];
				//targetLink.removeEventListener('click', deleteCommentEvent);
				changeCommentsCounter(-1);
			}

		}, modalContainer);

	});


	modalContainer.addEventListener('hidden.bs.modal', function (e) {
		if (statusMsg) {
			statusMsg.classList = 'message-status';
			statusMsg.textContent = '';
		}

		if (closeModal) {
			closeModal.classList = 'btn btn-cancel';
			closeModal.textContent = 'Отменить';
		}

		if (submitModal) {
			submitModal.classList = 'btn btn-primary';
			submitModal.textContent = 'Сохранить';
			submitModal.disabled = false;
		}
		// Удаление элементов внутри тела модального окна
		var modalBody = this.querySelector('.modal-body');
		while (modalBody.firstChild) {
			modalBody.removeChild(modalBody.firstChild);
		}
	});


	function changeCommentsCounter(i) {
		var commentsCounter = document.querySelector('.comments-counter span');
		commentsCounter.innerText = Number(commentsCounter.innerText)+i;
	}

	function toggleCommentForm(el, clearInnerText=false, toggle=false) {
		var textBlock = el.querySelector('textarea');
		if (textBlock) {
			if (toggle) el.classList.toggle('hidden');
			!el.classList.contains('hidden') && textBlock.focus();
			if (clearInnerText) {
				textBlock.value = textBlock.innerText;
			} else {
				textBlock.setSelectionRange(textBlock.value.length,textBlock.value.length);
				//var replyName = textBlock.innerText;
				//if (replyName) textBlock.value += ', ';

			}
		}
	}


	function textareaResize(e) {
		// будем хранить длину строки ввода до начала переноса в свойстве col
		var textLength = this.cols;
		this.parentNode.dataset.value = this.value;

		if (this.scrollHeight > minTextareaHeight) {
			if (textLength < 2) this.cols = this.textLength - 1;
			this.style.flex = 'auto';

			this.nextElementSibling.style.flex = '100%';
			this.style.height = "5px";
			this.style.height = (this.scrollHeight)+"px";
		}

		if (textLength > 1 && this.textLength < textLength) {
			this.cols = 1;
			this.style.flex = '';
			this.nextElementSibling.style.flex = '';
			this.style.height = minTextareaHeight + "px";
		}
	}


	const replyCommentLink = document.querySelectorAll('.reply-link');
	replyCommentLink.forEach( (item) => {
		item.addEventListener('click', replyCommentEvent);
	});

	const editCommentLink = document.querySelectorAll('.edit-link');
	editCommentLink.forEach( (item) => {
		if (item.href) {
			item.addEventListener('click', editCommentEvent);
		} else {
			item.style.visibility = 'hidden';
		}
	});

	const deleteCommentLink = document.querySelectorAll('.delete-link');
	deleteCommentLink.forEach( (item) => {
		if (item.href) {
			item.addEventListener('click', deleteCommentEvent);
		} else {
			item.style.visibility = 'hidden';
		}
	});

	// Обновляем данные формы при сохранении
	const reviewForm = document.querySelector('.review-form[name=review]');
	if (reviewForm) {
		reviewForm.addEventListener('submit', submitCommentEvent);

		// Подключаем обработчик события ввода текста в поле сообщения
		const textarea = reviewForm.querySelector('textarea[name=message]');
		var minTextareaHeight = textarea.offsetHeight;
		textarea.addEventListener('input', textareaResize);
	}

