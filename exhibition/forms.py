from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Exhibitions, Winners, Nominations, Portfolio, Image
from django.contrib.auth.models import User
from django.forms.widgets import ClearableFileInput
from uuslug import uuslug
#from django.contrib.admin.widgets import FilteredSelectMultiple
#from django_summernote.widgets import SummernoteInplaceWidget

class PersonUserForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = User
		fields = '__all__'

	error_messages = {
	'duplicate_username': ("My message for unique")
	}

	def clean_username(self):
		username = self.cleaned_data["username"]
		print('Username: %s' % username)
		if self.instance.username == username:
			return username
			try:
				User._default_manager.get(username=username)
			except User.DoesNotExist:
				return username
			raise forms.ValidationError(
					self.error_messages['duplicate_username'],
					code='duplicate_username',
				)

class CustomClearableFileInput(ClearableFileInput):
	template_name = 'admin/exhibition/widgets/file_input.html'


class ExhibitionsForm(forms.ModelForm):
	files = forms.FileField(label='Фото', widget=forms.ClearableFileInput(attrs={'multiple': True}),required=False)

	class Meta:
		model = Exhibitions
		fields = '__all__'
		#exclude = ('slug',)
		#template_name = 'django/forms/widgets/checkbox_select.html'

		widgets = {
			"exhibitors" : forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
			"partners" : forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
			"jury" : forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
			"nominations" : forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
		}


class ImagesUploadForm(forms.ModelForm):
	files = forms.FileField(label='Фото', widget=forms.ClearableFileInput(attrs={'multiple': True}),required=False)

	class Meta:
		model = Portfolio
		fields = '__all__'
		exclude = ('project_id',)

		widgets = {
			#"nominations" : FilteredSelectMultiple('Номинация', attrs={'class': 'form-check-input'}, is_stacked=False),
		}

	def __init__(self, *args, **kwargs):
		self.css_class = "form-control"
		self.user = kwargs.pop('user',None)
		# if user.is_staff:
		# 	self.fields['owner'].widget = forms.TextInput()

		super().__init__(*args, **kwargs)



class FeedbackForm(forms.Form):
	name = forms.CharField(label='Имя', required=True, widget=forms.TextInput(attrs={'placeholder': 'Имя'}))
	from_email = forms.EmailField(label='E-mail', required=False, widget=forms.TextInput(attrs={'placeholder': 'E-mail'}))
	message = forms.CharField(label='Сообщение', required=True, widget=forms.Textarea(attrs={'placeholder': 'Сообщение'}))
