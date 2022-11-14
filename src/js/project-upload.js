
document.addEventListener("DOMContentLoaded", function() {
	//= components/_ajax.js

	const modalContainer = document.getElementById('progressModal');
	const form = document.querySelector('#portfolio_form');
	var exhibition = form.querySelector('select[name=exhibition]');
	var nominations= form.querySelector('.field-nominations');
	var categories = form.querySelector('.field-categories');
	var attributes = form.querySelector('.field-attributes');
	var images 	= form.querySelectorAll('.field-images img');

	if (exhibition.value == ""){
		nominations && nominations.classList.add('hidden');
		attributes && attributes.classList.add('hidden');
	} else {
		categories && categories.classList.add('hidden');
	}

	exhibition && exhibition.addEventListener('change', function(e){
		if (e.target.value != "") {
			nominations && nominations.classList.remove('hidden');
			attributes && attributes.classList.remove('hidden');
			categories && categories.classList.add('hidden');
		} else {
			categories && categories.classList.remove('hidden');
			attributes && attributes.classList.add('hidden');
			nominations && nominations.classList.add('hidden');
		}
	})

	images.forEach(function(image) {
		image.addEventListener('click', function(e){
			e.target.parentNode.classList.toggle('selected');
		})
	})

	form && form.addEventListener('submit', function(e){
		var html = '0%';
		modalHandler(html);
		ajax(e);
	})


	// Обработчик закрытия всплывающих инфо-окон
	modalHandler = function (percent) {
		if (modalContainer) {
			modalContainer.addEventListener('show.bs.modal', function (event) {
				var bar = modalContainer.querySelector('.progress-bar');
				bar.textContent = percent;
			})
			var modal = new bootstrap.Modal(modalContainer);
			modal.show()
		}
	}

	function ajax(e) {
		e.preventDefault();
		var data = new FormData(form.get(0));
		console.log(data);

		//ajax upload
		var xhr=new XMLHttpRequest();
		console.log(xhr);

		xhr.addEventListener('load', function (e) {
			if(xhr.status == 0 || xhr.status >= 400){
				return this.error(xhr);
			}

			this.render_progress(100);

			var url;
			var content_type = xhr.getResponseHeader('Content-Type');

			// make it possible to return the redirect URL in
			// a JSON response
			if (content_type.indexOf('application/json') !== -1) {
				var response = $.parseJSON(xhr.responseText);
				url = response.location;
			}
			else {
				url = this.options.redirect_url;
			}
			window.location.href = url;
		});

		//The upload progress callback
		xhr.upload.addEventListener('progress', function (e) {
			//The length measurement returns a Boolean value, 100% is false, otherwise true
			if(e.lengthComputable){
				var progress=(e.loaded/e.total)*100;
				console.log(progress);
			}
		});

		console.log(window.location.href);
		xhr.open(form.attr('method'), window.location.href);
		xhr.setRequestHeader('X-REQUESTED-WITH', 'XMLHttpRequest');
		xhr.send(data);

	}

})
