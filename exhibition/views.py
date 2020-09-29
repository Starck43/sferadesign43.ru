from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView #, MultipleObjectMixin
from django.views.generic.detail import DetailView
from django.db.models import Q, Prefetch
from .models import *


""" Main page """
def index(request):
	classesList = ['home','is-nav']
	context = {
		'classes': classesList,
	}
	return render(request, 'index.html', context)


""" Exhibitors view """
class exhibitors_list(ListView):
	model = Exhibitors
	template_name = 'exhibitors_list.html'
	context_object_name = 'exhibitors'

	paginate_by = 10

	def get_queryset(self):
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		if search_query:
			query_fields_or = (Q(name__icontains=search_query) | Q(description__icontains = search_query))
			posts = self.model.objects.filter(query_fields_or)
		else:
			if slug == None:
				posts = self.model.objects.all()
			else:
				#posts = self.model.objects.filter(exhibitions__exh_year=slug)
				posts = self.model.objects.prefetch_related('exhibitors_for_exh').filter(exhibitions__date_start__year=slug)
				self.exhibitors = posts
				
		return posts

	def get_context_data(self, **kwargs):
		year = self.kwargs['exh_year']
		context = super().get_context_data(**kwargs)
		context['classes'] = ['participants',]
		context['exh_year'] = self.exhibitors.date_start[0]
		# context['exh_year'] = self.kwargs['exh_year']
		return context 


class exhibitors_detail(DetailView):
	model = Exhibitors
	template_name = 'exhibitors_detail.html'
	context_object_name = 'exhibitor'


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['classes'] = ['participant-detail']
		# context['exhibitions'] = self.object.exhibitions_set.all()
		context['exhibitions'] = ', '.join(Exhibitions.objects.filter(exhibitions=self.object).values_list('title', flat=True))

		return context


""" Winners view """
class winners_list(ListView):
	model = Winners
	template_name = 'winners_list.html'
	context_object_name = 'winners'

	def get_queryset(self):
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		if search_query:
			query_fields_or = (Q(exhibitor__name__icontains=search_query) | Q(nomination__title__icontains = search_query))
			posts = self.model.objects.select_related().filter(query_fields_or)
		else:
			if slug == None:
				# posts = Exhibitors.objects.prefetch_related('exhibitor').distinct()
				posts = self.model.objects.select_related('exhibitor').sorted_by('exhibitor__name')
			else:
				posts = self.model.objects.select_related().filter(exhibition__date_start__year=slug)
				#posts = self.model.objects.select_related('exhibition').filter(exhibitions__date_start__year=slug)
				
		return posts
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['classes'] = ['winners',]
		context['exh_year'] = self.kwargs['exh_year']

		return context

	