
	function ajaxSend(url, params='', method='post', renderFunc=render, alertModal=null) {
		// Отправляем запрос
		fetch(`${url}?${params}`, {
			method: method,
			headers: {
				'X-Requested-With': 'XMLHttpRequest', // it's nesessary for correct checking request.is_ajax() on server
				'Content-Type': 'application/x-www-form-urlencoded',
				//'X-CSRFToken': csrfmiddlewaretoken,
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
