from django.conf import settings

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.views.generic.list import ListView #, MultipleObjectMixin
from django.views.generic.detail import DetailView

from django.contrib.auth.models import User
from django.db.models import Count #, F, Q , OuterRef, Subquery, Prefetch
# from django.db.models.expressions import F, Value
#from django.db.models.functions import Coalesce

from .models import Category, Article


class article_list(ListView):
	model = Article
	template_name = 'blog/article_list.html'

	PAGE_SIZE = getattr(settings, 'ARTICLES_COUNT_PER_PAGE', 10) # Количество выводимых записей на странице

	def get_queryset(self):
		# self.page - текущая страница для получения диапазона выборки записей,  (см. функцию get ниже )
		self.page = int(self.page) if self.page else 1

		start_page = (self.page-1)*self.PAGE_SIZE # начало диапазона
		end_page = self.page*self.PAGE_SIZE # конец диапазона

		# Если выбраны опции фильтра, то найдем все номинации в текущей категории "self.slug"
		if self.filter_cat and self.filter_cat != 'all':
			#query = Q(category_id=int(self.filter_cat))
			posts = self.model.objects.filter(category_id=int(self.filter_cat))[start_page:end_page+1] # +1 сделано для выявления наличия следующей страницы
		else:
			posts = self.model.objects.all()[start_page:end_page+1] # +1 сделано для выявления наличия следующей страницы

		self.is_next_page = False if len(posts) <= self.PAGE_SIZE else True
		return posts #[:self.PAGE_SIZE]


	def get(self, request, *args, **kwargs):
		self.page = self.request.GET.get('page', None) # Параметр GET запроса ?page текущей страницы
		self.filter_cat = self.request.GET.get("article-category", None) # Выбранные опции checkbox в GET запросе (?nominations=[])

		if self.filter_cat or self.page:
			queryset = self.get_queryset()
			article_list = list(queryset.values())
			if self.is_next_page:
				article_list.pop()

			for i,q in enumerate(article_list):
				person = queryset[i].person()
				if person:
					q.update({'person':person.name})
					q.update({'person_url':person.get_absolute_url()})

			json_data = {
				'current_page': int(self.page or 1),
				'next_page': self.is_next_page,
				'articles': list(article_list),
				#'media_url': settings.MEDIA_URL,
			}
			return JsonResponse(json_data, safe=False)
		else:
			# выполняется при загрузке первой страницы
			return super().get(request, **kwargs)


	def get_context_data(self, **kwargs):
		attrs = Category.objects.prefetch_related('article_set').annotate(count=Count('article')).filter(count__gt=0).values('id','name','count')
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['articles',]
		context['page_title'] = self.model._meta.verbose_name_plural
		context['article_list'] = self.object_list[:self.PAGE_SIZE]
		context['filter_attributes'] = attrs
		context['cache_timeout'] = 86400
		return context



class article_detail(DetailView):
	model = Article

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['article']
		context['parent_link'] = '/articles/'
		context['cache_timeout'] = 86400
		return context


