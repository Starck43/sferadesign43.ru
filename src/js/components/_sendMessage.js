
	const modalContainer = document.getElementById('feedbackContainer'),
		feedbackForm 	 = modalContainer.querySelector('form[name=feedback]');

	if (modalContainer && feedbackForm) {
		const submitBtn 	= modalContainer.querySelector('.send-button[type=submit]');
		const statusWrapper = modalContainer.querySelector('.status-wrapper');
		const loading 		= modalContainer.querySelector('.loading-block');

		var modal = bootstrap.Modal.getInstance(modalContainer);
		if (!modal) modal = new bootstrap.Modal(modalContainer);

		modalContainer.addEventListener('hidden.bs.modal', function (event) {
			updateStatus('reset');
		})

		feedbackForm.addEventListener('submit', function(e){
			e.preventDefault();

			updateStatus('loading');

			var params = new URLSearchParams(new FormData(this)).toString();
			ajaxSend(this.action, params, 'post', jsonHandler, modalContainer);
		});

		function jsonHandler(data) {
			updateStatus(data['status']);
		}

		function updateStatus(status) {
			let loadedText = 'OK';
			var statusInner = (statusWrapper.firstElementChild.tagName == 'DIV') ? statusWrapper.firstElementChild : statusWrapper;

			switch (status) {
				case 'loading':
					submitBtn.disabled = true;
					feedbackForm.classList.add('disabled');
					loading.innerHTML = 'Отправка сообщения... <div class="spinner-border ms-1" role="status" aria-hidden="true"></div>';
					loading.classList.add('show');
					break

				case 'error':
					loadedText = 'Ошибка';
				case 'success':
					loading.innerHTML = `Отправка сообщения... <div class="message-status ${status} ms-1"><b>${loadedText}</b></div>`;
					statusInner.insertAdjacentHTML('afterBegin', '<span>' +
						(status=='success'
						? '<h5>Сообщение успешно отправлено!</h5>Мы ответим Вам в ближайшее время. Спасибо за обращение'
						: '<h5>Произошла ошибка!</h5>Попробуйте связаться другим удобным способом') + '</span>');
					statusWrapper.classList.add('show');
					statusWrapper.classList.remove('hidden');
					break

				case 'reset':
					submitBtn.disabled = false;
					loading.innerHTML = '';
					loading.classList.remove('show');
					statusWrapper.classList.remove('show');
					statusWrapper.classList.add('hidden');
					feedbackForm.classList.remove('disabled');
					statusWrapper.firstElementChild
					statusInner.firstElementChild.remove();
			}

		}

	}