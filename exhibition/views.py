from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView #, MultipleObjectMixin
from django.views.generic.detail import DetailView
from django.db.models import Q, Prefetch #, Count
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce

from .models import *


""" Main page """
def index(request):
	classesList = ['home','is-nav']
	context = {
		'html_classes': classesList,
	}
	return render(request, 'index.html', context)


def contacts(request, section=''):
	context = {
		'html_classes': ['contacts'],
	}
	return render(request, 'contacts.html', context)


""" Exhibitons view """
class exhibitions_list(ListView):
	model = Exhibitions

	paginate_by = 10

	def get_queryset(self):
		self.exh_years_list = None
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')

		self.exhibitions = super().get_queryset()
		if search_query:
			query_fields_or = (Q(title__icontains=search_query) | Q(description__icontains = search_query))
			posts = self.exhibitions.filter(query_fields_or)
		else:
			if slug == None:
				posts = self.exhibitions
			else:
				posts = self.exhibitions.filter(date_start__year=slug)

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibitions',]
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


""" Nominations view """
# class nominations_list(ListView):
# 	model = Nominations
# 	template_name = 'exhibition/members_list.html'

# 	def get_queryset(self):
# 		slug = self.kwargs['exh_year']
# 		search_query = self.request.GET.get('q')
# 		self.exhibition = None

# 		if search_query:
# 			query_fields_or = (Q(title__icontains=search_query) | Q(description__icontains = search_query))
# 			posts = self.model.objects.filter(query_fields_or)
# 		else:
# 			if slug == None:
# 				exhibition = Exhibitions.objects.all().order_by('-date_start')[0]
# 			else:
# 				exhibition = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('nominations')[0]
# 				self.exhibition = exhibition
# 			posts = exhibition.nominations.only('title').order_by('title')

# 		return posts

# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		context['html_classes'] = ['nominations',]
# 		context['absolute_url'] = '/nominations/'
# 		context['page_title'] = self.model._meta.verbose_name_plural
# 		context['exhibition'] = self.exhibition

# 		return context


""" Nominations view """
class events_list(ListView):
	model = Events
	template_name = 'exhibition/members_list.html'

	def get_queryset(self):
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		self.exhibition = None

		if search_query:
			query_fields_or = (Q(title__icontains=search_query) | Q(description__icontains = search_query))
			posts = self.model.objects.filter(query_fields_or)
		else:
			exhibition = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('events')[0]
			self.exhibition = exhibition
			posts = exhibition.events.only('title').order_by('title')

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['events',]
		context['absolute_url'] = '/events/'

		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context


""" Exhibitors view """
class exhibitors_list(ListView):
	model = Exhibitors
	template_name = 'exhibition/members_list.html'


	def get_queryset(self):
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		self.exhibition = None

		if search_query:
			query_fields_or = (Q(name__icontains=search_query) | Q(description__icontains = search_query))
			posts = self.model.objects.filter(query_fields_or)
		else:
			if slug == None:
				posts = self.model.objects.all()
			else:
				exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('exhibitors')[0]
				posts = exhibition_by_year.exhibitors.only('name')
				self.exhibition = exhibition_by_year
				#exh_query = Exhibitions.objects.filter(date_start__year=slug).values_list('exhibitors__id')
				#posts = self.model.objects.filterter(pk__in=exh_query)

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants',]
		context['absolute_url'] = '/exhibitors/'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context


""" Winners view """
class winners_list(ListView):
	model = Winners
	template_name = 'exhibition/members_list.html'

	def get_queryset(self):
		self.exhibition = None
		self.exh_years_list = None
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')

		if search_query:
			query_fields_or = (Q(exhibitor__name__icontains=search_query) | Q(nomination__title__icontains = search_query))
			posts = self.model.objects.select_related().filter(query_fields_or)
		else:
			self.exh_years_list = Exhibitions.objects.all().values_list('date_start__year',flat=True)
			if slug == None:
				# posts = Exhibitors.objects.prefetch_related('exhibitors_for_exh')
				# winners = self.model.objects.only('exhibitor__name')
				# posts = Exhibitors.objects.filter(id__in=winners).order_by('name')
				posts = self.model.objects.select_related('exhibitors').values_list('exhibitor__name', flat=True).distinct().order_by('exhibitor__name') #.annotate(exhibitors_count=Count('exhibitor_id'))
			else:
				posts = self.model.objects.select_related('exhibition').filter(exhibition__date_start__year=slug).order_by('exhibitor__name')
				# winners = self.model.objects.prefetch_related(Prefetch('exhibitor', queryset=Exhibitors.objects.only('name'))).select_related('exhibition').only('exhibition__date_start').filter(exhibition__date_start__year=slug)
				self.exhibition = posts[0].exhibition

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants-list',]
		context['absolute_url'] = '/winners/'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context



""" Partners view """
class partners_list(ListView):
	model = Partners
	template_name = 'exhibition/members_list.html'

	def get_queryset(self):
		queryset = super().get_queryset()
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		self.exhibition = None


		if search_query:
			query_fields_or = (Q(name__icontains=search_query) | Q(description__icontains = search_query))
			posts = queryset.filter(query_fields_or)
		else:
			if slug == None:
				posts = queryset
			else:
				exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('partners')[0]
				posts = exhibition_by_year.partners.only('name')
				self.exhibition = exhibition_by_year

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants-list',]
		context['absolute_url'] = '/partners/'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context



""" Jury view """
class jury_list(ListView):
	model = Jury
	template_name = 'exhibition/members_list.html'

	def get_queryset(self):
		queryset = super().get_queryset()
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		self.exhibition = None

		if search_query:
			query_fields_or = (Q(name__icontains=search_query) | Q(description__icontains = search_query))
			posts = queryset.filter(query_fields_or)
		else:
			if slug == None:
				posts = queryset
			else:
				exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('jury')[0]
				posts = exhibition_by_year.jury.only('name')
				self.exhibition = exhibition_by_year

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants-list',]
		context['absolute_url'] = '/jury/'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context



""" Exhibitors & Winners detail """
class exhibitor_detail(DetailView):
	model = Exhibitors
	template_name = 'exhibition/members_detail.html'

	def get_context_data(self, **kwargs):
		slug = self.kwargs['slug']
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant-detail']
		context['winners_list'] = Nominations.objects.prefetch_related('nomination_for_winner').filter(nomination_for_winner__exhibitor__slug=slug).annotate(exh_year=F('nomination_for_winner__exhibition__slug')).values('title', 'slug', 'exh_year').order_by('exh_year')
		#context['exh_list'] = ', '.join(Exhibitions.objects.filter(exhibitors=self.object).values_list('title', flat=True))

		return context


""" Jury detail """
class jury_detail(DetailView):
	model = Jury
	template_name = 'exhibition/members_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant-detail']

		return context


""" Partners detail """
class partner_detail(DetailView):
	model = Partners
	template_name = 'exhibition/members_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant']

		return context


""" Exhibitions detail """
class exhibition_detail(DetailView):
	model = Exhibitions

	def get_context_data(self, **kwargs):
		slug = self.kwargs['slug'] # current exhibition year
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibition']

		nominations_with_winners = self.object.nominations.filter(nomination_for_winner__exhibition_id=self.object.id).annotate(exhibitor_name=F('nomination_for_winner__exhibitor__name'), exhibitor_slug=F('nomination_for_winner__exhibitor__slug')).values('id','exhibitor_name','exhibitor_slug','title', 'slug') #.filter(nomination_for_winner__exhibition_id=self.object.id).values('nomination_for_winner__exhibition_id', 'nomination_for_winner__exhibitor__name', 'title')#.filter(nomination_for_winner__exhibition_id=self.object.id)
		if not nominations_with_winners:
			context['nominations_list'] = self.object.nominations.all
		else:
			context['nominations_list'] = nominations_with_winners
		context['exhibition'] = self.model.objects.prefetch_related('exhibitors','partners','jury','events').filter(date_start__year=slug)[0]
		context['events_title'] = Events._meta.verbose_name_plural

		return context


""" Nomination detail """
class nomination_detail(DetailView):
	model = Nominations
	slug_url_kwarg = 'name'
	#context_object_name = 'portfolio'

	def get_context_data(self, **kwargs):
		exh_year = self.kwargs['slug']
		#nom_name = self.kwargs['name']
		nom = self.object.id
		winner = None
		try:
			exhibitors = None
			winner = Winners.objects.get(exhibition__slug=exh_year,nomination=nom)
			try:
				portfolio = Portfolio.objects.prefetch_related('images').get(exhibition__slug=exh_year,nominations=nom, owner=winner.exhibitor.id)
			except Portfolio.DoesNotExist:
				portfolio = None

		except Winners.DoesNotExist:
			portfolio = None
			exhibitors = Exhibitors.objects.prefetch_related('exhibitors_for_exh').filter(exhibitors_for_exh__slug=exh_year).only('name', 'slug')

		#self.portfolio = Portfolio.objects.filter(exhibition__slug=exh_year,nominations__in=q)
		#self.portfolio = Portfolio.objects.select_related('exhibition').filter(exhibition__slug=exh_year).prefetch_related('nominations')
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['nomination']
		context['winner'] = winner
		context['portfolio'] = portfolio
		context['exhibitors'] = exhibitors

		return context


""" Exhibitors & Winners detail """
class event_detail(DetailView):
	model = Events

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['event']

		return context

