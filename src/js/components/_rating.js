/*
* Обработчик нажатия на рейтинг
*/
	const ratingForm = document.querySelector('form[name=rating]');

	if (ratingForm) {
		// Получаем данные из формы
		ratingForm.addEventListener("click", function (e) {
			var score = ratingForm.getAttribute('value');
			if (score) {
				var message = '<h3>Внимание!</h3><p>Вы уже проголосовали, Ваша оценка: <b>'+score+'.0</b></p>';
				alertHandler(message); // функция обработки сообщений
				e.preventDefault();
			}
		});

		ratingForm.addEventListener("change", function (e) {
			var score = ratingForm.getAttribute('value');
			if (!score) {
				var params = new URLSearchParams(new FormData(this)).toString();
				ajaxSend(this.action, params, 'post', rateRender);
			} else {
				ratingForm.click();
			}
		});
	}
