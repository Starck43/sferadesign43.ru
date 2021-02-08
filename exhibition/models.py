import re
from os import path
from django.conf import settings
from django.core.validators import RegexValidator
#from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse # Used to generate URLs by reversing the URL patterns
from django.db import models
from django.contrib.auth.models import User, UserManager
from django.contrib.auth import get_user_model

from django.db.models import F
from django.db.models.functions import Coalesce

from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

from crm import models
from .logic import ImageResize, UploadFilename, GalleryUploadTo, MediaFileStorage

from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
#from django.core.files.base import ContentFile
from sorl.thumbnail import get_thumbnail, delete
from uuslug import uuslug #, slugify
from smart_selects.db_fields import ChainedForeignKey, ChainedManyToManyField, GroupedForeignKey


logo_folder = 'logos/'
banner_folder = 'banners/'


def get_image_html(obj):
	#if path.isfile(os.path.join(settings.MEDIA_ROOT,obj.name)):
	if obj and path.isfile(path.join(settings.MEDIA_ROOT,obj.name)):
		size = '%sx%s' % (settings.ADMIN_THUMBNAIL_SIZE[0], settings.ADMIN_THUMBNAIL_SIZE[1])
		thumb = get_thumbnail(obj.name, size, crop='center', quality=75)
		return format_html('<img src="{0}" width="50"/>', thumb.url)
	else:
		return format_html('<img src="/media/no-image.png" width="50"/>')


"""Abstract model for Exhibitors, Jury, Partners"""
class Person(models.Model):
	logo = models.ImageField('Логотип', upload_to=logo_folder, storage=MediaFileStorage(), null=True, blank=True)
	#avatar = models.ImageField('Аватар', upload_to=avatar_folder, storage=MediaFileStorage(), null=True, blank=True)
	name = models.CharField('Имя контакта', max_length=100)
	slug = models.SlugField('Ярлык', max_length=100, unique=True)
	description = RichTextUploadingField('Информация о контакте', blank=True)
	sort = models.IntegerField('Индекс сортировки', null=True, blank=True)

	class Meta:
		ordering = ['name'] # '-' for DESC ordering
		abstract = True    # The table will not be created

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.name.lower(), instance=self)
		#print('uuslug: '+self.slug)
		super().save(*args, **kwargs)

	def logo_thumb(self):
		return get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'

	def __iter__(self):
		for field in self._meta.fields:
			name = field.name
			label = field.verbose_name
			value = field.value_to_string(self)
			link = None
			if value and type(field.default) is str :
				value = value.rsplit('/', 1)[-1]
				link = field.default+value

			if field.name in ['description','vk','fb','instagram']:
				label = ''

			if field.name == 'site' and value:
				value = re.sub(r'^https?:\/\/|\/$', '', value, flags=re.MULTILINE)
				link = 'http://'+value

			if (name == 'address' or name == 'site' or link) and value :
				yield (name, label, value, link)


"""Abstract model for Exhibitors and Partners"""
class Profile(models.Model):
	phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Введите номер в формате: '+999999999'")
	address = models.CharField('Адрес', max_length=100, blank=True)
	phone = models.CharField('Контактный телефон', validators=[phone_regex], max_length=17, blank=True,default="tel:")
	email = models.EmailField('E-mail', max_length=75, blank=True, default="mailto:")
	site = models.URLField('Сайт', max_length=75, blank=True)
	vk = models.CharField('Вконтакте', max_length=75, blank=True, default="https://vk.com/")
	fb = models.CharField('Facebook', max_length=75, blank=True, default="https://facebook.com/")
	instagram = models.CharField('Instagram', max_length=75, blank=True, default="https://instagram.com/")

	class Meta:
		abstract = True    # The table will not be created



class Exhibitors(Person, Profile):
	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'Пользователь')
	objects = UserManager()

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Участник выставки'
		verbose_name_plural = 'Участники выставки'
		ordering = ['user__last_name']
		#unique_together = ('name',)
		db_table = 'exhibitors'
		unique_together = ['user',]

	def clean_username(self, username):
		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			return username
		return None

	def save(self, *args, **kwargs):
		#user = get_user_model()
		if not self.user and self.email:
			username = self.clean_username(self.email.rpartition('@')[0])
			if username:
				user = User.objects.create_user(username=username, email=self.email, password='1111')
				user.save()
				self.user = user

		super().save(*args, **kwargs)

	def get_absolute_url(self):
		return reverse('exhibitor-detail-url', kwargs={'slug': self.slug })



class Organizer(Person, Profile):
	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'Пользователь')
	objects = UserManager()

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Организатор'
		verbose_name_plural = 'Организаторы'
		db_table = 'organizers'


class Jury(Person):
	excerpt = models.CharField('Краткое описание', max_length=255, null=True, blank=True)

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Жюри'
		verbose_name_plural = 'Жюри'
		ordering = ['sort','name']
		db_table = 'jury'
	# def __init__(self,id,name,slug,description,logo,sort,excerpt):
	# 	super().__init__(self)
	# 	self.excerpt = excerpt
	# 	self.description = description
	# 	print(self)
		# self.fields.keyOrder = [
		# 'excerpt',
		# 'description',
		# ]

	def get_absolute_url(self):
		return reverse('jury-detail-url', kwargs={'slug': self.slug })


class Partners(Person, Profile):

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Партнер выставки'
		verbose_name_plural = 'Партнеры выставки'
		db_table = 'partners'

	def get_absolute_url(self):
		return reverse('partner-detail-url', kwargs={'slug': self.slug })



''' Таблица Категорий '''
class Categories(models.Model):
	logo = models.ImageField('Логотип', upload_to=logo_folder, storage=MediaFileStorage(), null=True, blank=True)
	title = models.CharField('Категория', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	description = models.TextField('Описание категории', blank=True)
	sort = models.IntegerField('Индекс сортировки', null=True, blank=True)

	# Metadata
	class Meta:
		ordering = ['sort', 'title'] # '-' for DESC ordering
		verbose_name = 'Категория'
		verbose_name_plural = 'Категории'
		db_table = 'categories'

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.title.lower(), instance=self)
		super().save(*args, **kwargs)

	def __str__(self):
		if self.title:
			return self.title
		else:
			return '<без категории>'

	def logo_thumb(self):
		return get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'

	def get_absolute_url(self):
		return reverse('nomination-detail-url', kwargs={'slug': self.slug })


''' Таблица Номинаций '''
class Nominations(models.Model):
	category = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, blank=True, verbose_name = 'Категория')
	title = models.CharField('Номинация', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	description = RichTextUploadingField('Описание номинации', blank=True)
	sort = models.IntegerField('Индекс сортировки', null=True, blank=True)

	# Metadata
	class Meta:
		ordering = ['sort', 'title'] # '-' for DESC ordering
		verbose_name = 'Номинация'
		verbose_name_plural = 'Номинации'
		db_table = 'nominations'

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.title.lower(), instance=self)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		if self.category:
			return reverse('nomination-detail-url', kwargs={'slug': self.category.slug })
		else:
			return reverse('nomination-detail-url', kwargs={'slug': None })



''' Таблица Выставки '''
class Exhibitions(models.Model):
	title = models.CharField('Название выставки', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	banner = models.ImageField('Баннер', upload_to=banner_folder, null=True, blank=True)
	description = RichTextUploadingField('Описание выставки', blank=True)
	date_start = models.DateField('Начало выставки', unique=True)
	date_end = models.DateField('Окончание выставки', unique=True)
	location = models.CharField('Расположение выставки', max_length=200, blank=True)
	exhibitors = models.ManyToManyField(Exhibitors, related_name='exhibitors_for_exh', verbose_name = 'Участники', blank=True)
	partners = models.ManyToManyField(Partners, related_name='partners_for_exh', verbose_name = 'Партнеры', blank=True)
	jury = models.ManyToManyField(Jury, related_name='jury_for_exh', verbose_name = 'Жюри', blank=True)
	nominations = models.ManyToManyField(Nominations, related_name='nominations_for_exh', verbose_name = 'Номинации', blank=True)
	#events = models.ManyToManyField(Events, related_name='events_for_exh', verbose_name = 'Мероприятия')

	# Metadata
	class Meta:
		ordering = ['-date_start'] # '-' for DESC ordering
		verbose_name = 'Выставка'
		verbose_name_plural = 'Выставки'
		db_table = 'exhibitions'

	# удаление связанных фото с галереей
	def delete(self, *args, **kwargs):
		posts = self.gallery.all()
		for post in posts:
			post.delete()

		super().delete(*args, **kwargs)


	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.date_start.strftime('%Y'), instance=self)
		super().save(*args, **kwargs)

	def clean_slug(self):
		print(self.slug)


	def __str__(self):
		return self.title

	def exh_year(self):
		return self.date_start.strftime('%Y')
	exh_year.short_description = 'Выставка'

	def banner_thumb(self):
		return get_image_html(self.banner)

	banner_thumb.short_description = 'Логотип'

	def get_absolute_url(self):
		return reverse('exhibition-detail-url', kwargs={'exh_year': self.slug})



''' Таблица Мероприятий '''
class Events(models.Model):
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.SET_NULL, related_name='events', null=True, blank=True, verbose_name = 'Выставка')
	title = models.CharField('Название мероприятия', max_length=250)
	date_event = models.DateField('Дата мероприятия')
	time_start = models.TimeField('Начало мероприятия')
	time_end = models.TimeField('Окончание мероприятия')
	location = models.CharField('Зона проведения', max_length=75, blank=True)
	hoster = models.CharField('Участник мероприятия', max_length=75)
	lector = models.CharField('Ведущий мероприятия', max_length=75)
	description = RichTextUploadingField('Описание мероприятия', blank=True)

	# Metadata
	class Meta:
		ordering = ['date_event','time_start'] # '-' for DESC ordering
		verbose_name = 'Мероприятие'
		verbose_name_plural = 'Мероприятия'
		db_table = 'events'
		unique_together = ['exhibition', 'time_start', 'time_end']


	def __str__(self):
		return self.title

	def time_event(self):
		return ("%s - %s" % (self.time_start.strftime('%H:%M'), self.time_end.strftime('%H:%M')))
	time_event.short_description = 'Время мероприятия'

	def get_absolute_url(self):
		return reverse('event-detail-url', kwargs={'exh_year': self.exhibition.slug, 'pk': self.id})



"""Аттрибуты фильтра для портфолио"""
class PortfolioAttributes(models.Model):
	Groups=(
		('type','тип помещения'),
		('style','стиль помещения'),
	)

	group = models.CharField('Группа',choices=Groups, max_length=30)
	name = models.CharField("Название аттрибута", max_length=30)
	slug = models.SlugField('Ярлык', max_length=30, null=True, unique=True)

	class Meta:
		verbose_name = "Аттрибут фильтра"
		verbose_name_plural = "Аттрибуты фильтра"
		db_table = 'filter_attributes'
		ordering = ['group','name']

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.name, instance=self)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.get_group_display()} / {self.name}"



class Portfolio(models.Model):
	project_id = models.IntegerField(null=True)
	owner = models.ForeignKey(Exhibitors, on_delete=models.CASCADE, verbose_name = 'Участник')
	#exhibition = models.ForeignKey(Exhibitions, on_delete=models.SET_NULL, null=True, verbose_name = 'Выставка')
	exhibition = ChainedForeignKey(Exhibitions,
		chained_field="owner",
		chained_model_field="exhibitors",
		show_all=False,
		auto_choose=True,
		sort=True,
		on_delete=models.SET_NULL, null=True, verbose_name = 'Выставка')

	#nominations = models.ManyToManyField(Nominations, related_name='nominations_for_portfolio', blank=True, verbose_name = 'Номинации')
	nominations = ChainedManyToManyField(Nominations,
		chained_field="exhibition",
		chained_model_field="nominations_for_exh",
		#horizontal=True,
		auto_choose=True,
		related_name='nominations_for_portfolio', blank=True, verbose_name='Номинации')

	title = models.CharField('Название', max_length=200, blank=True)
	description = RichTextField('Описание портфолио', blank=True)
	attributes = models.ManyToManyField(PortfolioAttributes, related_name='attributes_for_portfolio', verbose_name = 'Аттрибуты фильтра', blank=True)

	# Metadata
	class Meta:
		ordering = ['-exhibition__date_start'] # '-' for DESC ordering
		verbose_name = 'Портфолио'
		verbose_name_plural = 'Портфолио работ'
		db_table = 'portfolio'
		unique_together = ['owner', 'project_id']

	# удаление связанных фото с портфолио
	def delete(self, *args, **kwargs):
		posts = self.images.all()
		for post in posts:
			post.delete()
		super().delete(*args, **kwargs)

	def save(self, images=None, *args, **kwargs):
		if not self.project_id:
			# найдем последнюю запись с наибольшим id
			post = Portfolio.objects.filter(owner=self.owner).only('project_id').order_by('project_id').last()
			index = 1
			if post and post.project_id:
				index += post.project_id

			self.project_id = index
		super().save(*args, **kwargs)

		# сохраним связанные с портфолио изображения
		for image in images:
			upload_filename = path.join('uploads/', self.owner.slug, self.exhibition.slug, self.slug, image.name)
			file_path = path.join(settings.MEDIA_ROOT,upload_filename)

			append_image = True
			instance = Image.objects.filter(portfolio=self, file=upload_filename).first()
			if instance:
				# Portfolio has this image yet
				if path.exists(file_path):
					append_image = False
					obj = ImageResize(instance.file)
			else:
				# New image in portfolio
				if path.exists(file_path):
					image = upload_filename

			if append_image:
				instance = Image(portfolio=self, file=image)
				instance.save()

	@property
	def slug(self):
		if self.project_id:
			return ('project-%s') % self.project_id
		else:
			return '<Без названия>'

	def root_comments(self):
		return self.comments_portfolio.filter(parent__isnull=True)

	def __str__(self):
		if self.title:
			return self.title
		else:
			return self.slug

	def get_absolute_url(self):
		return reverse('project-detail-url', kwargs={'owner': self.owner.slug, 'project_id': self.project_id })
		#return reverse('portfolio-detail-url', kwargs={'year': self.exhibition.date_start, 'owner': self.owner.slug, 'id': self.pk })



''' Таблица Победителей '''
class Winners(models.Model):

	exhibition = models.ForeignKey(Exhibitions, related_name='exhibition_for_winner', on_delete=models.CASCADE, null=True, verbose_name = 'Выставка')
	nomination = ChainedForeignKey(Nominations,
		chained_field="exhibition",
		chained_model_field="nominations_for_exh",
		show_all=False,
		auto_choose=True,
		sort=True,
		related_name='nomination_for_winner', on_delete=models.CASCADE, null=True, verbose_name = 'Номинация')
	exhibitor = ChainedForeignKey(Exhibitors,
		chained_field="exhibition",
		chained_model_field="exhibitors_for_exh",
		show_all=False,
		auto_choose=True,
		sort=True,
		related_name='exhibitor_for_winner', on_delete=models.CASCADE, null=True, verbose_name = 'Победитель')
	portfolio = ChainedForeignKey(Portfolio,
		chained_field="exhibitor",
		chained_model_field="owner",
		show_all=False,
		auto_choose=True,
		sort=True,
		related_name='portfolio_for_winner', on_delete=models.SET_NULL, null=True, verbose_name = 'Проект')

	# Metadata
	class Meta:
		ordering = ['-exhibition__date_start'] # '-' for DESC ordering
		verbose_name = 'Победитель'
		verbose_name_plural = 'Победители'
		db_table = 'winners'
		unique_together = ['exhibition', 'exhibitor', 'nomination']

	def __str__(self):
		return '%s - Номинация: "%s"' % (self.exhibitor.name, self.nomination.title)

	def exh_year(self):
		# return only Exhibition's year from date_start
		return self.exhibition.date_start.strftime('%Y')
	exh_year.short_description = 'Выставка'

	def name(self):
		return self.exhibitor.name
	name.short_description = 'Победитель'

	def get_absolute_url(self):
		return reverse('winner-project-detail-url', kwargs={'exh_year': self.exhibition.slug, 'slug': self.nomination.slug})



# Exhibition Photo Gallery
class Gallery(models.Model):
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.CASCADE, related_name='gallery', verbose_name = 'Выставка')
	title = models.CharField('Заголовок', max_length=100, null=True, blank=True)
	file = models.ImageField('Фото', upload_to=GalleryUploadTo, storage=MediaFileStorage())

	# Metadata
	class Meta:
		verbose_name = 'Фото с выставки'
		verbose_name_plural = 'Фото с выставки'
		db_table = 'gallery'

	def delete_storage_file(self):
		try:
			# is the object in the database yet?
			obj = Gallery.objects.get(id=self.id)
		except Gallery.DoesNotExist:
			if path.exists(self.file.path):
				delete(self.file)
			return

		if obj.file and self.file and obj.file != self.file:
			delete(obj.file)


	# Удаление файла на диске
	def delete(self, *args, **kwargs):
		delete(self.file)
		super().delete(*args, **kwargs)

	def save(self, *args, **kwargs):
		self.delete_storage_file()
		resized_image = ImageResize(self.file)
		if resized_image:
			self.file = resized_image
		super().save(*args, **kwargs)

	def __str__(self):
		if self.title:
			return self.title
		else:
			return '<Без имени>'


	def file_thumb(self):
		return get_image_html(self.file)

	file_thumb.short_description = 'Фото'


	def filename(self):
		return self.file.name.rsplit('/', 1)[-1]

	filename.short_description = 'Имя файла'



class Image(models.Model):
	portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, null=True, related_name='images', verbose_name = 'Портфолио')
	title = models.CharField('Заголовок', max_length=100, null=True, blank=True)
	description = models.CharField('Описание', max_length=250, blank=True)
	file = models.ImageField('Фото', upload_to=UploadFilename, storage=MediaFileStorage())
	sort = models.SmallIntegerField('Индекс сортировки', null=True, blank=True)

	# Metadata
	class Meta:
		verbose_name = 'Фото участника'
		verbose_name_plural = 'Фото участников'
		ordering = [Coalesce("sort", F('id') + 500)]
		db_table = 'images'


	def __str__(self):
		if self.title:
			return self.title
		else:
			return '<Без имени>'


	def delete_storage_file(self):
		try:
			# is the object in the database yet?
			obj = Image.objects.get(id=self.id)
		except Image.DoesNotExist:
			# if object is not in DB and it exists on disk then delete this file
			if path.exists(self.file.path):
				delete(self.file)
			return

		if obj.file and self.file and obj.file != self.file:
			delete(obj.file)


	# Удаление файла на диске, если файл прикреплен только к текущему портфолио
	def delete(self, *args, **kwargs):
		if Image.objects.filter(file=self.file.name).count() == 1:
			delete(self.file)
		super().delete(*args, **kwargs)

	def save(self, *args, **kwargs):
		self.delete_storage_file()
		# Resizing uploading image.
		# Alternative package - django-resized
		resized_image = ImageResize(self.file)
		if resized_image:
			self.file = resized_image
		super().save(*args, **kwargs)


	def file_thumb(self):
		return get_image_html(self.file)

	file_thumb.short_description = 'Фото'


	def filename(self):
		return self.file.name.rsplit('/', 1)[-1]

	filename.short_description = 'Имя файла'



class MetaSEO(models.Model):
	PAGES = (
		('index', 'Главная страница'),
		('contacts', 'Обратная связь'),
		('exhibitors-list', 'Список участников'),
		('exhibitor-detail', 'Профиль участника'),
		('jury-list', 'Список жюри'),
		('jury-detail', 'Профиль жюри'),
		('partners-list', 'Список партнеров'),
		('partner-detail', 'Профиль партнера'),
		('nominations-list', 'Разделы номинаций'),
		('nomination-detail', 'Список проектов'),
		('exhibitions-list', 'Список выставок'),
		('exhibition-detail', 'Выставка'),
		('events-list', 'Мероприятия выставки'),
		('winners-list', 'Список победителей'),
		('winner-project-detail', 'Проект победителя'),
		('project-detail', 'Проект участника'),
	)

	page = models.CharField('Страница', choices=PAGES, unique=True, max_length=30, help_text='Выберите страницу для SEO данных')
	description = models.CharField('Мета описание', max_length=100, help_text='Описание в поисковой выдаче. Рекомендуется 70-80 символов')
	keywords = models.CharField('Поисковые фразы', max_length=255, blank=True, help_text='Поисковые фразы. Указывать через запятую')

	# Metadata
	class Meta:
		verbose_name = 'SEO описание'
		verbose_name_plural = 'SEO описания'
		db_table = 'meta'

	def __str__(self):
		return self.page
