from django import forms
from .models import Exhibitions, Winners, Nominations, Portfolio, Image
from django.contrib.auth.models import User
from django.forms.models import ModelMultipleChoiceField
from django.forms.widgets import ClearableFileInput
from uuslug import uuslug

from .logic import SetUserGroup

from django.contrib.auth.forms import UserCreationForm
from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm

""" Форма регистрации """
class AccountSignupForm(SignupForm):
	username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя (латиницей)'}))
	email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email адрес'}))
	first_name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'placeholder': 'Ваше имя'}))
	last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={'placeholder': 'Фамилия'}))
	exhibitor = forms.BooleanField(label="Участник выставки?",required=False)

	def __init__(self, *args, **kwargs):
		self.field_order = ['first_name', 'last_name', 'username', 'email', 'exhibitor', 'password1', 'password2',]
		super().__init__(*args, **kwargs)
		self.fields["password2"].widget.attrs['placeholder'] = 'Пароль повторно'

	# class Meta:
	# 	model = User
	# 	fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'exhibitor',]

	# 	widgets = {
	# 		'first_name' : forms.TextInput(attrs={'placeholder': 'Имя'}),
	# 		'last_name' : forms.TextInput(attrs={'placeholder': 'Фамилия'}),
	# 	}

	# error_messages = {
	# 'duplicate_username': ("Имя пользователя уже существует")
	# }

	# def clean_username(self):
	# 	username = self.cleaned_data["username"]
	# 	if self.instance.username == username:
	# 		return username

	# 	try:
	# 		User._default_manager.get(username=username)
	# 	except User.DoesNotExist:
	# 		return username
	# 	raise forms.ValidationError(
	# 			self.error_messages['duplicate_username'],
	# 			code='duplicate_username',
	# 		)
	def save(self, request):
		# .save() returns a User object.
		user = super().save(request)
		user = SetUserGroup(request, user)

		return user


""" Форма регистрации """
class CustomSocialSignupForm(SocialSignupForm):
	first_name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'placeholder': 'Ваше имя'}))
	last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={'placeholder': 'Фамилия'}))

	username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя (уникальный ник)'}))
	email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email адрес'}))
	exhibitor = forms.BooleanField(label="Участник выставки?",required=False)

	def __init__(self, *args, **kwargs):
		self.field_order = ['first_name', 'last_name', 'username', 'email', 'exhibitor',]
		super().__init__(*args, **kwargs)

	def save(self, request):
		# .save() returns a User object.
		user = super().save(request)
		user = SetUserGroup(request, user)

		return user


class DeactivateUserForm(forms.Form):
	deactivate = forms.BooleanField(label='Удалить?', help_text='Пожалуйста, поставьте галочку, если желаете удалить аккаунт', required=True)


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


""" Переопределение отображения списка пользователей """
class UserMultipleModelChoiceField(ModelMultipleChoiceField):
	def label_from_instance(self, obj):
		return "%s %s [%s]" % (obj.first_name, obj.last_name, obj.email)


""" Вывод списка пользователей в рассылке сброса паролей"""
class UsersListForm(forms.Form):
	users = UserMultipleModelChoiceField(label='Имя пользователя / Email',
		widget=forms.CheckboxSelectMultiple(attrs={}),
		queryset=User.objects.filter(groups__name='Exhibitors').order_by('first_name'),
		to_field_name="email"
	)

# User fields to output:
# date_joined, email, emailaddress, exhibitors, first_name, groups, id, is_active, is_staff, is_superuser, last_login, last_name, logentry, organizer, password, rating, reviews, user_permissions, username


