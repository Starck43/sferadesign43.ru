from .models import Exhibitions
from .apps import ExhibitionConfig
from .logic import IsMobile


""" Global context processor variables """
def common_context(request):
	meta = {
		'description' : "Выставка реализованных дизайн-проектов Сфера Дизайна",
		'keywords' : "дизайнерская выставка, реализованные проекты интерьеров, лучшие интерьеры, дизайн интерьеров,сфера дизайна, современные отделочные материалы"
	}
	context = {
		'is_mobile' :IsMobile(request),
		'main_title': ExhibitionConfig.verbose_name,
		'exhibitions_list' : Exhibitions.objects.all().only('slug', 'date_start'),
		#'organizer' : Organizer.objects.all().first(),
		'meta_default': meta
	}
	return context
