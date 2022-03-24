
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
		ajax();
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

	function ajax() {
		var files=document.querySelector('input[name=files]').files;
		if (files) {
			//get data less than 1M
			var data = new FormData();
			for(var i=0;i<files.length;i++)
			{
				data.append("file"+i+":",files[i]);
			}
			console.log(data);
		}

		//ajax upload
		var xhr=new XMLHttpRequest();
		console.log(xhr);
		xhr.onreadystatechange = function(){
			if(xhr.readyState==4){
				if(xhr.status==200){
					console.log(xhr.responseText);
				}
			}
		}

		var progress; //=document.querySelector(".progress-bar");
		//The upload progress callback
		xhr.upload.addEventListener('progress', function (e) {

			//The length measurement returns a Boolean value, 100% is false, otherwise true
			if(e.lengthComputable)
			{
				progress=(e.loaded/e.total)*100;
				console.log(progress);
			}
		});

	}

})
