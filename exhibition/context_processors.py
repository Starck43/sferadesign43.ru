from .apps import ExhibitionConfig
from .logic import IsMobile
from .models import Exhibitions


def common_context(request):
	""" Global context processor variables """
	exh_list = Exhibitions.objects.all().only('slug', 'date_start')
	meta = {
		'title': "Дизайнерская выставка Сфера Дизайна",
		'description': "Выставка дизайн-проектов, где представлены портфолио дизайнеров и победители в номинациях с 2008 года",
		'keywords': "дизайнерская выставка, реализованные проекты интерьеров, дизайн интерьеров, сфера дизайна, портфолио дизайнеров, победители выставки"
	}

	scheme = request.is_secure() and "https" or "http"
	site_url = '%s://%s' % (scheme, request.META['HTTP_HOST'])
	site_host = request.META['HTTP_HOST']

	return {
		'is_mobile': IsMobile(request),
		'separator': '|',
		'main_title': ExhibitionConfig.verbose_name,
		'exhibitions_list': exh_list,
		'site_url': site_url,
		'site_host': site_host,
		'scheme': scheme,
		# 'page_url'			: site_url + request.path,
		'default_meta': meta,
	}
