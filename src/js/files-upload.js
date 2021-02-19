
document.addEventListener("DOMContentLoaded", function() {
	var node = document.createElement('<div>');
	node.id = 'alertContainer';
	node.classList = 'hidden centered';
	document.body.append(node);

	//= components/_ajax.js

	const uploadForm = document.querySelector('input[type=submit]');
	if (uploadForm) {

		uploadForm.forEach( (button) => {
			button.addEventListener('submit', function (e) {
				e.preventDefault();
				params = new URLSearchParams(new FormData(this)).toString();
				ajaxSend(window.location.href, params, this.method, uploadRender);
			})
		});

		// Рендер шаблона
		uploadRender = function(data) {
			var message = '<h3>Загрузка файлов в портфолио ...</h3>\
			<progress id="progressBar" value="0" max="100" style="width:100%;"></progress>';
			alertHandler(message); // функция обработки сообщений
		}

	}

});
