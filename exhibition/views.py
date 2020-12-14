from os import path
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.generic.list import ListView #, MultipleObjectMixin
from django.views.generic.detail import DetailView
from django.core.files.storage import FileSystemStorage
from django.db.models import Q, Prefetch, Max #, Count
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce
from django import forms

from .models import *
from .forms import ImagesUploadForm, FeedbackForm
from .logic import IsMobile, SendEmail


def success_message(request):
	return HttpResponse('Сообщение отправлено! Спасибо за вашу заявку.')


""" Main page """
@cache_page(60 * 60)
def index(request):
	context = {
		'html_classes': ['home'],
		'organizers': Organizer.objects.all().only('logo','name','description').order_by('sort','name'),
	}
	url_name = request.resolver_match.url_name
	try:
		meta = MetaSEO.objects.get(page=url_name)
	except MetaSEO.DoesNotExist:
		meta = None

	context['meta'] = meta

	return render(request, 'index.html', context)


def contacts(request):
	if request.method == 'GET':
		form = FeedbackForm()
	elif request.method == 'POST':
		# если метод POST, проверим форму и отправим письмо
		form = FeedbackForm(request.POST)
		if form.is_valid() and SendEmail(form.cleaned_data):
			return redirect('/success/')
		else:
			return HttpResponse('Неверный запрос')

	context = {
		'html_classes': ['contacts'],
		'form': form,
	}
	return render(request, 'contacts.html', context)


""" Exhibitons view """
#@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class exhibitions_list(ListView):
	model = Exhibitions

	def get_queryset(self):
		slug = self.kwargs['exh_year']

		if slug == None:
			q = self.model.objects.all()
			# q = super().get_queryset()
		else:
			q = self.model.objects.filter(date_start__year=slug)
		return q

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibitions',]
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


""" Events view """
class events_list(ListView):
	model = Events
	template_name = 'exhibition/participants_list.html'

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
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context


""" Exhibitors view """
class exhibitors_list(ListView):
	model = Exhibitors
	template_name = 'exhibition/participants_list.html'


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
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context


""" Nominations view """
#@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class nominations_list(ListView):
	model = Categories
	template_name = 'exhibition/nominations_list.html'

	def get_queryset(self):
		search_query = self.request.GET.get('q')
		if search_query:
			query_fields_or = (Q(title__icontains=search_query) | Q(description__icontains = search_query))
			posts = self.model.objects.filter(query_fields_or)
		else:
			posts = self.model.objects.all()

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['nominations',]
		context['absolute_url'] = 'category'
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


""" Projects view """
class projects_list(ListView):
	model = Portfolio
	template_name = 'exhibition/projects_list.html'

	def get_queryset(self):
		slug = self.kwargs['slug']
		search_query = self.request.GET.get('q')
		self.category = None

		if search_query:
			query_fields_or = (Q(title__icontains=search_query) | Q(description__icontains = search_query))
			posts = self.model.objects.filter(query_fields_or)
		else:
			posts = self.model.objects.filter(nominations__category__slug=slug)
			if posts:
				self.category = posts.values_list('nominations__category__title', flat=True)[0]

				#print(self.category)
				#print(posts.query)
		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['projects',]
		context['absolute_url'] = 'projects'
		context['page_title'] = self.category

		return context



""" Winners view """
class winners_list(ListView):
	model = Winners
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.exhibition = None
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')

		if search_query:
			query_fields_or = (Q(exhibitor__name__icontains=search_query) | Q(exhibitor__description__icontains = search_query))
			posts = self.model.objects.filter(query_fields_or)
		else:
			if slug == None:
				# posts = Exhibitors.objects.prefetch_related('exhibitors_for_exh')
				# winners = self.model.objects.only('exhibitor__name')
				# posts = Exhibitors.objects.filter(id__in=winners).order_by('name')
				posts = self.model.objects.select_related('exhibitors').values('exhibitor__name', 'exhibitor__slug').distinct().order_by('exhibitor__name') #.annotate(exhibitors_count=Count('exhibitor_id'))
			else:
				# winners = self.model.objects.prefetch_related(Prefetch('exhibitor', queryset=Exhibitors.objects.only('name'))).select_related('exhibition').only('exhibition__date_start').filter(exhibition__date_start__year=slug)
				posts = self.model.objects.select_related('exhibition').filter(exhibition__date_start__year=slug).order_by('exhibitor__name')
				if posts:
					self.exhibition = posts[0].exhibition

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants',]
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context



""" Partners view """
class partners_list(ListView):
	model = Partners
	template_name = 'exhibition/partners_list.html'

	def get_queryset(self):
		slug = self.kwargs['exh_year']
		search_query = self.request.GET.get('q')
		self.exhibition = None
		queryset = super().get_queryset()


		if search_query:
			query_fields_or = (Q(name__icontains=search_query) | Q(description__icontains=search_query))
			posts = queryset.filter(query_fields_or)
		else:
			if slug == None:
				last_year = Exhibitions.objects.values_list('slug', flat=True).first()
				posts = queryset.prefetch_related('partners_for_exh').filter(~Q(partners_for_exh__slug=last_year)).order_by('name')
			else:
				#exhibition_by_year = self.objects.prefetch_related('partners_for_exh').filter(partners_for_exh__slug=slug).order_by('name'),
				exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('partners')[0]
				posts = exhibition_by_year.partners.only('name')
				self.exhibition = exhibition_by_year

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['partners',]
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context



""" Jury view """
class jury_list(ListView):
	model = Jury
	template_name = 'exhibition/persons_list.html'

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

		context['html_classes'] = ['jury',]
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition
		return context



""" Exhibitors & Winners detail """
class exhibitor_detail(DetailView):
	model = Exhibitors
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		slug = self.kwargs['slug']
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant']
		context['winners_list'] = Nominations.objects.prefetch_related('nomination_for_winner').filter(nomination_for_winner__exhibitor__slug=slug).annotate(exh_year=F('nomination_for_winner__exhibition__slug')).values('title', 'slug', 'exh_year').order_by('exh_year')
		context['object_list'] = Portfolio.objects.prefetch_related('images').filter(owner__slug=slug).annotate(exh_year=F('exhibition__slug')).order_by('-exh_year')
		#context['exh_list'] = ', '.join(Exhibitions.objects.filter(exhibitors=self.object).values_list('title', flat=True))
		context['parent_link'] = self.model.__name__.lower

		return context


""" Jury detail """
class jury_detail(DetailView):
	model = Jury
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'jury']
		context['parent_link'] = self.model.__name__.lower

		return context


""" Partners detail """
class partner_detail(DetailView):
	model = Partners
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'partner']
		context['parent_link'] = self.model.__name__.lower
		return context


""" Exhibitions detail """
class exhibition_detail(DetailView):
	model = Exhibitions
	def get_object(self, queryset=None):
		slug = self.kwargs['exh_year']
		try:
			q = self.model.objects.prefetch_related('exhibitors','partners','jury','events','gallery').get(date_start__year=slug)
		except self.model.DoesNotExist:
			q = None
		return q

	def get_context_data(self, **kwargs):
		slug = self.kwargs['exh_year'] # current exhibition year
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibition']
		context['is_mobile'] = IsMobile(self.request)

		nominations_with_winners = self.object.nominations.filter(nomination_for_winner__exhibition_id=self.object.id).annotate(exhibitor_name=F('nomination_for_winner__exhibitor__name'), exhibitor_slug=F('nomination_for_winner__exhibitor__slug')).values('id','exhibitor_name','exhibitor_slug','title', 'slug') #.filter(nomination_for_winner__exhibition_id=self.object.id).values('nomination_for_winner__exhibition_id', 'nomination_for_winner__exhibitor__name', 'title')#.filter(nomination_for_winner__exhibition_id=self.object.id)
		if not nominations_with_winners:
			context['nominations_list'] = self.object.nominations.all
		else:
			context['nominations_list'] = nominations_with_winners
		context['last_exh'] = Exhibitions.objects.values('slug')[:1].first()
		context['events_title'] = Events._meta.verbose_name_plural
		context['gallery_title'] = Gallery._meta.verbose_name_plural

		return context


""" Winner project detail """
class winner_project_detail(DetailView):
	model = Winners
	#slug_url_kwarg = 'name'
	#context_object_name = 'portfolio'
	template_name = 'exhibition/nominations_detail.html'

	def get_object(self, queryset=None):
#	def get_queryset(self):
		nom = self.kwargs['slug']
		exh_year = self.kwargs['exh_year']

		try:
			q = self.model.objects.get(exhibition__slug=exh_year,nomination__slug=nom)
			self.exhibitors = None
			self.nomination = q.nomination
		except self.model.DoesNotExist:
			q = None
			self.exhibitors = Exhibitors.objects.prefetch_related('exhibitors_for_exh').filter(exhibitors_for_exh__slug=exh_year).only('name', 'slug')
			self.nomination = Nominations.objects.only('title', 'description').get(slug=nom)

		return q

	def get_context_data(self, **kwargs):
		exh_year = self.kwargs['exh_year']

		if self.object:
			try:
				if self.object.portfolio:
					portfolio = Portfolio.objects.prefetch_related('images').get(pk=self.object.portfolio.id)
				else:
					portfolio = Portfolio.objects.prefetch_related('images').get(exhibition=self.object.exhibition,nominations=self.object.nomination, owner=self.object.exhibitor)
				#portfolio = Portfolio.objects.prefetch_related('images').get(exhibition__slug=exh_year,nominations=nom, owner=winner.exhibitor.id, pk=winner.portfolio_id)
			except (Portfolio.DoesNotExist, Portfolio.MultipleObjectsReturned):
				portfolio = None

		else:
			portfolio = None

		#self.portfolio = Portfolio.objects.filter(exhibition__slug=exh_year,nominations__in=q)
		#self.portfolio = Portfolio.objects.select_related('exhibition').filter(exhibition__slug=exh_year).prefetch_related('nominations')
		context = super().get_context_data(**kwargs)
		context['is_mobile'] = IsMobile(self.request)
		context['html_classes'] = ['portfolio']
		context['portfolio'] = portfolio
		context['exhibitors'] = self.exhibitors
		context['nomination'] = self.nomination

		context['parent_link'] = '/exhibition/%s/' % exh_year

		return context


""" Project detail """
class project_detail(DetailView):
	model = Portfolio
	#slug_url_kwarg = 'slug'
	context_object_name = 'portfolio'
	#template_name = 'exhibition/portfolio_detail.html'

	def get_object(self, queryset=None):
#	def get_queryset(self):
		owner = self.kwargs['owner']
		project = self.kwargs['project_id']
		if (owner != 'None' and project != 'None'):
			try:
				q = self.model.objects.get(project_id=project, owner__slug=owner)
			except self.model.DoesNotExist:
				q = None
		else:
			q = None

		return q

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_mobile'] = IsMobile(self.request)
		context['html_classes'] = ['portfolio']
		q = self.object.nominations.filter(category__slug__isnull=False).first()
		if q and self.object:
			context['parent_link'] = '/category/%s/' % q.category.slug
		else:
			context['parent_link'] = '/category/'

		return context


""" Event detail """
class event_detail(DetailView):
	model = Events

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['event']

		return context


@login_required
def portfolio_upload(request):
	exhibitor = None
	try:
		exhibitor = Exhibitors.objects.get(user=request.user)
	except Exhibitors.DoesNotExist:
		pass

	if request.method == 'POST':
		form = ImagesUploadForm(request.POST, request.FILES)

		if form.is_valid():
			obj = form.save(commit=False)
			# Deny access for exhibitors to choose their name in list
			if not request.user.is_staff:
				obj.owner = exhibitor

			obj.save(request.FILES.getlist('files'))

			return render(request, 'success_upload.html', { 'portfolio': obj, 'files': request.FILES.getlist('files') })
	else:
		if not request.user.is_staff:
			form = ImagesUploadForm(user=request.user, initial={'owner': exhibitor})
			form.fields['owner'].widget = forms.TextInput()
		else:
			form = ImagesUploadForm(user=request.user)

	return render(request, 'upload.html', { 'form': form, 'exhibitor': exhibitor })

