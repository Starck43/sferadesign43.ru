/*
 * bootstrap-uploadprogress
 * github: https://github.com/jakobadam/bootstrap-uploadprogress
 *
 * Copyright (c) 2015 Jakob Aarøe Dam
 * Version 1.0.0
 * Licensed under the MIT license.
 */
(function($){
	"use strict";

	$.support.xhrFileUpload = !!(window.FileReader && window.ProgressEvent);
	$.support.xhrFormData = !!window.FormData;

	if(!$.support.xhrFileUpload || !$.support.xhrFormData){
		// skip decorating form
		return;
	}

	var Uploadprogress = function(element, options){
		this.options = options;
		this.$element = $(element);
	};

	Uploadprogress.prototype = {

		constructor: function() {
			this.$form = this.$element;
			this.$modal = $(this.options.template);
			this.$modal_message = this.$modal.find('.modal-message');
			this.$modal_title = this.$modal.find('.modal-title');
			this.$modal_footer = this.$modal.find('.modal-footer');
			this.$modal_bar = this.$modal.find('.progress-bar');

			this.$form.on('submit', $.proxy(this.submit, this));
			this.$modal.on('hidden.bs.modal', $.proxy(this.reset, this));
		},

		reset: function(){
			this.$modal_message = this.$modal_title.text('');
			this.$modal_bar.removeClass('bg-danger');

			if (this.xhr) this.xhr.abort();
		},

		submit: function(e) {
			var filesAdded = this.$form.find(':file:visible').get(0).files.length;
			var filesDeleted = this.$form.find(':input:visible:checked').length;
			if (filesAdded - filesDeleted > 0) {
				e.preventDefault();

				this.$modal.modal({
					show: true,
				   //backdrop: 'static',
				});

				var form = this.$form;
				var data = new FormData(form.get(0));
				var xhr = new XMLHttpRequest(); // The native XMLHttpRequest for the progress event
				this.xhr = xhr;

				xhr.upload.addEventListener('progress', $.proxy(this.progress, this));
				xhr.addEventListener('load', $.proxy(this.success, this, xhr));
				xhr.addEventListener('error', $.proxy(this.error, this, xhr));
				//xhr.addEventListener('abort', function(){});

				xhr.open(form.attr('method'), window.location.href);
				xhr.setRequestHeader('X-REQUESTED-WITH', 'XMLHttpRequest');
				xhr.send(data);
			}
		},

		success: function(xhr) {
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
		},

		// handle form error
		// we replace the form with the returned one
		error: function(xhr){
			this.$modal_message.text('Возникла ошибка при загрузке файлов!');
			this.$modal_bar.addClass('bg-danger');

			// Replace the contents of the form, with the returned html
			if(xhr.status === 422){
				var new_html = $.parseHTML(xhr.responseText);
				this.replace_form(new_html);
				this.$modal.modal('hide');
			}
			// Write the error response to the document.
			else {
				var response_text = xhr.responseText;
				var content_type = xhr.getResponseHeader('Content-Type');

				if(content_type.indexOf('text/plain') !== -1){ // if plain text
					response_text = '<pre>' + response_text + '</pre>';
				}
				document.write(xhr.responseText);
			}
		},

		render_progress: function(percent){
			this.$modal_bar.attr('aria-valuenow', percent);
			this.$modal_bar.css('width', percent + '%');
			this.$modal_bar.text(percent + '%');
		},

		progress: function(e){
			var percent = Math.round((e.loaded / e.total) * 100);
			this.render_progress(percent);
		},

		// replace_form replaces the contents of the current form
		// with the form in the html argument.
		// We use the id of the current form to find the new form in the html
		replace_form: function(html){
			var new_form;
			var form_id = this.$form.attr('id');
			if(form_id !== undefined){
				new_form = $(html).find('#' + form_id);
			}
			else{
				new_form = $(html).find('form');
			}

			// add the filestyle again
			new_form.find(':file').filestyle({buttonBefore: true});
			this.$form.html(new_form.children());
		}
	};

	$.fn.uploadprogress = function(options, value){
		return this.each(function(){
			var _options = $.extend({}, $.fn.uploadprogress.defaults, options);
			var file_progress = new Uploadprogress(this, _options);
			file_progress.constructor();
		});
	};

	$.fn.uploadprogress.defaults = {
		//redirect_url: ...
		//template: template
	};


})(window.jQuery);

// Select all images in Portfolio Admin
function checkImagesSelect(selector) {
	checkboxes = document.querySelectorAll(`${selector} input[type=checkbox]`);
	for (var i = 0, n = checkboxes.length; i < n; i++) {
		checkboxes[i].checked = !checkboxes[i].checked;
	}
}

document.addEventListener("DOMContentLoaded", function() {

	var template = '<div class="modal fade" id="file-progress-modal">\
		<div class="modal-dialog"><div class="modal-content">\
			<div class="modal-header">\
				<h4 class="modal-title">Загрузка...</h4>\
				<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\
			</div>\
			<div class="modal-body">\
				<div class="modal-message"></div>\
				<div class="progress" style="height:2em;">\
					<div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">\
					0%\
					</div>\
				</div>\
			</div>\
			<div class="modal-footer">\
				<button type="button" class="btn btn-default" data-dismiss="modal">Отмена</button>\
			</div>\
		</div></div>\
	</div>';

	const portfolioForm = document.querySelector('#portfolio_form');
	portfolioForm.insertAdjacentHTML("afterend",template);

	$(portfolioForm).uploadprogress({redirect_url: portfolioForm.action, template: $("#file-progress-modal") });


});
