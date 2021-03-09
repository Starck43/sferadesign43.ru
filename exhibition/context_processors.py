#from django.views.decorators.cache import cache_page

from .models import Exhibitions
from .apps import ExhibitionConfig
from .logic import IsMobile


""" Global context processor variables """
def common_context(request):
	meta = {
		'description' : "Выставка реализованных дизайн-проектов Сфера Дизайна",
		'keywords' : "дизайнерская выставка, реализованные проекты интерьеров, лучшие интерьеры, дизайн интерьеров,сфера дизайна, современные отделочные материалы"
	}
	exh_list = Exhibitions.objects.all().only('slug', 'date_end')

	context = {
		'is_mobile'			: IsMobile(request),
		'separator'			: '|',
		'main_title'		: ExhibitionConfig.verbose_name,
		'exhibitions_list'	: exh_list,
		#'last_exh_date' : exh_list.first().date_end,
		'meta_default'		: meta
	}
	return context
