import re
from os import path, rename, rmdir, listdir
from django.conf import settings
from django.core.validators import RegexValidator
#from django.utils.text import slugify
from django.urls import reverse # Used to generate URLs by reversing the URL patterns
from django.db import models
from django.contrib.auth.models import User, UserManager
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from django.db.models import F
from django.db.models.functions import Coalesce

from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

from crm import models
from .logic import get_image_html, ImageResize, PortfolioUploadTo, CoverUploadTo, GalleryUploadTo, MediaFileStorage, limit_file_size, update_google_sitemap

from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
#from django.core.files.base import ContentFile
from sorl.thumbnail import delete
from uuslug import uuslug
from smart_selects.db_fields import ChainedForeignKey, ChainedManyToManyField, GroupedForeignKey


LOGO_FOLDER = 'logos/'
BANNER_FOLDER = 'banners/'


"""Abstract model for Exhibitors, Organizer, Jury, Partners"""
class Person(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'Пользователь')
	logo = models.ImageField('Логотип', upload_to=LOGO_FOLDER, storage=MediaFileStorage(), null=True, blank=True)
	#avatar = models.ImageField('Аватар', upload_to=avatar_folder, storage=MediaFileStorage(), null=True, blank=True)
	name = models.CharField('Имя контакта', max_length=100)
	slug = models.SlugField('Ярлык', max_length=100, unique=True)
	description = RichTextUploadingField('Информация о контакте', blank=True)
	sort = models.IntegerField('Индекс сортировки', null=True, blank=True)

	class Meta:
		abstract = True # Table will not be created

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.name.lower(), instance=self)
		super().save(*args, **kwargs)

	def logo_thumb(self):
		return get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'


"""Abstract model for Exhibitors and Partners"""
class Profile(models.Model):
	phone_regex = RegexValidator(regex=r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$', message="Допустимы цифры, знак плюс, символы пробела и круглые скобки")
	address = models.CharField('Адрес', max_length=100, blank=True)
	phone = models.CharField('Контактный телефон', validators=[phone_regex], max_length=18, blank=True)
	email = models.EmailField('E-mail', max_length=75, blank=True)
	site = models.URLField('Сайт', max_length=75, blank=True)
	instagram = models.CharField('Instagram', max_length=75, blank=True, default="https://instagram.com")
	fb = models.CharField('Facebook', max_length=75, blank=True, default="https://facebook.com")
	vk = models.CharField('Вконтакте', max_length=75, blank=True, default="https://vk.com")

	class Meta:
		abstract = True    # The table will not be created


	def __iter__(self):
		for field in self._meta.fields:
			name = field.name
			label = field.verbose_name
			value = field.value_to_string(self)
			link = None
			if value and type(field.default) is str :
				value = value.rsplit('/', 1)[-1]
				link = field.default+'/'+value.lower()

			if value and name in ['phone','email'] :
				prefix = 'tel' if name == 'phone' else 'mailto'
				link = prefix+':'+value.lower()

			if name in ['description','vk','fb','instagram']:
				label = ''

			if name == 'site' and value:
				value = re.sub(r'^https?:\/\/|\/$', '', value, flags=re.MULTILINE)
				link = 'https://'+value

			if (name == 'address' or name == 'site' or link) and value :
				yield (name, label, value, link)



class Exhibitors(Person, Profile):
	objects = UserManager()

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Участник выставки'
		verbose_name_plural = 'Участники выставки'
		ordering = ['user__last_name']
		#unique_together = ('name',)
		db_table = 'exhibitors'
		unique_together = ['user',]

	original_slug = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.original_slug = self.slug

	def save(self, *args, **kwargs):
		#user = get_user_model()
		if not self.user and self.email:
			username = self.clean_username(self.email.rpartition('@')[0])
			if not username:
				username = self.slug
			if username:
				user = User.objects.create_user(username=username, email=self.email, password='1111')
				user.save()
				self.user = user

		if self.original_slug and self.slug != self.original_slug:
			portfolio_folder = path.join(settings.MEDIA_ROOT, settings.FILES_UPLOAD_FOLDER, self.original_slug)
			if path.exists(portfolio_folder):
				new_portfolio_folder = path.join(settings.MEDIA_ROOT, settings.FILES_UPLOAD_FOLDER, self.slug)
				# переименуем имя папки с проектами текущего участника
				rename(portfolio_folder, new_portfolio_folder)
				# почистим кэшированные файлы и изменим путь к файлам в таблице Image для всех портфолио принадлежащих текущему участнику
				owner_images = Image.objects.filter(portfolio__owner__slug=self.original_slug)
				for image in owner_images:
					# Only clears key-value store data in thumbnail-kvstore, but does not delete image file
					delete(image.file, delete_file=False)
					renamed_file = str(image.file).replace(self.original_slug, self.slug)
					image.file = renamed_file
					image.save()

			self.original_slug = self.slug

		super().save(*args, **kwargs)
		update_google_sitemap() # обновим карту сайта Google


	def clean_username(self, username):
		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			return username
		return None

	def get_absolute_url(self):
		return reverse('exhibition:exhibitor-detail-url', kwargs={'slug': self.slug })



class Organizer(Person, Profile):
	objects = UserManager()

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Организатор'
		verbose_name_plural = 'Организаторы'
		db_table = 'organizers'
		ordering = ['sort','name']



class Jury(Person):
	excerpt = models.CharField('Краткое описание', max_length=255, null=True, blank=True)
	objects = UserManager()

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Жюри'
		verbose_name_plural = 'Жюри'
		ordering = ['sort','name']
		db_table = 'jury'


	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		update_google_sitemap() # обновим карту сайта Google


	def get_absolute_url(self):
		return reverse('exhibition:jury-detail-url', kwargs={'slug': self.slug })



class Partners(Person, Profile):
	objects = UserManager()

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Партнер выставки'
		verbose_name_plural = 'Партнеры выставки'
		db_table = 'partners'
		ordering = [Coalesce("sort", F('id') + 500)] #сортировка в приоритете по полю sort, а потом уже по-умолчанию


	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		update_google_sitemap() # обновим карту сайта Google

	def get_absolute_url(self):
		return reverse('exhibition:partner-detail-url', kwargs={'slug': self.slug })



''' Таблица Категорий '''
class Categories(models.Model):
	title = models.CharField('Категория', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	description = models.TextField('Описание категории', blank=True)
	logo = models.ImageField('Логотип', upload_to=LOGO_FOLDER, storage=MediaFileStorage(), null=True, blank=True)
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
		update_google_sitemap() # обновим карту сайта Google


	def __str__(self):
		if self.title:
			return self.title
		else:
			return '<без категории>'

	def logo_thumb(self):
		return get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'

	def get_absolute_url(self):
		return reverse('exhibition:projects-list-url', kwargs={'slug': self.slug })


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
		update_google_sitemap() # обновим карту сайта Google


	def __str__(self):
		return self.title

	def get_absolute_url(self):
		if self.category:
			return reverse('exhibition:projects-list-url', kwargs={'slug': self.category.slug })
		else:
			return reverse('exhibition:category-list-url', kwargs={'slug': None })



''' Таблица Выставки '''
class Exhibitions(models.Model):
	title = models.CharField('Название выставки', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	banner = models.ImageField('Баннер', upload_to=BANNER_FOLDER, null=True, blank=True)
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
		update_google_sitemap() # обновим карту сайта Google

	# def clean_slug(self):
	# 	print(self.slug)


	def __str__(self):
		return self.title

	def exh_year(self):
		return self.date_start.strftime('%Y')
	exh_year.short_description = 'Выставка'

	def banner_thumb(self):
		return get_image_html(self.banner)
	banner_thumb.short_description = 'Логотип'

	def get_absolute_url(self):
		return reverse('exhibition:exhibition-detail-url', kwargs={'exh_year': self.slug})



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
		#unique_together = ['date_event', 'time_start', 'time_end']

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		update_google_sitemap() # обновим карту сайта Google

	def __str__(self):
		return self.title

	def time_event(self):
		return ("%s - %s" % (self.time_start.strftime('%H:%M'), self.time_end.strftime('%H:%M')))
	time_event.short_description = 'Время мероприятия'

	def get_absolute_url(self):
		return reverse('exhibition:event-detail-url', kwargs={'exh_year': self.exhibition.slug, 'pk': self.id})



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
		#show_all=True,
		auto_choose=False,
		sort=True,
		on_delete=models.SET_NULL, null=True, blank=True, verbose_name = 'Выставка', help_text='Выберите год, если проект будет участвовать в конкурсе')

	categories = models.ManyToManyField(Categories, related_name='categories_for_portfolio', blank=True, verbose_name = 'Категории', help_text='Отметьте нужные категории соответствующие вашему проекту')
	nominations = ChainedManyToManyField(Nominations,
		chained_field="exhibition",
		chained_model_field="nominations_for_exh",
		#horizontal=True,
		auto_choose=True,
		related_name='nominations_for_portfolio', blank=True, verbose_name='Номинации', help_text='Отметьте номинации, в которых заявляетесь с Вашим проектом')

	title = models.CharField('Название', max_length=200, blank=True)
	description = RichTextField('Описание портфолио', blank=True)
	cover = models.ImageField('Обложка', upload_to=CoverUploadTo, storage=MediaFileStorage(), null=True, blank=True, validators=[limit_file_size], help_text='Размер файла не более %s Мб' % round(settings.FILE_UPLOAD_MAX_MEMORY_SIZE/1024/1024))
	attributes = models.ManyToManyField(PortfolioAttributes, related_name='attributes_for_portfolio', verbose_name = 'Аттрибуты фильтра', blank=True)
	status = models.BooleanField('Статус', null=True, blank=True, default=True, help_text='Видимость на сайте')

	# Metadata
	class Meta:
		ordering = ['-exhibition__slug','title'] # '-' for DESC ordering
		verbose_name = 'Портфолио'
		verbose_name_plural = 'Портфолио работ'
		db_table = 'portfolio'
		unique_together = ['owner', 'project_id']

	def delete(self, *args, **kwargs):
		# удаление связанных фото с портфолио
		for post in self.images.all():
			post.delete()

		super().delete(*args, **kwargs)
		update_google_sitemap()

	def save(self, *args, **kwargs):
		images = kwargs.pop('images',None)

		if not self.project_id:
			# найдем последнюю запись с наибольшим id
			post = Portfolio.objects.filter(owner=self.owner).only('project_id').order_by('project_id').last()
			if post:
				self.project_id = post.project_id + 1
			else:
				self.project_id = 1

		super().save(*args, **kwargs)


		# сохраним связанные с портфолио изображения
		if self.pk and images:
			for image in images:
				exhibition_slug = self.exhibition.slug if self.exhibition else 'non-exhibition'
				upload_filename = path.join(settings.FILES_UPLOAD_FOLDER, self.owner.slug, exhibition_slug, self.slug, image.name)
				file_path = path.join(settings.MEDIA_ROOT,upload_filename)
				append_image = True

				if path.exists(file_path):
					try:
						# Portfolio has an image yet
						exist_image = Image.objects.get(portfolio=self, file=upload_filename)
						# Проверим размер загруженного повторно файла и изменим оригинал, если он превысит лимит указанный в settings
						ImageResize(exist_image.file)
						append_image = False
					except Image.DoesNotExist:
						# New image in portfolio
						image = upload_filename

				if append_image:
					instance = Image(portfolio=self, file=image)
					instance.save()

		update_google_sitemap() # обновим карту сайта Google


	@property
	def slug(self):
		return ('project-%s') % self.project_id

	def root_comments(self):
		return self.comments_portfolio.filter(parent__isnull=True)

	def __str__(self):
		if self.title:
			return self.title
		else:
			return ('Проект %s') % self.project_id

	def get_absolute_url(self):
		return reverse('exhibition:project-detail-url', kwargs={'owner': self.owner.slug, 'project_id': self.project_id })
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
		ordering = ['-exhibition__slug']
		verbose_name = 'Победитель выставки'
		verbose_name_plural = 'Победители'
		db_table = 'winners'
		unique_together = ['exhibition', 'exhibitor', 'nomination']

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		update_google_sitemap() # обновим карту сайта Google


	def __str__(self):
		return '%s | %s, %s' % (self.exhibitor.name, self.nomination.title, self.exhibition.slug)

	def exh_year(self):
		# return only Exhibition's year from date_start
		return self.exhibition.date_start.strftime('%Y')
	exh_year.short_description = 'Выставка'

	def name(self):
		return self.exhibitor.name
	name.short_description = 'Победитель'

	def get_absolute_url(self):
		return reverse('exhibition:winner-detail-url', kwargs={'exh_year': self.exhibition.slug, 'slug': self.nomination.slug})



# Exhibition Photo Gallery
class Gallery(models.Model):
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.CASCADE, related_name='gallery', verbose_name = 'Выставка')
	title = models.CharField('Заголовок', max_length=100, null=True, blank=True)
	file = models.ImageField('Фото', upload_to=GalleryUploadTo)

	# Metadata
	class Meta:
		verbose_name = 'Фото с выставки'
		verbose_name_plural = 'Фото с выставки'
		db_table = 'gallery'

	def delete_storage_file(self):
		try:
			# is the object in the database yet?
			obj = Gallery.objects.get(id=self.id)
			if obj.file and self.file and obj.file != self.file:
				delete(obj.file)
		except Gallery.DoesNotExist:
			if path.exists(self.file.path):
				delete(self.file)


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
	file = models.ImageField('Файл', upload_to=PortfolioUploadTo, storage=MediaFileStorage(), validators=[limit_file_size], help_text='Размер файла не более %s Мб' % round(settings.FILE_UPLOAD_MAX_MEMORY_SIZE/1024/1024))
	sort = models.SmallIntegerField('Индекс сортировки', null=True, blank=True)

	# Metadata
	class Meta:
		verbose_name = 'Фото проекта'
		verbose_name_plural = 'Фото портфолио'
		ordering = [Coalesce("sort", F('id') + 500)] #сортировка в приоритете по полю sort, а потом уже по-умолчанию
		db_table = 'images'


	def __str__(self):
		if self.title:
			return self.title
		else:
			return '<Без имени>'


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.original_file = self.file


	def delete(self, *args, **kwargs):
		# Удаление файла на диске, если файл прикреплен только к текущему портфолио
		if len(Image.objects.filter(file=self.file.name)) == 1:
			# физически удалим файл с диска, если он единственный
			delete(self.file)
			folder = path.join(settings.MEDIA_ROOT, path.dirname(self.file.name))
			if not listdir(folder):
				rmdir(folder)

		super().delete(*args, **kwargs)


	def save(self, *args, **kwargs):
		# если файл заменен, то требуется удалить все миниатюры в кэше у sorl-thumbnails
		if self.original_file and self.original_file != self.file:
			delete(self.original_file)

		# Resizing uploading image
		# Alternative package - django-resized
		resized_image = ImageResize(self.file)
		if resized_image and resized_image != 'error':
			self.file = resized_image

		if resized_image != 'error':
			super().save(*args, **kwargs)
			self.original_file = self.file


	def file_thumb(self):
		return get_image_html(self.file)
	file_thumb.short_description = 'Фото'


	def filename(self):
		return self.file.name.rsplit('/', 1)[-1]
	filename.short_description = 'Имя файла'



class MetaSEO(models.Model):
	model = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='Раздел')
	post_id = models.PositiveIntegerField('Запись в разделе', null=True, blank=True)
	title = models.CharField('Заголовок страницы', max_length=100, blank=True, null=True)
	description = models.CharField('Мета описание', max_length=100, blank=True, null=True, help_text='Описание в поисковой выдаче. Рекомендуется 70-80 символов')
	keywords = models.CharField('Ключевые слова', max_length=255, blank=True, null=True, help_text='Поисковые словосочетания указывать через запятую. Рекомендуется до 20 слов и не более 3-х повторов')

	# Metadata
	class Meta:
		verbose_name = 'SEO описание'
		verbose_name_plural = 'SEO описания'
		db_table = 'metaseo'
		unique_together = ['model', 'post_id']


	def get_model(model):
		return ContentType.objects.get(model=model).model_class()

	def __str__(self):
		return self.title

