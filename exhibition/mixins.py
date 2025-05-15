from .models import MetaSEO
from ads.models import Banner


class ExhibitionYearListMixin:
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower()
		context['exh_year'] = self.kwargs.get('exh_year', None)
		if not context.get('cache_timeout'):
			context['cache_timeout'] = 86400
		return context


class BannersMixin:
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		model_name = self.model.__name__.lower()
		banners = Banner.get_banners(model_name)
		context['ads_banners'] = list(banners)
		if banners and banners[0].is_general:
			context['general_banner'] = banners[0]
			del context['ads_banners'][0]
		return context


class MetaSeoMixin:
	object = None

	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['meta'] = MetaSEO.get_content(self.model, self.object.id if self.object else None)
		return context
