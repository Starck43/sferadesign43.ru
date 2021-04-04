from datetime import date

from django.db import models
from django.db.models import Q, Value, CharField

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from blog.models import Article
from exhibition.models import Exhibitors, Partners
from exhibition.logic import get_image_html, MediaFileStorage
from sorl.thumbnail import delete

ads_folder = 'ads/'


class Banner(models.Model):
	title = models.CharField('Название баннера', max_length=100)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name = 'Владелец')
	file_200 = models.FileField('Файл A', upload_to=ads_folder, storage=MediaFileStorage(), null=True, blank=True, help_text="Квадратный баннер 200х200 пикс. для бокового размещения")
	file_1000 = models.FileField('Файл B', upload_to=ads_folder, storage=MediaFileStorage(), null=True, blank=True, help_text="Горизонталтный баннер 1000х200 пикс. для размещения в центральной части сайта")
	show_start = models.DateField('Начало показа', null=True, blank=True)
	show_end = models.DateField('Окончание показа', null=True, blank=True)
	pages = models.ManyToManyField(ContentType, related_name='banner_pages', blank=True, verbose_name='Разделы', help_text="Отметьте те разделы, где будет демонстрироваться баннер")
	article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, verbose_name = 'Статья', help_text="Можно указать статью, в конце которой будет показываться баннер")
	is_general = models.BooleanField('Генеральный партнер ', default=False, help_text="Баннер партнера отобразится вверху страницы")
	sort = models.IntegerField('Индекс сортировки', null=True, blank=True)

	class Meta:
		verbose_name = 'Баннер'
		verbose_name_plural = 'Баннеры'
		ordering = ['-is_general', '-show_end', 'sort',]
		#unique_together = ['article']

	def __str__(self):
		return self.title


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.file_200_current = self.file_200
		self.file_1000_current = self.file_1000


	def save(self, *args, **kwargs):
		# если файл заменен, то требуется удалить все миниатюры в кэше у sorl-thumbnails
		if self.file_1000_current and self.file_1000_current != self.file_1000:
			delete(self.file_1000_current)
		super().save(*args, **kwargs)
		self.file_1000_current = self.file_1000


	def delete(self, *args, **kwargs):
		# физически удалим файл и его sorl-миниатюры с диска
		if self.file_200:
			delete(self.file_200)
		if self.file_1000:
			delete(self.file_1000)

		super().delete(*args, **kwargs)


	def get_banners(self):
		model_name = self.model.__name__.lower() #возьмем имя модели для отбора баннеров
		today = date.today()

		banners = Banner.objects.filter(
			Q(pages__model=model_name) & (Q(show_start__lte=today) & Q(show_end__gte=today) | Q(is_general=True))
		).annotate(page=Value(model_name, output_field=CharField())) # добавим значение модели как строка
		return banners


	def owner(self):
		try:
			q = Exhibitors.objects.get(user=self.user)
		except Exhibitors.DoesNotExist:
			try:
				q = Partners.objects.get(user=self.user)
			except Partners.DoesNotExist:
				q = None
		return q


	def banner_thumb(self):
		if self.file_200:
			return get_image_html(self.file_200)
		else:
			return get_image_html(self.file_1000)


	banner_thumb.short_description = 'Миниатюра'
