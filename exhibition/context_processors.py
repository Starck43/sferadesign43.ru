#from django.views.decorators.cache import cache_page
from django.conf import settings
from django.urls import resolve, Resolver404

from .models import Exhibitions, MetaSEO
from .apps import ExhibitionConfig
from .logic import IsMobile

""" Global context processor variables """
def common_context(request):
	exh_list = Exhibitions.objects.all().only('slug', 'date_end')
	meta = {
		'title'			: "Дизайнерская выставка Сфера Дизайна",
		'description'	: "Выставка дизайн-проектов, где представлены портфолио дизайнеров и победители в номинациях с 2008 года",
		'keywords'		: "дизайнерская выставка, реализованные проекты интерьеров, дизайн интерьеров, сфера дизайна, портфолио дизайнеров, победители выставки"
	}

	scheme = request.is_secure() and "https" or "http"
	site_url = '%s://%s' % (scheme, request.META['HTTP_HOST'])

	context = {
		'is_mobile'			: IsMobile(request),
		'separator'			: '|',
		'main_title'		: ExhibitionConfig.verbose_name,
		'exhibitions_list'	: exh_list,
		'site_url'			: site_url,
		#'page_url'			: site_url + request.path,
		'default_meta'		: meta,
	}
	return context
