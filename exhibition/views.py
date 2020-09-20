from django.shortcuts import render

def index(request):
	classesList = ['home','is-nav']
	context = {
		'classes': classesList,
	}
	return render(request, 'index.html', context)
