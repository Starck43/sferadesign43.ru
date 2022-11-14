from django.db.models import Q

from .models import MetaSEO
from ads.models import Banner


class ExhibitionYearListMixin:
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower()
		context['exh_year'] = self.slug if self.slug != None else 'all'
		return context


class BannersMixin:
	def get_context_data(self, **kwargs):
		banners = Banner.get_banners(self)
		context = super().get_context_data(**kwargs)
		context['ads_banners'] = list(banners)
		if banners and banners[0].is_general:
			context['general_banner'] = banners[0]
			del context['ads_banners'][0]
		return context


class MetaSeoMixin:
	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.object = None

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		class_name = self.__class__.__name__
		model_name = self.model.__name__.lower()
		query = Q(model__model=model_name)
		if self.object:
			# если объект
			query.add(Q(post_id=self.object.id), Q.AND)
		else:
			# если список объектов
			query.add(Q(post_id__isnull=True), Q.AND)


		meta = MetaSEO.objects.filter(query)

		context['meta'] = meta[0] if meta else None
		return context
