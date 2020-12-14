from .models import Exhibitions
from .apps import ExhibitionConfig


""" Global context processor variables """
def common_context(request):
	meta = {
		'description' : "Сайт дизайн-выставки Сфера-дизайна",
		'keywords' : "дизайн выставка, сфера дизайна"
	}
	context = {
		'main_title': ExhibitionConfig.verbose_name,
		'exhibitions_list' : Exhibitions.objects.all().only('slug', 'date_start'),
		#'organizer' : Organizer.objects.all().first(),
		'meta_default': meta
	}
	return context
