	const alertContainer = document.querySelector('#alertContainer');

	closeAlert = function(e, alert) {
		//window.removeEventListener('keydown', (e)=>{});
		//var alert = bootstrap.Alert.getInstance(alertContainer.querySelector('.alert'));
		// if (alert) alert.close();
	}

	// Обработчик закрытия всплывающих инфо-окон
	alertHandler = function (html) {
		if (alertContainer) {
			alertContainer.classList.remove('hidden');
			document.body.classList.add('modal-open');

			var alertNode = alertContainer.querySelector('.alert');
			if (alertNode) {
				var body = alertNode.querySelector('.alert-body');
				body.innerHTML = html;
			} else {
				alertNode = document.createElement('div');
				alertNode.className = 'alert show fade';
				alertNode.innerHTML =  '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>\
										<div class="alert-body">'+html+'</div>';
				alertContainer.append(alertNode);

				var alert = bootstrap.Alert.getInstance(alertNode);
				if (!alert) alert = new bootstrap.Alert(alertNode,{});

				alertNode.addEventListener('close.bs.alert', function () {
					alertNode.classList.remove('show');
					document.body.classList.remove('modal-open');
					window.removeEventListener('keydown', ()=>{});
				});

				alertNode.addEventListener('closed.bs.alert', function () {
					alertContainer.classList.add('hidden');
				});

				//alertNode.querySelector('.btn-close').addEventListener('click', (alert)=> closeAlert(alert));
				//var cancelBtn = alertNode.querySelector('.btn-cancel');
				//cancelBtn && cancelBtn.addEventListener('click', closeAlert);

				window.addEventListener('keydown', (e)=>{
					(e.keyCode == 27) && alert.close();
				});
			}
			return alertNode;

		} else return null;
	}

