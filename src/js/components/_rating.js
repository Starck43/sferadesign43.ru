/*
* Обработчик нажатия на рейтинг
*/
	const ratingForm = document.querySelector('form[name=rating]');

	if (ratingForm) {

		sendRatingToServer = function(e){
			var params = new URLSearchParams(new FormData(e)).toString();
			ajaxSend(e.action, params, 'post', rateRender);
		}


		// Рендер шаблона
		rateRender = function(data) {
			var message = '<h3>Рейтинг успешно установлен!</h3><p>\
							Автор проекта: <b>"'+data['author']+'" </b><br/>\
							Ваша оценка: <b>'+data['score']+'.0</b><br/>\
							Общий рейтинг: <b>'+data['score_avg'].toFixed(1)+'</b></p>';

			alertHandler(message); // функция обработки сообщений

			ratingForm.setAttribute('value', data['score']);

			const summaryScore = document.querySelector('.summary-score');
			if (summaryScore) {
				summaryScore.innerHTML = data['score_avg'].toFixed(1);
				var userScore = document.createElement('div');
				userScore.innerHTML = 'Ваша оценка: <b>'+data['score']+'.0</b>';
				summaryScore.after(userScore);
			}
		}

		submitRating = function(e) {
			var score = ratingForm.getAttribute('value');
			if (score) {
				e.preventDefault();
				var message = '<h3>Внимание!</h3><p>Вы уже проголосовали, Ваша оценка: <b>'+score+'.0</b></p>';
				alertHandler(message); // функция обработки сообщений
			} else
			if (e.target.localName == 'input') {
				var score = e.target.value;
				var form = this;
				if (score < 4) {
					const title = 'Подтверждение';
					var node = document.createElement('div');
					var message =  '<h3>Внимание!</h3>\
									<p>Вы выбрали оценку: <b>'+String(score)+'.0</b><br/>Уверены что хотите оставить ее?</p>\
									<hr>\
									<div class="d-grid gap-2 d-md-flex justify-content-md-end">\
										<button class="btn btn-cancel me-md-2" type="button" data-bs-dismiss="alert">Отмена</button>\
										<button class="btn btn-primary ml-2" type="submit">Подтвердить</button>\
									</div>';

					var alertNode = alertHandler(message); // функция обработки сообщений
					if (alertNode) {
						alertNode.querySelector('.btn-cancel').addEventListener('click', closeAlert);
						alertNode.querySelector('button[type=submit]').addEventListener("click", function(){
							sendRatingToServer(form);
						});
					}

				} else {
					sendRatingToServer(form);
				}
			}
		}

		ratingForm.addEventListener("click", submitRating);
		//ratingForm.addEventListener("change", saveRating);

	}
