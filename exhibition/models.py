from django.db import models
from django.urls import reverse # Used to generate URLs by reversing the URL patterns
from django.utils.text import slugify
from django.utils.html import format_html
import os

from uuslug import uuslug
#from datetime import date
#from time import time
from crm import models
from .logic import MediaFileStorage

avatar_upload_folder = 'participants/avatars/'
logo_upload_folder = 'participants/logos/'

def UploadFilename(instance, filename):
	basename, ext = os.path.splitext(filename)
	return os.path.join('uploads/', basename + ext.lower())

class MediaFileStorage(FileSystemStorage):
	def save(self, name, content, max_length=None):
		# prevent saving file on disk
		return name

def get_image_html(obj)
	if obj:
		return format_html('<a href="{0}" target="_blank"><img src="{0}" width="50"/></a>', obj.url)
	else:
		return format_html('<img src="/media/no-image.png" width="50"/>')

"""Abstract model for Participant"""
class Participant(models.Model):
	name = models.CharField('ФИО', max_length=100)
	slug = models.SlugField('Ярлык', max_length=100, unique=True)
	description = models.TextField('Описание', db_index=True, blank=True)
	photo = models.ImageField('Аватар', upload_to=avatar_upload_folder, null=True, blank=True)

	class Meta:
		ordering = ['name'] # '-' for DESC ordering

	def __init__(self, arg):
		super(Contact, self).__init__()
		self.arg = arg

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.name, instance=self)
		super().save(*args, **kwargs)

	def photo_thumb(self):
			get_image_html(self.photo)

		photo_thumb.short_description = 'Портрет'


"""Abstract model for Contact"""
class Contact(models.Model):
	address = models.CharField('Адрес', max_length=100, blank=True)
	phone = models.PhoneNumberField('Контактный телефон')
	email = models.EmailField('E-mail', max_length=75)
	site = models.URLField('Сайт', max_length=75)
	vk = models.URLField('Вконтакте', max_length=75)
	fb = models.URLField('Facebook', max_length=75)
	instagram = models.URLField('Instagram', max_length=75)
	logo = models.ImageField('Логотип', upload_to=logo_upload_folder, null=True, blank=True)

	def logo_thumb(self):
		get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'


class Exhibitors(Participant, Contact):

	# Metadata
	class Meta(Participant.Meta):
		verbose_name = 'Участник выставки'
		verbose_name_plural = 'Участники выставки'

	def get_absolute_url(self):
		pass
		#return reverse('exhibitor-detail', kwargs={'slug': self.slug })


class Jury(Participant):

	# Metadata
	class Meta(Participant.Meta):
		verbose_name = 'Жюри'
		verbose_name_plural = 'Жюри'

	def get_absolute_url(self):
		pass
		#return reverse('Jury-detail', kwargs={'slug': self.slug })


class Partners(Participant, Contact):

	# Metadata
	class Meta(Participant.Meta):
		verbose_name = 'Партнер выставки'
		verbose_name_plural = 'Партнеры выставки'

	def get_absolute_url(self):
		pass
		#return reverse('exhibitor-detail', kwargs={'slug': self.slug })


''' Таблица Выставки '''
class Exhibitions(models.Model):
	title = models.CharField('Название выставки', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	description = models.TextField('Описание выставки', db_index=True, blank=True)
	date_start = DateField('Начало выставки', unique=True)
	date_end = DateField('Окончание выставки', unique=True)
	exhibitions = models.ManyToManyField(Exhibitions, db_table='nominations_relationships', on_delete=models.SET_NULL, related_name='exhibitions')

	# Metadata
	class Meta:
		ordering = ['title'] # '-' for DESC ordering
		verbose_name = 'Выставка'
		verbose_name_plural = 'Выставки'

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.title, instance=self)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		pass
		#return reverse('exhibition-detail', kwargs={'slug': self.slug })


''' Таблица Номинаций '''
class Nominations(models.Model):
	title = models.CharField('Номинация', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	description = models.TextField('Описание номинации', db_index=True, blank=True)
	logo = models.ImageField('Логотип', upload_to=logo_upload_folder, null=True, blank=True)

	# Metadata
	class Meta:
		ordering = ['title'] # '-' for DESC ordering
		verbose_name = 'Номинация'
		verbose_name_plural = 'Номинации'

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.title, instance=self)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		pass
		#return reverse('nomination-detail', kwargs={'slug': self.slug })

	def logo_thumb(self):
		get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'


''' Таблица Мероприятий '''
class Events(models.Model):
	title = models.CharField('Название мероприятия', max_length=250)
	description = models.TextField('Описание мероприятия', db_index=True)
	date_event = DateField('Дата мероприятия')
	time_start = TimeField('Начало мероприятия', unique=True)
	time_end = TimeField('Окончание мероприятия', unique=True)
	location = models.CharField('Зона проведения', max_length=75)
	hoster = models.CharField('Участник мероприятия', max_length=75)
	lector = models.CharField('Ведущий мероприятия', max_length=75)
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.SET_NULL, related_name='events', null=True, blank=True)

	# Metadata
	class Meta:
		ordering = ['title'] # '-' for DESC ordering
		verbose_name = 'Мероприятие'
		verbose_name_plural = 'Мероприятия'

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.title, instance=self)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		pass
		#return reverse('event-detail', kwargs={'slug': self.slug })


class Portfolio(models.Model):
	owner = models.ForeignKey(Exhibitors, on_delete=models.SET_NULL, related_name='exhibitor')
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.SET_NULL, related_name='exhibition', null=True, blank=True)
	nomination = models.ManyToManyField(Nominations, on_delete=models.SET_NULL, related_name='nomination')
	description = models.TextField('Описание работы', db_index=True)


class Image(models.Model):
	portfolio = models.ForeignKey(Portfolio, on_delete=models.SET_NULL, related_name='portfolio', null=True, blank=True)
	title = models.CharField('Заголовок', max_length=150, null=True, blank=True)
	description = models.CharField('Описание', max_length=255, null=True, blank=True)
	file = models.ImageField('Фото', upload_to='uploads/', default="/no-image.png", storage=MediaFileStorage(), unique=False)
	name = models.CharField('Имя файла', max_length=50, null=True)

	# Metadata
	class Meta:
		verbose_name = 'Изображение'
		verbose_name_plural = 'Изображения'

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		if not self.name:
			self.name = self.file.name.rsplit('/', 1)[-1]

		if not self.title:
			# take only file name
			self.title = os.path.splitext(self.file.name)[0]
		super().save(*args, **kwargs)

	def file_thumb(self):
		get_image_html(self.file)

	file_thumb.short_description = 'Миниатюра'

	@property
	def filename(self):
		return self.file.name.rsplit('/', 1)[-1]
