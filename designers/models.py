from ckeditor.fields import RichTextField
from django.db import models
from django.urls import reverse
from smart_selects.db_fields import ChainedManyToManyField
from sorl.thumbnail import delete

from exhibition.logic import MediaFileStorage, image_resize, designers_upload_to
from exhibition.models import Exhibitors, Partners, Portfolio

LOGO_FOLDER = 'logos/'
AVATAR_FOLDER = 'avatars/'


class Designer(models.Model):
	""" Страница Дизайнера """
	STATUS = (
		(1, 'на модерации'),
		(2, 'опубликован'),
		(3, 'приостановлен'),
	)
	owner = models.OneToOneField(
		Exhibitors, on_delete=models.CASCADE, related_name='designer',
		verbose_name='Владелец сайта'
	)
	title = models.CharField(
		'Заголовок сайта', max_length=255, blank=True,
		help_text='Укажите дополнительное название студии рядом с логотипом, если необходимо'
	)
	slug = models.SlugField(
		'Имя сайта', max_length=20, unique=True,
		help_text='Субдомен или часть адреса сайта латиницей, типа sitename.sd43.ru'
	)
	logo = models.ImageField('Логотип', upload_to=LOGO_FOLDER, storage=MediaFileStorage(), null=True, blank=True)
	avatar = models.ImageField('Аватар', upload_to=AVATAR_FOLDER, storage=MediaFileStorage(), null=True, blank=True)
	about = RichTextField('О себе', blank=True)
	background = models.ImageField(
		'Основное изображение', upload_to=designers_upload_to, storage=MediaFileStorage(),
		null=True, blank=True, help_text='Фоновое изображение в шапке сайта'
	)
	exh_portfolio = ChainedManyToManyField(
		Portfolio,
		chained_field="owner",
		chained_model_field="owner",
		blank=True,
		verbose_name='Выставочные проекты',
		related_name="exh_portfolio",
		limit_choices_to=models.Q(exhibition__isnull=False)
	)
	add_portfolio = ChainedManyToManyField(
		Portfolio,
		chained_field="owner",
		chained_model_field="owner",
		blank=True,
		verbose_name='Вневыставочные проекты',
		related_name="add_portfolio",
		limit_choices_to={'exhibition': None}
	)

	partners = models.ManyToManyField(
		Partners, verbose_name='Партнеры', blank=True,
		help_text='Партнеры выставки, с которыми есть сотрудничество'
	)
	whatsapp = models.CharField(
		'WhatsApp', max_length=75, blank=True, default="wa.me",
		help_text='Укажите номер телефона только цифрами'
	)
	telegram = models.CharField(
		'Telegram', max_length=75, blank=True, default="t.me",
		help_text='Укажите имя пользователя username'
	)
	show_phone = models.BooleanField('Показать телефон в контактах?', blank=True, default=True)
	show_email = models.BooleanField('Показать почтовый адрес в контактах?', blank=True, default=True)

	status = models.SmallIntegerField('Статус', choices=STATUS, default=1)
	pub_date_start = models.DateField('Начало публикации', null=True, blank=True)
	pub_date_end = models.DateField('Окончание публикации', null=True, blank=True)
	comment = models.CharField('Комментарий', max_length=255, blank=True)

	class Meta:
		verbose_name = 'Страница дизайнера'
		verbose_name_plural = 'Страницы дизайнеров'
		ordering = ['owner']
		db_table = 'designer_pages'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.original_avatar = self.avatar
		self.original_logo = self.logo
		self.original_background = self.background

	def __iter__(self):
		for f in self._meta.fields:
			name = f.name
			label = f.verbose_name
			value = f.value_to_string(self)
			link = None
			if name in ['whatsapp', 'telegram'] and value and type(f.default) is str:
				value = value.strip('@')
				value = value.rsplit('/', 1)[-1]
				link = 'https://' + f.default + '/' + value

			yield (name, label, value, link)

	def save(self, *args, **kwargs):
		# если файл заменен, то требуется удалить все миниатюры в кэше у sorl-thumbnails
		if self.original_avatar and self.original_avatar != self.avatar:
			delete(self.original_avatar)

		if self.original_logo and self.original_logo != self.logo:
			delete(self.original_logo)

		if self.original_background and self.original_background != self.background:
			delete(self.original_background)

		resized_avatar = image_resize(self.avatar, [600, 600])
		if resized_avatar and resized_avatar != 'error':
			self.avatar = resized_avatar

		resized_logo = image_resize(self.logo, [300, 300])
		if resized_logo and resized_logo != 'error':
			self.logo = resized_logo

		resized_background = image_resize(self.background, [1920, 1080])
		if resized_background and resized_background != 'error':
			self.background = resized_background

		super().save(*args, **kwargs)

		if resized_avatar != 'error':
			self.original_avatar = self.avatar

		if resized_logo != 'error':
			self.original_logo = self.logo

		if resized_background != 'error':
			self.original_background = self.background

	def get_absolute_url(self):
		return reverse('designers:portfolio-page-url', kwargs={'slug': self.slug.lower()})

	def __str__(self):
		return self.owner.name


class Customer(models.Model):
	""" Заказчики дизайнеров """
	designer = models.ForeignKey(Designer, on_delete=models.CASCADE, related_name='customers', verbose_name='Дизайнер')
	name = models.CharField('Имя заказчика', max_length=255)
	excerpt = models.TextField('Дополнительное описание', blank=True)
	logo = models.ImageField('Логотип', upload_to=LOGO_FOLDER, storage=MediaFileStorage(), null=True, blank=True)
	link = models.URLField(
		'Ссылка на проект',
		blank=True,
		help_text='Внешняя ссылка для перехода на портфолио или сайт заказчика'
	)

	# Metadata
	class Meta:
		verbose_name = 'Заказчик'
		verbose_name_plural = 'Заказчики'
		db_table = 'customers'
		ordering = ['-logo', 'name']

	def __str__(self):
		return self.name + ' ' + self.excerpt


class Achievement(models.Model):
	""" Таблица Достижений """
	STATUS = (
		(1, 'другие выставки'),
		(2, 'публикации в СМИ'),
	)
	group = models.SmallIntegerField('Вид события', choices=STATUS, default=1)
	designer = models.ForeignKey(
		Designer,
		on_delete=models.CASCADE,
		related_name='achievements',
		verbose_name='Дизайнер'
	)
	title = models.CharField('Заголовок', max_length=255)
	description = models.TextField('Дополнительное описание', blank=True)
	link = models.URLField(
		'Ссылка на источник', blank=True,
		help_text='Внешняя ссылка для перехода к источнику информации'
	)
	date = models.DateField('Дата события', blank=True)

	# Metadata
	class Meta:
		ordering = ['group', 'date']
		verbose_name = 'Достижение'
		verbose_name_plural = 'Достижения'
		db_table = 'achievements'

	def __str__(self):
		return self.title
