/*
* Обработчик нажатия на рейтинг
*/
	const ratingForm = document.querySelector('form[name=rating]');

	if (ratingForm) {

		sendRatingToServer = function(form){
			var params = new URLSearchParams(new FormData(form)).toString();
			ajaxSend(form.action, params, 'post', rateRender);
		}


		// Рендер шаблона
		rateRender = function(data) {
			var message = '<h3>Рейтинг успешно установлен!</h3><p>\
							Автор проекта: <b>"'+data['author']+'" </b><br/>\
							Ваша оценка: <b>'+data['score']+'.0</b><br/>\
							Общий рейтинг: <b>'+data['score_avg'].toFixed(1)+'</b></p>';

			alertHandler(message); // функция обработки сообщений

			ratingForm.setAttribute('value',data['score']);

			// Обновим средний рейтинг и ниже добавим строку с сохраненной оценкой
			const summaryScore = document.querySelector('.summary-score');
			if (summaryScore) {
				summaryScore.innerHTML = data['score_avg'].toFixed(1);
				var userScore = document.createElement('div');
				userScore.innerHTML = 'Ваша оценка: <b>'+data['score']+'.0</b>';
				summaryScore.after(userScore);
			}
		}

		submitRating = function(e) {
			var score = ratingForm.getAttribute('value'); // Если у формы уже стоит значение value, то рейтинг установлен
			if (score) {
				e.preventDefault();
				var message = '<h3>Внимание!</h3><p>Вы уже проголосовали.<br>Ваша оценка: <b>'+score+'.0</b></p>';
				alertHandler(message); // функция обработки сообщений
			} else
			if (e.target.localName == 'input') {
				score = e.target.value;
				var form = this;
				if (score < 4) {
					const title = 'Подтверждение';
					var node = document.createElement('div');
					var message =  '<h3>Внимание!</h3>\
									<p>Вы выбрали оценку: <b>'+String(score)+'.0</b><br/>Уверены что хотите оставить ее?</p>\
									<hr>\
									<div class="action-block text-right">\
										<button class="btn btn-cancel" type="button" data-bs-dismiss="alert">Отмена</button>\
										<button class="btn btn-primary ml-2" type="submit">Подтвердить</button>\
									</div>';

					var alertNode = alertHandler(message); // функция обработки сообщений
					if (alertNode) {
						alertNode.addEventListener('closed.bs.alert', function(){
							if (! ratingForm.getAttribute('value')) {
								var avg_score = Number(ratingForm.getAttribute('average').charAt(0));
								if (avg_score >= 1) {
									let i = 5-avg_score;
									ratingForm.star[i].checked = true;
								}
							}
						});

						alertNode.querySelector('button[type=submit]').addEventListener("click", function(){
							sendRatingToServer(ratingForm);
						});
					}

				} else {
					sendRatingToServer(ratingForm);
				}
			}
		}

		ratingForm.addEventListener("click", submitRating);
		//ratingForm.addEventListener("change", saveRating);

	}
