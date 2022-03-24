
//= ../plugins/peppermint/peppermint.js

document.addEventListener("DOMContentLoaded", function() {

	//= components/_inViewport.js
	//= components/_slider.js


	// обработчик раскрытия всего содержимого при нажатии на кнопку "Читать далее" при наличии блока описания
	const excerptBlock = document.querySelector('.description');
	if (excerptBlock) {
		var excerptBlock_h = excerptBlock.scrollHeight;
		if (excerptBlock_h/300 > 1.2) {
			//excerptBlock.style.height = (excerptBlock_h+30) + 'px';
			let div = document.createElement('a');
			div.className = "read-more-link";
			//div.innerHTML = "Read more";
			excerptBlock.append(div);
			excerptBlock.classList.add('brief');
		}

		excerptBlock.lastElementChild && excerptBlock.lastElementChild.addEventListener('click', (e) => {
			//var parentBlock = e.target.parentNode;
			excerptBlock.classList.toggle('brief');
			excerptBlock_h = excerptBlock.scrollHeight + 30;
			excerptBlock.style.height = ((excerptBlock.classList.contains('brief')) ? 300 : excerptBlock_h) + 'px';
		});
	}

});
