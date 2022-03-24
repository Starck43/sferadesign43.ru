
	// Форма модального окна
	modalHandler = function (modalNode, node=null, headerTitle='', subTitle='') {
		if (modalNode) {
			if (headerTitle) {
				var modalTitle = modalNode.querySelector('.modal-title');
				modalTitle.innerHTML = headerTitle;
			}
			var modalBody = modalNode.querySelector('.modal-body');
			if (node) {
				if (subTitle) modalBody.innerHTML = '<div class="sub-title">'+subTitle+'</div>';
				modalBody && modalBody.appendChild(node);

				if (modalBody.querySelector('[data-type=question]')) {
					submitModal.textContent = 'Да';
				}
			}

			var modal = bootstrap.Modal.getInstance(modalNode);
			if (!modal) modal = new bootstrap.Modal(modalNode,{});
			modal.show();

			var closeBtn = modalNode.querySelectorAll('button[data-bs-dismiss=modal]');
			closeBtn.forEach( (item) => {
				item.addEventListener('click', function () {
					modal.hide();
				});
			});

			modalNode.addEventListener('shown.bs.modal', function (e) {
				var textEl = this.querySelector('textarea');
				if (textEl) {
					textEl.focus();
					textEl.setSelectionRange(textEl.value.length,textEl.value.length);
				}
			});

		}
	}
