/*
* Обработчик изменения рейтинга
*/
	const rating = document.querySelector('form[name=rating]');
	if (rating) {
		rating.addEventListener("change", function (e) {
			// Получаем данные из формы
			score = this.getAttribute('value');
			if (score) {
				alert("Вы уже поставили оценку "+score);
				e.preventDefault();
			}
			else if (this.method == 'get') {
				alert("Функция доступна только для зарегистрированных пользователей!");
			}
			else {
				var data = new FormData(this);
				fetch(`${this.action}`, {
					method: 'POST',
					body: data
				})
				.then(response => alert("Рейтинг успешно установлен!"))
				.catch(error => alert("Внутренняя ошибка!"))
			}
		});
	}