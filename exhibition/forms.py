from django import forms
from django.forms.models import ModelMultipleChoiceField
from django.forms.widgets import ClearableFileInput
from django.utils.html import format_html, escape
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from uuslug import uuslug

from django.db.models import OuterRef, Subquery
from django.db.models.expressions import F, Value

from .models import Exhibitors, Exhibitions, Winners, Nominations, Portfolio, Image
from .logic import SetUserGroup

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from allauth.account.models import EmailAddress


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


""" Mixin: Переопределение отображения списка пользователей в UsersListForm """
class UserMultipleModelChoiceField(ModelMultipleChoiceField):
	def label_from_instance(self, obj):
		if not obj.verified == None:
			if obj.verified:
				email_status = '<img src="/static/admin/img/icon-yes.svg">'
			else:
				email_status = '<img src="/static/admin/img/icon-no.svg">'
		else:
			email_status = ''

		return format_html('<b>{0}</b> [{1}] </span><span>{2}</span><span>{3}</span>', obj.name, obj.user_email, obj.last_exh or '', format_html(email_status))
		#return format_html('<b>{0}</b> [{1}] </span><span>{2}</span>', obj['name'], obj['user_email'], obj['last_exh'] or '')


""" Вывод списка пользователей в рассылке сброса паролей"""
class UsersListForm(forms.Form):

	subquery = Subquery(Exhibitions.objects.filter(exhibitors=OuterRef('pk')).values('slug')[:1])
	subquery2 = Subquery(EmailAddress.objects.filter(user_id=OuterRef('user_id')).values('verified')[:1])
	users = UserMultipleModelChoiceField(label=format_html('Имя [Email]<span>Последняя выставка</span><span>Верификация</span>'),
		widget=forms.CheckboxSelectMultiple(),
		queryset=Exhibitors.objects.distinct().filter(user__is_active=True).annotate(
			user_email=F('user__email'),
			last_exh=subquery,
			verified=subquery2,
		).order_by('-last_exh', 'user_email', 'name'),
		to_field_name="user_email"
	)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#self.fields['users'].widget.attrs = {'class': 'reset-psw-user-input'}


# User fields to output:
# date_joined, email, emailaddress, exhibitors, first_name, groups, id, is_active, is_staff, is_superuser, last_login, last_name, logentry, organizer, password, rating, reviews, user_permissions, username


