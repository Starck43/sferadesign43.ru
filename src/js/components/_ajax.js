
	function ajaxSend(url, params='', method='post', renderFunc=render, alertModal=null) {
		// Отправляем запрос
		fetch(`${url}?${params}`, {
			method: method,
			headers: {
				'X-Requested-With': 'XMLHttpRequest', // it's nesessary for correct checking request.is_ajax() on server
				'Content-Type': 'application/x-www-form-urlencoded',
				//'X-CSRFToken': csrftoken,
			},
		})
		.then(response => response.json())
		.then(json => renderFunc(json))
		.catch(function(error){
			console.log(error);
			if (alertModal) {
				const alertBlock = alertModal.querySelector('.message-status');
				alertBlock.classList.add('error');
				alertBlock.textContent = 'Внутренняя ошибка: '+error.name;
			}
			else {
				var message =  '<h3>Ошибка!</h3><p>Что-то пошло не так...</p>';
				alertHandler(message);
			}
		})
	}

	closeAlert = function(e) {
		window.removeEventListener('keydown', (e)=>{});
		var alert = bootstrap.Alert.getInstance(alertContainer.querySelector('.alert'));
		if (alert) alert.close();
	}

	// Обработчик закрытия окон с сообщениями
	alertHandler = function (html) {
		if (alertContainer) {
			alertContainer.classList.remove('hidden');
			document.body.classList.add('modal-open');

			var alertNode = alertContainer.querySelector('.alert');
			if (alertNode) {
				var body = alertNode.querySelector('.alert-body');
				body.innerHTML = html;
			} else {
				alertNode = document.createElement('div');
				alertNode.className = 'alert show fade';
				alertNode.innerHTML =  '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>\
										<div class="alert-body">'+html+'</div>';
				alertContainer.append(alertNode);

				var alert = bootstrap.Alert.getInstance(alertNode);
				if (!alert) alert = new bootstrap.Alert(alertNode,{});

				alertNode.addEventListener('close.bs.alert', function () {
					alertNode.classList.remove('show');
					document.body.classList.remove('modal-open');
				});

				alertNode.addEventListener('closed.bs.alert', function () {
					alertContainer.classList.add('hidden');
				});

				alertNode.querySelector('.btn-close').addEventListener('click', closeAlert);

				window.addEventListener('keydown', (e)=>{
					(e.keyCode == 27) && alert.close();
				});
			}
			return alertNode;

		} else return null;
	}


	modalHandler = function (modalNode, node=null, headerTitle='', subTitle='') {
		if (modalNode) {
			if (headerTitle) {
				var modalTitle = modalNode.querySelector('.modal-title');
				modalTitle.innerHTML = headerTitle;
			}
			var modalBody = modalNode.querySelector('.modal-body');
			if (node) {
				if (subTitle) modalBody.innerHTML = '<div class="sub-title">'+subTitle+'</div>';
				modalBody && modalBody.appendChild(node);

				if (modalBody.querySelector('[data-type=question]')) {
					submitModal.textContent = 'Да';
				}
			}

			var modal = bootstrap.Modal.getInstance(modalContainer);
			if (!modal) modal = new bootstrap.Modal(modalNode,{});
			modal.show();

			var closeBtn = modalNode.querySelectorAll('button[data-bs-dismiss=modal]');
			closeBtn.forEach( (item) => {
				item.addEventListener('click', function () {
					modal.hide();
				});
			});

			modalNode.addEventListener('shown.bs.modal', function (e) {
				var textEl = this.querySelector('textarea');
				if (textEl) {
					textEl.focus();
					textEl.setSelectionRange(textEl.value.length,textEl.value.length);
				}
			});

		}

	}
