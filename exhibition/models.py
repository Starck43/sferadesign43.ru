from django.db import models
from django.contrib.auth.models import User
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


"""Abstract model for Exhibitors, Jury, Partners"""
class Person(models.Model):
	name = models.CharField('Имя контакта', max_length=100)
	slug = models.SlugField('Ярлык', max_length=100, unique=True)
	description = models.TextField('Информация о контакте', db_index=True, blank=True)
	avatar = models.ImageField('Аватар', upload_to=avatar_upload_folder, null=True, blank=True)

	class Meta:
		ordering = ['name'] # '-' for DESC ordering
		abstract = True    # The table will not be created
		
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
			get_image_html(self.avatar)

		photo_thumb.short_description = 'Аватар'


"""Abstract model for Exhibitors and Partners"""
class Profile(models.Model):
	address = models.CharField('Адрес', max_length=100, blank=True)
	phone = models.PhoneNumberField('Контактный телефон', blank=True)
	email = models.EmailField('Контактный E-mail', max_length=75, blank=True)
	site = models.URLField('Сайт', max_length=75, blank=True)
	vk = models.URLField('Вконтакте', max_length=75, blank=True)
	fb = models.URLField('Facebook', max_length=75, blank=True)
	instagram = models.URLField('Instagram', max_length=75, blank=True)
	logo = models.ImageField('Логотип', upload_to=logo_upload_folder, null=True, blank=True)

	class Meta:
		abstract = True    # The table will not be created
		
	def logo_thumb(self):
		get_image_html(self.logo)

	logo_thumb.short_description = 'Логотип'


class Exhibitors(Person, Profile):
	user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name = 'Аккаунт')
	
	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Участник выставки'
		verbose_name_plural = 'Участники выставки'

	def get_absolute_url(self):
		pass
		return reverse('exhibitor-detail', kwargs={'slug': self.slug })


class Jury(Person):

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Жюри'
		verbose_name_plural = 'Жюри'

	def get_absolute_url(self):
		pass
		#return reverse('jury-detail', kwargs={'slug': self.slug })


class Partners(Person, Profile):

	# Metadata
	class Meta(Person.Meta):
		verbose_name = 'Партнер выставки'
		verbose_name_plural = 'Партнеры выставки'

	def get_absolute_url(self):
		pass
		#return reverse('partner-detail', kwargs={'slug': self.slug })


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



''' Таблица Выставки '''
class Exhibitions(models.Model):
	title = models.CharField('Название выставки', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True)
	description = models.TextField('Описание выставки', db_index=True, blank=True)
	date_start = DateField('Начало выставки', unique=True)
	date_end = DateField('Окончание выставки', unique=True)
	location = models.CharField('Расположение выставки', max_length=200)
	exhibitors = models.ManyToManyField(Exhibitors,  on_delete=models.SET_NULL, related_name='exhibitors_for_exh', verbose_name = 'Участники')
	nominations = models.ManyToManyField(Nominations, on_delete=models.SET_NULL, related_name='nominations_for_exh', verbose_name = 'Номинации')

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

	@property
    def exh_year(self):
        # return only Exhibition's year from date_start
        return self.date_start.strftime('%Y')


''' Таблица Мероприятий '''
class Events(models.Model):
	title = models.CharField('Название мероприятия', max_length=250)
	description = models.TextField('Описание мероприятия', db_index=True, blank=True)
	date_event = DateField('Дата мероприятия')
	time_start = TimeField('Начало мероприятия', unique=True)
	time_end = TimeField('Окончание мероприятия', unique=True)
	location = models.CharField('Зона проведения', max_length=75, blank=True)
	hoster = models.CharField('Участник мероприятия', max_length=75)
	lector = models.CharField('Ведущий мероприятия', max_length=75)
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.SET_NULL,  null=True, blank=True, verbose_name = 'Выставка')

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


''' Таблица Победителей '''
class Winners(models.Model):
	
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.CASCADE, null=True, verbose_name = 'Выставка')
	nomination = models.ForeignKey(Nominations, on_delete=models.CASCADE, null=True, verbose_name = 'Номинация')
	exhibitor = models.ForeignKey(Exhibitors, on_delete=models.CASCADE, null=True, verbose_name = 'Победитель')

	def __str__(self):
		return "%s (%s), %s" % (
            self.exhibitor.name,
            self.nomination.title,
            self.exhibition.exh_year,
        )
		
	def get_absolute_url(self):
		pass
		#return reverse('winner-detail', kwargs={'slug': self.slug })



class Portfolio(models.Model):
	owner = models.ForeignKey(Exhibitors, on_delete=models.SET_NULL, null=True, blank=True, verbose_name = 'Участник')
	exhibition = models.ForeignKey(Exhibitions, on_delete=models.SET_NULL, null=True, blank=True, verbose_name = 'Выставка')
	nominations = models.ManyToManyField(Nominations, on_delete=models.SET_NULL, null=True, blank=True, related_name='nominations_for_portfolio', verbose_name = 'Номинации')
	title = models.CharField('Название работы', max_length=200, blank=True)
	description = models.TextField('Описание работы', db_index=True, blank=True)

	# Metadata
	class Meta:
		ordering = ['-exhibition.date_start'] # '-' for DESC ordering
		verbose_name = 'Портфолио'
		verbose_name_plural = 'Портфолио работ'
		
	def __str__(self):
		return self.title
		
	def get_absolute_url(self):
		pass
		#return reverse('portfolio-detail', kwargs={'year': self.exhibition.date_start, 'owner': self.owner.slug, 'id': self.pk })


class Image(models.Model):
	portfolio = models.ForeignKey(Portfolio, on_delete=models.SET_NULL, related_name='portfolio', blank=True, verbose_name = 'Портфолио')
	title = models.CharField('Заголовок', max_length=100, null=True, blank=True)
	description = models.CharField('Описание', max_length=250, blank=True)
	file = models.ImageField('Фото', upload_to='uploads/', default="/no-image.png", storage=MediaFileStorage(), unique=False)

	# Metadata
	class Meta:
		verbose_name = 'Изображение'
		verbose_name_plural = 'Изображения'

	def __str__(self):
		return self.title

	def get_file_name(self):
		return self.file.name.rsplit('/', 1)[-1]
	
	def save(self, *args, **kwargs):	
		if not self.title:
			# take only file name without ext
			self.title = os.path.splitext(self.file.name)[0]
		super().save(*args, **kwargs)

	def file_thumb(self):
		get_image_html(self.file)

	file_thumb.short_description = 'Миниатюра'

	@property
	def filename(self):
		return self.file.name.rsplit('/', 1)[-1]
