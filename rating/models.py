from django.db import models
from django.contrib.auth.models import User

from exhibition.models import Portfolio


"""Рейтинг"""
class Rating(models.Model):
	STARS = (
		(1,'1 звезда'),
		(2,'2 звезды'),
		(3,'3 звезды'),
		(4,'4 звезды'),
		(5,'5 звезд'),
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name = 'Пользователь')
	portfolio = models.ForeignKey(Portfolio, related_name='rated_portfolio', on_delete=models.CASCADE, verbose_name='Портфолио')
	star = models.SmallIntegerField('Оценка',choices=STARS)
	ip = models.CharField("IP адрес", max_length=15)

	class Meta:
		verbose_name = "Рейтинг"
		verbose_name_plural = "Рейтинги"
		unique_together = ('user', 'portfolio',)

	@property
	def fullname(self):
		if self.user:
			if (not self.user.first_name) and (not self.user.last_name) :
				return self.user.username
			else:
				return "%s %s" % (self.user.first_name, self.user.last_name)
		else:
			return ''

	fullname.fget.short_description = 'Автор рейтинга'

	def __str__(self):
		return f"{self.star} - {self.portfolio}"

	def has_rated(self, portfolio_id, user):
		return self.objects.filter( portfolio_id=portfolio_id, user=user).first()

	""" Recalculate the totals """
	def calculate(self):
		aggregates = self.rated_portfolio.aggregate(total=models.Sum('star'), average=models.Avg('star'), count=models.Count('star'))
		self.count = aggregates.get('count') or 0
		self.total = aggregates.get('total') or 0
		self.average = aggregates.get('average') or 0.0
		return self


"""Отзывы"""
class JuryRating(models.Model):
	"""Оценки жюри (отдельно от общего рейтинга)"""
	STARS = (
		(1, '1 звезда'),
		(2, '2 звезды'),
		(3, '3 звезды'),
		(4, '4 звезды'),
		(5, '5 звезд'),
	)
	jury = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Член жюри', limit_choices_to={'jury__isnull': False})
	portfolio = models.ForeignKey(Portfolio, related_name='jury_ratings', on_delete=models.CASCADE, verbose_name='Портфолио')
	star = models.SmallIntegerField('Оценка', choices=STARS)
	exhibition = models.ForeignKey('exhibition.Exhibitions', on_delete=models.CASCADE, verbose_name='Выставка')
	created_date = models.DateTimeField('Дата оценки', auto_now_add=True)
	ip = models.CharField("IP адрес", max_length=15, blank=True)

	class Meta:
		verbose_name = "Оценка жюри"
		verbose_name_plural = "Оценки жюри"
		unique_together = ('jury', 'portfolio', 'exhibition')
		ordering = ['-created_date']

	@property
	def fullname(self):
		if self.jury:
			if (not self.jury.first_name) and (not self.jury.last_name):
				return self.jury.username
			else:
				return f"{self.jury.first_name} {self.jury.last_name}"
		return ''

	fullname.fget.short_description = 'Член жюри'

	def __str__(self):
		return f"{self.star} - {self.portfolio} (Жюри: {self.fullname})"

	@classmethod
	def has_rated(cls, portfolio_id, user, exhibition_id):
		"""Проверка, выставлял ли член жюри уже оценку"""
		return cls.objects.filter(
			portfolio_id=portfolio_id, 
			jury=user, 
			exhibition_id=exhibition_id
		).exists()

	@classmethod
	def calculate_jury_average(cls, portfolio_id, exhibition_id):
		"""Расчет средней оценки жюри для конкретной выставки"""
		from django.db.models import Avg, Count
		aggregates = cls.objects.filter(
			portfolio_id=portfolio_id, 
			exhibition_id=exhibition_id
		).aggregate(
			average=Avg('star'), 
			count=Count('star')
		)
		return {
			'count': aggregates.get('count') or 0,
			'average': aggregates.get('average') or 0.0
		}


class Reviews(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name = 'Пользователь')
	parent = models.ForeignKey('self', related_name='parent_comments', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Родитель')
	group = models.ForeignKey('self', related_name='group_comments', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Группа')
	portfolio = models.ForeignKey(Portfolio, related_name='comments_portfolio', on_delete=models.CASCADE, verbose_name='Портфолио')
	message = models.TextField("Сообщение", max_length=3000)
	posted_date = models.DateTimeField("Опубликовано", auto_now_add=True, blank=True)

	class Meta:
		verbose_name = "Комментарий"
		verbose_name_plural = "Комментарии"
		ordering = ['-posted_date','group_id','parent_id']
		unique_together = (('id', 'parent'), ('id', 'group'),)

	def count(self):
		aggregates = self.comments_portfolio.aggregate(count=models.Count('portfolio'))
		return aggregates.get('count') or 0

	def reply_count(self):
		aggregates = self.parent_comments.aggregate(count=models.Count('parent'))
		return aggregates.get('count') or 0


	@property
	def fullname(self):
		if self.user:
			if (not self.user.first_name) and (not self.user.last_name) :
				return self.user.username
			else:
				return "%s %s" % (self.user.first_name, self.user.last_name)
		else:
			return ''

	fullname.fget.short_description = 'Комментатор'


	def __str__(self):
		return f"ID{self.id}: {self.user}"

