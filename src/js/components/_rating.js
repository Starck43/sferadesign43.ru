/*
* Обработчик изменения рейтинга
*/
	const ratingForm = document.querySelector('form[name=rating]');
	if (ratingForm) {
		// Получаем данные из формы
		var score = ratingForm.getAttribute('value');
		if (score) {
			ratingForm.addEventListener("click", function (e) {
				var message = '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>\
								<h3>Внимание!</h3><p>Вы уже проголосовали, Ваша оценка: <b>'+score+'.0</b></p>';

				alertHandler(message); // функция обработки сообщений
				e.preventDefault();
			});
		} else {
			ratingForm.addEventListener("change", function (e) {
				let params = new URLSearchParams(new FormData(this)).toString();
				ajaxSend(this.action, params);
			});
		}
	}
