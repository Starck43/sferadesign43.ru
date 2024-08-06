from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, Row, HTML  # , Submit, Button
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
# from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import OuterRef, Subquery
from django.db.models.expressions import F
from django.forms.models import ModelMultipleChoiceField
from django.utils.html import format_html

from .logic import SetUserGroup
from .models import Exhibitors, Exhibitions, Portfolio, Image, MetaSEO

""" Форма регистрации """


class AccountSignupForm(SignupForm):
	username = forms.CharField(label='Имя пользователя',
	                           widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя (латиницей)'}))
	email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email адрес'}))
	first_name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'placeholder': 'Ваше имя'}))
	last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={'placeholder': 'Фамилия'}))
	exhibitor = forms.BooleanField(label="Участник выставки?", required=False)

	def __init__(self, *args, **kwargs):
		self.field_order = ['first_name', 'last_name', 'username', 'email', 'exhibitor', 'password1', 'password2', ]
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

	username = forms.CharField(label='Имя пользователя',
	                           widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя (уникальный ник)'}))
	email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email адрес'}))
	exhibitor = forms.BooleanField(label="Участник выставки?", required=False)

	def __init__(self, *args, **kwargs):
		self.field_order = ['first_name', 'last_name', 'username', 'email', 'exhibitor', ]
		super().__init__(*args, **kwargs)

	def save(self, request):
		# .save() returns a User object.
		user = super().save(request)
		user = SetUserGroup(request, user)

		return user


class DeactivateUserForm(forms.Form):
	deactivate = forms.BooleanField(label='Удалить?',
	                                help_text='Пожалуйста, поставьте галочку, если желаете удалить аккаунт',
	                                required=True)


class MetaSeoFieldsForm(forms.ModelForm):
	meta_title = forms.CharField(label='Мета заголовок',
	                             widget=forms.TextInput(attrs={'style': 'width:100%;box-sizing: border-box;'}),
	                             required=False)
	meta_description = forms.CharField(label='Мета описание',
	                                   widget=forms.TextInput(attrs={'style': 'width:100%;box-sizing: border-box;'}),
	                                   required=False)
	meta_keywords = forms.CharField(label='Ключевые фразы', widget=forms.TextInput(
		attrs={'style': 'width:100%;box-sizing: border-box;', 'placeholder': 'введите ключевые слова через запятую'}),
	                                required=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		model_name = self._meta.model.__name__.lower()
		self.meta_model = ContentType.objects.get(model=model_name)
		self.meta = None
		if self.instance.pk:
			try:
				self.meta = MetaSEO.objects.get(model=self.meta_model, post_id=self.instance.id)
				self.fields['meta_title'].initial = self.meta.title
				self.fields['meta_description'].initial = self.meta.description
				self.fields['meta_keywords'].initial = self.meta.keywords
			except MetaSEO.DoesNotExist:
				pass

	def save(self, *args, **kwargs):
		instance = super().save(*args, **kwargs)
		meta_changed = any(str in ['meta_title', 'meta_keywords', 'meta_description'] for str in self.changed_data)
		meta_title = self.cleaned_data['meta_title']
		meta_description = self.cleaned_data['meta_description']
		meta_keywords = self.cleaned_data['meta_keywords']
		if meta_changed:
			if self.meta:
				self.meta.title = meta_title
				self.meta.description = meta_description
				self.meta.keywords = meta_keywords
				self.meta.save()
			else:
				MetaSEO.objects.create(
					model=self.meta_model,
					post_id=instance.id,
					title=meta_title,
					description=meta_description,
					keywords=meta_keywords
				)

		return instance


class ExhibitionsForm(MetaSeoFieldsForm, forms.ModelForm):
	files = forms.ImageField(
		label='Фото',
		widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}),
		required=False
	)

	class Meta:
		model = Exhibitions
		fields = '__all__'
		# fields = ('meta_title','meta_description','meta_keywords')
		# exclude = ('slug',)
		# template_name = 'django/forms/widgets/checkbox_select.html'

		widgets = {
			"exhibitors": forms.CheckboxSelectMultiple(attrs={'class': ''}),
			"partners": forms.CheckboxSelectMultiple(attrs={'class': ''}),
			"jury": forms.CheckboxSelectMultiple(attrs={'class': ''}),
			"nominations": forms.CheckboxSelectMultiple(attrs={'class': ''}),
		}


class PortfolioForm(MetaSeoFieldsForm, forms.ModelForm):
	files = forms.FileField(
		label='Фото проекта',
		widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'allow_multiple_selected': True}),
		required=False,
		help_text='Общий размер загружаемых фото не должен превышать %s Мб' % round(
			settings.MAX_UPLOAD_FILES_SIZE / 1024 / 1024)
	)

	class Meta:
		model = Portfolio
		fields = (
			'owner', 'exhibition', 'categories', 'nominations', 'attributes', 'title', 'description', 'cover', 'files',
			'status',)

		STATUS_CHOICES = (
			(False, "Скрыт"),
			(True, "Доступен (по умолчанию)"),
		)

		widgets = {
			'cover': forms.ClearableFileInput(attrs={'class': 'form-control', 'multiple': False}),
			'categories': forms.CheckboxSelectMultiple(attrs={'class': 'form-group'}),
			'nominations': forms.CheckboxSelectMultiple(attrs={'class': 'form-group'}),
			'attributes': forms.CheckboxSelectMultiple(attrs={'class': 'form-group'}),
			'status': forms.Select(choices=STATUS_CHOICES),
		}

	def __init__(self, *args, **kwargs):
		self.exhibitor = kwargs.pop('owner', None)
		request = kwargs.pop('request', None)
		if request:
			self.request = request

		super().__init__(*args, **kwargs)
		self.css_class = 'form-control'

		if self.exhibitor != None:
			# self.fields['files'].initial = files
			if self.exhibitor == 'staff':
				self.fields['exhibition'].queryset = Exhibitions.objects.all()
			else:
				self.fields['categories'].widget.attrs.update({'class': 'hidden'})
				self.fields['owner'].initial = self.exhibitor
				self.fields['owner'].widget = forms.HiddenInput()
				self.fields['status'].widget = forms.HiddenInput()

				self.helper.layout[0].append(
					HTML('<div>Участиник выставки:<br><h2>' + self.exhibitor.name + '</h2></div>'))

				self.fields['exhibition'].queryset = Exhibitions.objects.prefetch_related('exhibitors').filter(
					exhibitors=self.exhibitor)

	@property
	def helper(self):
		helper = FormHelper()
		helper.form_tag = False
		helper.layout = Layout(
			FloatingField('owner'),
			FloatingField('exhibition'),
			Field('categories', wrapper_class='field-categories'),
			Field('nominations', wrapper_class='field-nominations'),
			Field('attributes', wrapper_class='field-attributes'),
			FloatingField('title'),
			'description',
			FloatingField('status'),
			'cover',
			'files',
			Div(
				HTML('<div class="card-header">СЕО описание для поисковых систем</div>'),
				Div(
					FloatingField('meta_title'),
					FloatingField('meta_description'),
					FloatingField('meta_keywords'),
					css_class='card-body'
				),
				css_class="card mt-3 mb-5",
			)
		)
		return helper

	def clean(self):
		cleaned_data = super().clean()

		if self.exhibitor != None:
			if self.cleaned_data['exhibition']:
				self.cleaned_data['categories'] = []
			else:
				self.cleaned_data['nominations'] = []
				self.cleaned_data['attributes'] = []

		return cleaned_data

	def clean_files(self):
		data = self.cleaned_data['files']
		content_length = int(self.request.META['CONTENT_LENGTH'])
		if content_length > settings.MAX_UPLOAD_FILES_SIZE:
			raise ValidationError(
				'[%s Мб] Превышен общий размер загружаемых файлов!' % int(content_length / 1024 / 1024))
		return data


# def save(self, *args, **kwargs):
# 	instance = super().save(*args, **kwargs)
# 	if self.exhibitor:
# 		instance.categories.set(None)

# 	return instance


class ImageForm(forms.ModelForm):
	class Meta:
		model = Image
		fields = '__all__'
		exclude = ('portfolio',)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['description'].widget = forms.Textarea()


class ImageFormHelper(FormHelper):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# self.form_method = 'post'
		self.form_tag = False
		self.include_media = False
		self.disable_csrf = True
		self.layout = Layout(
			Div(
				HTML('<div class="card-header">Фото {{forloop.counter}}</div>'),
				Row(
					Field(
						'file',
						template='crispy_forms/image.html'
					),
					Div(
						Field('file', wrapper_class='upload-link'),
						FloatingField('title'),
						FloatingField('description'),
						FloatingField('sort'),
						Field('DELETE', wrapper_class='form-check form-check-inline'),
						css_class="meta"
					),
					css_class="card-body flex-column flex-md-row",
				),
				css_class="portfolio-image card mb-5"
			)
		)


# self.render_required_fields = True


class FeedbackForm(forms.Form):
	name = forms.CharField(label='Имя', required=True, widget=forms.TextInput(attrs={'placeholder': 'Ваше имя'}))
	# from_phone = forms.EmailField(label='Телефон', required=False, widget=forms.TextInput(attrs={'placeholder': 'Ваш номер для связи'}))
	from_email = forms.EmailField(label='E-mail', required=True,
	                              widget=forms.TextInput(attrs={'placeholder': 'Ваш почтовый ящик'}))
	message = forms.CharField(label='Сообщение', required=True,
	                          widget=forms.Textarea(attrs={'placeholder': 'Сообщение'}))


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

		return format_html('<b>{0}</b> [{1}] </span><span>{2}</span><span>{3}</span>', obj.name, obj.user_email,
		                   obj.last_exh or '', format_html(email_status))


# return format_html('<b>{0}</b> [{1}] </span><span>{2}</span>', obj['name'], obj['user_email'], obj['last_exh'] or '')


""" Вывод списка пользователей в рассылке сброса паролей"""


class UsersListForm(forms.Form):
	subquery = Subquery(Exhibitions.objects.filter(exhibitors=OuterRef('pk')).values('slug')[:1])
	subquery2 = Subquery(EmailAddress.objects.filter(user_id=OuterRef('user_id')).values('verified')[:1])
	users = UserMultipleModelChoiceField(
		label=format_html('Имя [Email]<span>Последняя выставка</span><span>Верификация</span>'),
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
# self.fields['users'].widget.attrs = {'class': 'reset-psw-user-input'}

# User fields to output:
# date_joined, email, emailaddress, exhibitors, first_name, groups, id, is_active, is_staff, is_superuser, last_login, last_name, logentry, organizer, password, rating, reviews, user_permissions, username
