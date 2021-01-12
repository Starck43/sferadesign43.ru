from os import path
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader	import render_to_string
from django.dispatch import receiver
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from django.views.generic.list import ListView #, MultipleObjectMixin
from django.views.generic.detail import DetailView
from django.core.files.storage import FileSystemStorage
from django.db.models import Q, Prefetch, Max, Count
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce

from sorl.thumbnail import get_thumbnail
from allauth.account.signals import user_signed_up
from allauth.account.views import PasswordResetView
from watson import search as watson
from watson.views import SearchMixin

from django import forms
from .models import *

from rating.models import Rating, Reviews
from .forms import ImagesUploadForm, FeedbackForm, UsersListForm
from rating.forms import RatingForm
from .logic import SendEmail, SetUserGroup



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
		template = render_to_string('contacts/confirm_email.html', {
			'name':form.cleaned_data['name'],
			'email':form.cleaned_data['from_email'],
			'message':form.cleaned_data['message'],
		})
		if form.is_valid() and SendEmail(template):
			return redirect('/success/')
		else:
			return HttpResponse('Неверный запрос')

	context = {
		'html_classes': ['contacts'],
		'form': form,
	}
	return render(request, 'contacts.html', context)


""" Exhibitors view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class exhibitors_list(ListView):
	model = Exhibitors
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		slug = self.kwargs['exh_year']
		self.exhibition = None

		if slug:
			exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('exhibitors')[0]
			posts = exhibition_by_year.exhibitors.only('name')
			self.exhibition = exhibition_by_year
			return posts

		return super().get_queryset()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants',]
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context


""" Partners view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class partners_list(ListView):
	model = Partners
	template_name = 'exhibition/partners_list.html'

	def get_queryset(self):
		slug = self.kwargs['exh_year']

		if slug == None:
			last_year = Exhibitions.objects.values_list('slug', flat=True).first()
			posts = Partners.objects.prefetch_related('partners_for_exh').filter(~Q(partners_for_exh__slug=last_year)).order_by('name')
			self.exhibition = None
		else:
			#exhibition_by_year = self.objects.prefetch_related('partners_for_exh').filter(partners_for_exh__slug=slug).order_by('name'),
			exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('partners')[0]
			posts = exhibition_by_year.partners.only('name')
			self.exhibition = exhibition_by_year

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'partners',]
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition

		return context



""" Jury view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class jury_list(ListView):
	model = Jury
	template_name = 'exhibition/persons_list.html'

	def get_queryset(self):
		slug = self.kwargs['exh_year']
		self.exhibition = None

		if slug:
			exhibition_by_year = Exhibitions.objects.filter(date_start__year=slug).prefetch_related('jury')[0]
			posts = exhibition_by_year.jury.only('name')
			self.exhibition = exhibition_by_year
			return posts

		return super().get_queryset()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context['html_classes'] = ['participants', 'jury',]
		context['absolute_url'] = self.model.__name__.lower
		context['page_title'] = self.model._meta.verbose_name_plural
		context['exhibition'] = self.exhibition
		return context


""" Exhibitons view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class exhibitions_list(ListView):
	model = Exhibitions

	# def get_queryset(self):
	# 	slug = self.kwargs['exh_year']

	# 	if slug == None:
	# 		posts = self.model.objects.all()
	# 	else:
	# 		posts = self.model.objects.filter(date_start__year=slug)
	# 	return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibitions',]
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


""" Nominations view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class nominations_list(ListView):
	model = Categories
	template_name = 'exhibition/nominations_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['nominations',]
		context['absolute_url'] = 'category'
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


""" Events view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class events_list(ListView):
	model = Events
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		slug = self.kwargs['exh_year']

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


""" Projects view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class projects_list(ListView):
	model = Portfolio
	template_name = 'exhibition/projects_list.html'

	def get_queryset(self):
		slug = self.kwargs['slug']
		self.category = None

		posts = self.model.objects.filter(nominations__category__slug=slug, project_id__isnull=False).distinct()
		if posts:
			self.category = posts.values_list('nominations__category__title', flat=True)[0]

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['projects',]
		context['absolute_url'] = 'projects'
		context['page_title'] = self.category

		return context



""" Winners view """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class winners_list(ListView):
	model = Winners
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.exhibition = None
		slug = self.kwargs['exh_year']

		if slug == None:
			posts = self.model.objects.select_related('exhibitors').values('exhibitor__name', 'exhibitor__slug').distinct().order_by('exhibitor__name') #.annotate(exhibitors_count=Count('exhibitor_id'))
		else:
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



""" Exhibitors & Winners detail """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
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
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class jury_detail(DetailView):
	model = Jury
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'jury']
		context['parent_link'] = self.model.__name__.lower

		return context


""" Partners detail """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class partner_detail(DetailView):
	model = Partners
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'partner']
		context['parent_link'] = self.model.__name__.lower
		return context


""" Event detail """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class event_detail(DetailView):
	model = Events
	template_name = 'exhibition/event_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['event']
		context['parent_link'] = self.model.__name__.lower
		return context


""" Exhibitions detail """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
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

		nominations_with_winners = self.object.nominations.filter(nomination_for_winner__exhibition_id=self.object.id).annotate(exhibitor_name=F('nomination_for_winner__exhibitor__name'), exhibitor_slug=F('nomination_for_winner__exhibitor__slug')).values('id', 'exhibitor_name','exhibitor_slug','title', 'slug') #.filter(nomination_for_winner__exhibition_id=self.object.id).values('nomination_for_winner__exhibition_id', 'nomination_for_winner__exhibitor__name', 'title')#.filter(nomination_for_winner__exhibition_id=self.object.id)
		if nominations_with_winners:
			context['nominations_list'] = nominations_with_winners
		else:
			context['nominations_list'] = self.object.nominations.all

		context['last_exh'] = Exhibitions.objects.values('slug')[:1].first()
		banner_slider = []
		if self.object.banner and self.object.banner.width!=0 :
			banner_slider.append(self.object.banner)
			context['banner_height'] = f"{self.object.banner.height / self.object.banner.width * 100}%"

		for winner in nominations_with_winners:
			query_and = (Q(exhibition=self.object) & Q(nominations=winner['id']) & Q(owner__slug=winner['exhibitor_slug']))
			first_image = Portfolio.objects.prefetch_related('images').filter(query_and, images__file__isnull=False).values('images__file').first()
			if first_image:
				banner_slider.append(first_image['images__file'])
				#print(first_image)

		context['banner_slider'] = banner_slider
		context['events_title'] = Events._meta.verbose_name_plural
		context['gallery_title'] = Gallery._meta.verbose_name_plural

		return context


""" Winner project detail """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
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
		context['html_classes'] = ['project']
		context['portfolio'] = portfolio
		context['exhibitors'] = self.exhibitors
		context['nomination'] = self.nomination
		context['parent_link'] = '/exhibition/%s/' % exh_year

		if portfolio:
			score = Rating.calculate(portfolio)
			rate = score.average
		else:
			rate = 0

		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(portfolio=portfolio, user=self.request.user).values_list('star',flat=True).first()
		context['average_rate'] = round(rate, 2)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])

		return context


""" Project detail """
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
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
		context['html_classes'] = ['project']
		context['parent_link'] = self.request.META.get('HTTP_REFERER')
		if context['parent_link'] == None:
			q = self.object.nominations.filter(category__slug__isnull=False).first()
			if q and self.object:
				context['parent_link'] = '/category/%s/' % q.category.slug
			else:
				context['parent_link'] = '/category/'
		score = Rating.calculate(self.object)
		rate = score.average
		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(portfolio=self.object, user=self.request.user).values_list('star',flat=True).first()
		context['average_rate'] = round(rate, 2)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])

		return context


""" Watson model's search """
class search_site(SearchMixin, ListView):
	template_name = 'search_results.html'
	paginate_by = 15

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['search-result']
		# for result in self.object_list:
		# 	print(result)

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


@staff_member_required
def send_reset_password_email(request):

	if request.method == 'GET':
		form = UsersListForm()
	else:
		form = UsersListForm(request.POST)
		if form.is_valid():
			users_email = request.POST.getlist('users', None)
			for email in users_email:
				request.POST = {
					'email': email,
					#'csrfmiddlewaretoken': get_token(request) #HttpRequest()
				}
				# allauth email send
				PasswordResetView.as_view()(request)

			return HttpResponse('<h1>Письма успешно отправлены!</h1>')
		else:
			return HttpResponse('<h1>Что-то пошло не так...</h1>')

	return render(request, 'account/send_password_reset_email.html', { 'form': form })


""" Подслушаем событие подтвреждения регистрации пользователя и отправим письмо администратору"""
# dispatch_uid: some.unique.string.id.for.allauth.user_signed_up
@receiver(user_signed_up, dispatch_uid="2020")
def user_signed_up_(request, user, **kwargs):
	user = SetUserGroup(request, user)
	template = render_to_string('account/admin_email_confirm.html', {
		'name': '%s %s (%s)' % (user.first_name, user.last_name, user.username),
		'email': user.email,
		'group': list(user.groups.all().values_list('name', flat=True)),
	})
	SendEmail(template)


def account(request):
	# try:
	# 	profile = Exhibitors.objects.get(user=request.user)
	# except Exhibitors.DoesNotExist:
	# 	profile = None

	profile = None
	rates = Rating.objects.filter(user=request.user)
	reviews = Reviews.objects.filter(user=request.user)

	return render(request, 'account/base.html', { 'profile': profile, 'rates': rates, 'reviews': reviews })

