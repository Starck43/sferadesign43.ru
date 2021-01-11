// Filter movies
const forms = document.querySelector('form[name=filter]');

forms.addEventListener('submit', function (e) {
	// Получаем данные из формы
	e.preventDefault();
	let url = this.action;
	let params = new URLSearchParams(new FormData(this)).toString();
	ajaxSend(url, params);
});

function render(data) {
	// Рендер шаблона
	let template = Hogan.compile(html);
	let output = template.render(data);

	const div = document.querySelector('.left-ads-display>.row');
	div.innerHTML = output;
}

