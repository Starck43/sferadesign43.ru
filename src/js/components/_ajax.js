
//var csrftoken =document.getElementsByName('csrfmiddlewaretoken')[0].value;

function ajaxSend(url, params='') {
	// Отправляем запрос
	fetch(`${url}?${params}`, {
		method: 'POST',
		headers: {
			'X-Requested-With': 'XMLHttpRequest', // it's nesessary for correct checking request.is_ajax() on server
			'Content-Type': 'application/x-www-form-urlencoded',
			//'X-CSRFToken': csrftoken,
		},
	})
	.then(response => response.json())
	.then(json => render(json))
	.catch(error => console.error(error))
}
