from .models import Exhibitions, Organizer

""" Global context processor variables """
def common_context(request):
	context = {
		'exhibitions_list' : Exhibitions.objects.all(),
		'organizer' : Organizer.objects.all().first(),
	}
	return context
