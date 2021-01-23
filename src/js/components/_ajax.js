
//var csrftoken =document.getElementsByName('csrfmiddlewaretoken')[0].value;

function ajaxSend(url, params='', method='post', renderFunc=render) {
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
		var message =  '<h3>Ошибка!</h3><p>Что-то пошло не так...</p>';
		alertHandler(message);
	})
}


// Обработчик закрытия окон с сообщениями
alertHandler = function(html){
	if (alertContainer) {
		var alertNode = alertContainer.querySelector('.alert');
		if (alertNode) {
			var body = alertNode.querySelector('.alert-body');
			body.innerHTML = html;
		} else {
			alertNode = document.createElement('div');
			alertNode.className = 'alert alert-secondary fade show';
			alertNode.setAttribute('role','alert');
			alertNode.innerHTML =  '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>\
									<div class="alert-body blockquote">'+html+'</div>';
			alertContainer.append(alertNode);

			var alert = new bootstrap.Alert(alertNode);
			var closeBtn = alertNode.querySelector('.btn-close');
			closeBtn && closeBtn.addEventListener('click', function () {
				window.removeEventListener('keydown', (e)=>{});
				alert.close();
			});
			alert && window.addEventListener('keydown', (e)=>{
				(e.keyCode == 27) && alert.close();
			});
			alertNode.addEventListener('closed.bs.alert', function () {
				alertContainer.classList.add('hidden');
			});
		}
		alertContainer.classList.remove('hidden');
	}
}
