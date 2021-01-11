
var referenceSubmit = null;

var submitEvent = function (e) {
	e.preventDefault();
	referenceSubmit = e.target;
	let url = e.target.action;
	let params = new URLSearchParams(new FormData(e.target)).toString();
	//this.after(newNode);
	ajaxSend(url, params);
}

var replyEvent = function (e) {
	e.preventDefault();
	var link = e.target;
	// если ниже нет формы, то клонируем из основной
	if (!link.nextSibling || link.nextSibling.localName !== 'form') {
		const reviewForm = document.querySelector('.review-form');
		var cloneForm = reviewForm.cloneNode(true);
		cloneForm.classList = 'reply-form form-control hidden';
		cloneForm.querySelector('button').className = 'btn btn-link'; // заменим тип конпки на ссылку для ответов
		link.after(cloneForm);

		var parentEl = cloneForm.querySelector('.parent-control');
		var groupEl = cloneForm.querySelector('.group-control');
		var textEl = cloneForm.querySelector('textarea');
		textEl.className = 'text-control';
		parentEl.value = Number(link.dataset.id);
		groupEl.value = Number(link.dataset.group);
		textEl.setAttribute('value', link.dataset.author);
		textEl.placeholder = 'Ваш ответ...';
		cloneForm.addEventListener('submit', submitEvent); // Повесим событие на сохранение формы
		textEl.addEventListener('input', textareaResize);

	}
	// Сделаем клон формы видимым без очистки содержимого поля ввода
	toggleCommentForm(link.nextSibling, false, true);

}

const replyCommentLink = document.querySelectorAll('.reply-link');
replyCommentLink.forEach( (item) => {
	item.addEventListener('click', replyEvent);
});

// Обновляем данные формы при сохранении
const reviewForm = document.querySelector('.review-form[name=review]');
reviewForm && reviewForm.addEventListener('submit', submitEvent);


// Подключаем обработчик события ввода текста в поле сообщения
const textarea = reviewForm.querySelector('textarea[name=message]');
var minTextareaHeight = textarea.offsetHeight;
textarea.addEventListener('input', textareaResize);


// Рендер шаблона
function render(data) {

	var newNode = document.createElement('article'),
		parent = group = data['id'],
		datetime = new Date().toLocaleDateString();

	newNode.className = 'porfolio-comment';
	if (referenceSubmit.parentNode.classList.contains(newNode.className)) {
		toggleCommentForm(referenceSubmit, true, true); //скроем форму ввода сообщения и почистим его область текста
		newNode.classList.add('subcomment');
		referenceSubmit.parentNode.after(newNode);
		// если подкомментарий, то родителем будет являться текущий id родительского комментария
		group = data['group'];
	} else {
		toggleCommentForm(referenceSubmit, true, false); //скроем форму ввода сообщения и почистим его область текста
		referenceSubmit.after(newNode);
	}

	var html = '<div class="comment-block">\
				<h3 class="comment-block-author">'+data['author']+'</h3>\
				<div class="comment-block-datetime">'+datetime+'</div>\
				<p class="comment-block-text">'+data['message']+'</p>\
			</div>\
			<a class="reply-link" data-id="'+parent+'" data-group="'+group+'" data-author="'+data['author']+'">Ответить</a>';
	newNode.innerHTML = html;

	var commentsCounter = document.querySelector('.comments-counter span');
	commentsCounter.innerText = Number(commentsCounter.innerText)+1;

	var replyLink = newNode.querySelector('.reply-link');
	replyLink && replyLink.addEventListener('click', replyEvent, {passive: true});

}


function toggleCommentForm(el, clearInnerText=false, toggle=false) {
	var textBlock = el.querySelector('textarea');
	if (toggle) el.classList.toggle('hidden');
	!el.classList.contains('hidden') && textBlock.focus();
	if (clearInnerText) {
		textBlock.value = textBlock.innerText;
	} else {
		var replyName = textBlock.getAttribute('value');
		if (replyName) textBlock.innerText = replyName + ', ';
	}
}

function textareaResize(e) {
	// будем хранить длину строки ввода до начала переноса в свойстве col
	var textLength = this.cols;
	this.parentNode.dataset.value = this.value;

	if (this.scrollHeight > minTextareaHeight) {
		if (textLength < 2) this.cols = this.textLength - 1;
		this.style.flex = 'auto';

		this.nextElementSibling.style.flex = '100%';
		this.style.height = "5px";
		this.style.height = (this.scrollHeight)+"px";
	}

	if (textLength > 1 && this.textLength < textLength) {
		this.cols = 1;
		this.style.flex = '';
		this.nextElementSibling.style.flex = '';
		this.style.height = minTextareaHeight + "px";
	}
}


