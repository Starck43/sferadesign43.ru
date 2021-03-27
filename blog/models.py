from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

from django.db.models import F, Q
from django.db.models.functions import Coalesce

from uuslug import uuslug
from ckeditor_uploader.fields import RichTextUploadingField

from exhibition.models import Exhibitors, Partners, Jury


class Category(models.Model):
	name = models.CharField('Раздел', max_length=150, unique=True)
	slug = models.SlugField('Ярлык', max_length=150, unique=True, null=True)

	class Meta:
		verbose_name = 'Раздел статей'
		verbose_name_plural = 'Разделы статей'
		ordering = ['name']
		db_table = 'article_category'

	# def get_absolute_url(self):
	# 	return reverse('articles-list-by-category', args=[self.slug.lower()])

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.name.lower(), instance=self)
		super().save(*args, **kwargs)


class Article(models.Model):
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name = 'Раздел')
	owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name = 'Автор статьи')
	title = models.CharField('Название статьи', max_length=150)
	slug = models.SlugField('Ярлык', max_length=150, unique=True, null=True)
	content = RichTextUploadingField('Статья', blank=True)
	modified_date = models.DateField('Дата изменения', auto_now_add=True)

	class Meta:
		verbose_name = 'Статья'
		verbose_name_plural = 'Статьи'
		ordering = ['-modified_date']
		db_table = 'article'


	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = uuslug(self.title.lower(), instance=self)
		super().save(*args, **kwargs)

	def person(self):
		try:
			post = Exhibitors.objects.get(user=self.owner)
		except Exhibitors.DoesNotExist:
			try:
				post = Partners.objects.get(user=self.owner)
			except Partners.DoesNotExist:
				try:
					post = Jury.objects.get(user=self.owner)
				except Jury.DoesNotExist:
					post = None
		return post

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		return reverse('blog:article-detail-url', kwargs={'pk': self.id})



