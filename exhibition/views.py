
import base64
import hashlib
import hmac
import math

from os import path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.template.loader	import render_to_string

from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadhandler import FileUploadHandler
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
#from django.views.generic import View
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.forms import inlineformset_factory
from django.db.models import Q, OuterRef, Subquery, Max, Count, Avg, CharField, Case, When
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce
from django.db.models.signals import pre_save

from allauth.account.views import PasswordResetView
from allauth.account.models import EmailAddress
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.signals import social_account_removed

from sorl.thumbnail import get_thumbnail
from watson import search as watson
from watson.views import SearchMixin

from django import forms
from .models import *

from rating.models import Rating, Reviews
from blog.models import Article

from .forms import PortfolioForm, ImageForm, ImageFormHelper, FeedbackForm, UsersListForm, DeactivateUserForm
from rating.forms import RatingForm
from .logic import SendEmail, SendEmailAsync, SetUserGroup
from .mixins import ExhibitionYearListMixin,  BannersMixin, MetaSeoMixin
from designers.models import Designer, Achievement, Customer
from collections import defaultdict


def success_message(request):
	return HttpResponse('<h1>Сообщение отправлено!</h1><p>Спасибо за обращение</p>')

""" Policy page """
def registration_policy(request):
	return render(request, 'policy.html')


""" Main page """
def index(request):
	context = {
		'html_classes': ['home'],
		'organizers': Organizer.objects.all().only('logo','name','description').order_by('sort','name'),
	}
	return render(request, 'index.html', context)



""" Exhibitors view """
class exhibitors_list(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	model = Exhibitors
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']
		if self.slug:
			return self.model.objects.prefetch_related('exhibitors_for_exh').filter(exhibitors_for_exh__slug=self.slug).order_by('name')
		else:
			return self.model.objects.prefetch_related('exhibitors_for_exh').all().order_by('name')
			#return super().get_queryset()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants',]
		return context


""" Partners view """
class partners_list(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	model = Partners
	template_name = 'exhibition/partners_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']
		if self.slug:
			q = Q(partners_for_exh__slug=self.slug)
		else:
			last_exh = Exhibitions.objects.values_list('slug', flat=True).first()
			q = ~Q(partners_for_exh__slug=last_exh) # except last exhibition

		posts = self.model.objects.prefetch_related('partners_for_exh').filter(q)

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'partners',]

		return context



""" Jury view """
class jury_list(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	model = Jury
	template_name = 'exhibition/persons_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']
		if self.slug:
			posts = self.model.objects.prefetch_related('jury_for_exh').filter(jury_for_exh__slug=self.slug)
		else:
			posts = self.model.objects.all()

		return posts


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'jury',]

		return context



""" Events view """
class events_list(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	model = Events
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']
		if self.slug:
			posts = self.model.objects.filter(exhibition__slug=self.slug).order_by('title')
		else:
			posts = self.model.objects.all().order_by('-exhibition__slug','title')

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['events',]

		return context



""" Exhibitons view """
class exhibitions_list(MetaSeoMixin, BannersMixin, ListView):
	model = Exhibitions

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibitions',]
		context['page_title'] = self.model._meta.verbose_name_plural

		return context



""" Winners view """
class winners_list(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	model = Winners
	template_name = 'exhibition/winners_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']

		query = self.model.objects.select_related('nomination','exhibitor','exhibition', 'portfolio').annotate(
			exh_year=F('exhibition__slug'),
			nomination_title=F('nomination__title'),
			exhibitor_name=F('exhibitor__name'),
			exhibitor_slug=F('exhibitor__slug'),
			project_id=F('portfolio__project_id'),
		).values('exh_year', 'nomination_title', 'exhibitor_name', 'exhibitor_slug', 'project_id').order_by('exhibitor_name', '-exh_year')

		if self.slug:
			posts = query.filter(exhibition__slug=self.slug)
		else:
			posts = query.all()

		return posts


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants','winners']

		return context



""" Categories (groupped Nominations) view """
class category_list(MetaSeoMixin, BannersMixin, ListView):
	model = Categories
	template_name = 'exhibition/category_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['nominations',]
		context['absolute_url'] = 'category'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['cache_timeout'] = 2592000
		return context



""" Projects view """
class projects_list(MetaSeoMixin, BannersMixin, ListView):
	model = Categories
	template_name = 'exhibition/projects_list.html'
	PAGE_SIZE = getattr(settings, 'PORTFOLIO_COUNT_PER_PAGE', 20) # Количество выводимых записей на странице

	# использовано для миксина MetaSeoMixin, где проверяется self.object
	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.slug = kwargs['slug']
		if self.slug:
			self.object = self.model.objects.get(slug=self.slug)


	def get_queryset(self):

		# self.page - текущая страница для получения диапазона выборки записей,  (см. функцию get ниже )
		self.page = int(self.page) if self.page else 1

		start_page = (self.page-1)*self.PAGE_SIZE # начало диапазона
		end_page = self.page*self.PAGE_SIZE # конец диапазона

		query = Q(nominations__category__slug=self.slug)

		# Если выбраны опции фильтра, то найдем все номинации в текущей категории "self.slug"
		if self.filters_group and self.filters_group[0] != '0':
			query.add(Q(attributes__in=self.filters_group), Q.AND)

		subqry = Subquery(Image.objects.filter(portfolio=OuterRef('pk')).values('file')[:1]) # Подзапрос для получения первого фото в портфолио
		subqry2 = Subquery(Winners.objects.filter(
			portfolio_id=OuterRef('pk'),
			nomination__category__slug=self.slug
		).values('exhibition__slug')[:1]) # Подзапрос для получения статуса победителя

		posts = Portfolio.objects.filter(Q(exhibition__isnull=False) & Q(project_id__isnull=False) & query
		).distinct().prefetch_related('rated_portfolio').annotate(
			last_exh_year=F('exhibition__slug'),
			#cat_title=F('nominations__category__title'),
			average=Avg('rated_portfolio__star'),
			win_year=subqry2,
			project_cover=Case(
				When(Q(cover__exact='') | Q(cover__isnull=True), then=subqry),
				default='cover',
				output_field=CharField()
			)
		).values('id','title','last_exh_year','win_year','average','owner__name','owner__slug','project_id','project_cover'
		).order_by('-last_exh_year','-win_year', '-average')[start_page:end_page] # +1 сделано для выявления наличия следующей страницы

		self.is_next_page = False if len(posts) < self.PAGE_SIZE else True
		return posts #[:self.PAGE_SIZE]


	def get_context_data(self, **kwargs):
		#attributes = self.object_list.distinct().filter(attributes__group__isnull=False).annotate(attribute_id=F('attributes'), group=F('attributes__group'), name=F('attributes__name'))#.values('group', 'name', 'attribute_id').order_by('group', 'name')
		# Отсортируем и сгруппируем словарь аттрибутов по ключу group
		# keyfunc = lambda x:x['group']
		# attributes = [list(data) for _, data in groupby(sorted(data, key=keyfunc), key=keyfunc)]

		# найдем аттрибуты для фильтра в портфолио, если они есть в текущей категории
		attributes = PortfolioAttributes.objects.prefetch_related('attributes_for_portfolio').filter(
			attributes_for_portfolio__nominations__category__slug=self.slug,
			group__isnull=False,
		).distinct()

		# Формирование групп аттрибутов фильтра
		attributes_dict = attributes.values('id','name','group')
		filter_attributes = defaultdict(list)
		for i,item in enumerate(attributes_dict):
			attributes_dict[i].update({'group_name' : attributes[i].get_group_display()}) # {queryset_row}.get_group_display() - get choice field name
			filter_attributes[item['group']].append(attributes_dict[i])

		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['projects',]
		context['parent_link'] = '/category'
		context['absolute_url'] = self.slug
		context['category_title'] = self.object
		context['next_page'] = self.is_next_page
		context['filter_attributes'] = list(filter_attributes.values())
		context['cache_timeout'] = 86400 # one day
		return context


	def get(self, request, *args, **kwargs):
		self.page = self.request.GET.get('page', None) # Параметр GET запроса ?page текущей страницы
		self.filters_group = self.request.GET.getlist("filter-group", None) # Выбранные опции checkbox в GET запросе (?nominations=[])

		if self.filters_group or self.page:
			DEFAULT_QUALITY = getattr(settings, 'THUMBNAIL_QUALITY', 85)
			ADMIN_THUMBNAIL_SIZE = getattr(settings, 'ADMIN_THUMBNAIL_SIZE', [100, 100])
			ADMIN_DEFAULT_SIZE = '%sx%s' % (ADMIN_THUMBNAIL_SIZE[0], ADMIN_THUMBNAIL_SIZE[1])
			ADMIN_DEFAULT_QUALITY = getattr(settings, 'ADMIN_THUMBNAIL_QUALITY', 75)

			queryset = self.get_queryset()

			for i,q in enumerate(queryset):
				if q['project_cover']:
					thumb_mini = get_thumbnail(q['project_cover'], ADMIN_DEFAULT_SIZE, crop='center', quality=ADMIN_DEFAULT_QUALITY)
					thumb_320 = get_thumbnail(q['project_cover'], '320', quality=DEFAULT_QUALITY)
					thumb_576 = get_thumbnail(q['project_cover'], '576', quality=DEFAULT_QUALITY)
					queryset[i].update({
						'thumb_mini' :str(thumb_mini),
						'thumb_xs' :str(thumb_320),
						'thumb_sm'	:str(thumb_576),
						'thumb_xs_w':320,
						'thumb_sm_w':576
					})

			json_data = {
				'current_page': int(self.page or 1),
				'next_page': self.is_next_page,
				'projects_list': list(queryset),
				'projects_url': '/projects/',
				'media_url': settings.MEDIA_URL,
			}

			return JsonResponse(json_data, safe=False)
		else:
			# выполняется при загрузке первой страницы
			return super().get(request, **kwargs)


""" Projects by year view """
class projects_list_by_year(ListView):
	model = Portfolio
	template_name = 'exhibition/projects_by_year.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']

		subqry = Subquery(Image.objects.filter(portfolio=OuterRef('pk')).values('file')[:1]) # Подзапрос для получения первого фото в портфолио

		posts = self.model.objects.filter(Q(exhibition__slug=self.slug) & Q(project_id__isnull=False)
		).distinct().prefetch_related('rated_portfolio').annotate(
			project_cover=Case(
				When(Q(cover__exact='') | Q(cover__isnull=True), then=subqry),
				default='cover',
				output_field=CharField()
			)
		).values('id','title','owner__name','owner__slug','project_id','project_cover').order_by('owner__slug')

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['year'] = self.slug
		return context


""" Exhibitors detail """
class exhibitor_detail(MetaSeoMixin, DetailView):
	model = Exhibitors
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		slug = self.kwargs['slug']

		portfolio = Portfolio.objects.filter(owner__slug=slug, exhibition__isnull=False).annotate(
			exh_year=F('exhibition__slug'),
			win_year=Subquery(Winners.objects.filter(portfolio_id=OuterRef('pk')).values('exhibition__slug')[:1]),
			project_cover=Case(
				When(Q(cover__exact='') | Q(cover__isnull=True), then=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])),
				default='cover',
				output_field=CharField()
			)
		).order_by('-exh_year')

		awards = Nominations.objects.prefetch_related('nomination_for_winner').filter(
			nomination_for_winner__exhibitor__slug=slug).annotate(
			exh_year=F('nomination_for_winner__exhibition__slug')
		).values('title', 'slug', 'exh_year').order_by('-exh_year')

		#articles = Article.objects.filter()
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant']
		context['object_list'] = portfolio
		context['awards_list'] = awards
		context['article_list'] = Article.objects.filter(owner=self.object.user).only('title').order_by('title') if self.object.user else None
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 86400
		return context


""" Jury detail """
class jury_detail(MetaSeoMixin, BannersMixin, DetailView):
	model = Jury
	template_name = 'exhibition/jury_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'jury']
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 86400
		return context


""" Partners detail """
class partner_detail(MetaSeoMixin, BannersMixin, DetailView):
	model = Partners
	template_name = 'exhibition/partner_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'partner']
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 86400
		return context


""" Event detail """
class event_detail(MetaSeoMixin, BannersMixin, DetailView):
	model = Events
	template_name = 'exhibition/event_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['event']
		context['model_name'] = self.model.__name__.lower()
		context['exh_year'] = self.kwargs['exh_year']
		return context


""" Exhibitions detail """
class exhibition_detail(MetaSeoMixin, BannersMixin, DetailView):
	model = Exhibitions

	def get_object(self, queryset=None):
		slug = self.kwargs['exh_year']
		self.kwargs['id'] = 1
		try:
			q = self.model.objects.prefetch_related('events','gallery').get(slug=slug)
		except self.model.DoesNotExist:
			q = None
		return q

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		win_nominations = self.object.nominations.filter(nomination_for_winner__exhibition_id=self.object.id).annotate(
			exhibitor_name=F('nomination_for_winner__exhibitor__name'),
			exhibitor_slug=F('nomination_for_winner__exhibitor__slug'),
			#cover=Coalesce(Subquery(Image.objects.filter(portfolio_id=OuterRef('portfolio_for_winner')).values('file')[:1]), None)
		).values('id', 'exhibitor_name', 'exhibitor_slug', 'title', 'slug')

		# Добавляем слайды в баннер (основной + первые фото победных проектов)
		banner_slider = []
		if self.object.banner and self.object.banner.width > 0 :
			banner_slider.append(self.object.banner)
			context['banner_height'] = f"{self.object.banner.height / self.object.banner.width * 100}%"

		for nom in win_nominations:
			cover = Image.objects.filter(
				portfolio__exhibition=self.object.id,
				portfolio__nominations=nom['id'],
				portfolio__owner__slug=nom['exhibitor_slug'],
			).values('file')[:1].first()
			if cover:
				banner_slider.append(cover['file'])

		context['html_classes'] = ['exhibition']
		context['banner_slider'] = banner_slider
		context['win_nominations'] = win_nominations
		context['events_title'] = Events._meta.verbose_name_plural
		context['gallery_title'] = Gallery._meta.verbose_name_plural
		context['last_exh'] = self.model.objects.only('slug')[:1].first().slug
		context['exh_year'] = self.kwargs['exh_year']
		context['today'] = now().date()
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 2592000
		return context


""" Winner project detail """
class winner_project_detail(MetaSeoMixin, BannersMixin, DetailView):
	model = Winners
	template_name = 'exhibition/nominations_detail.html'
	#slug_url_kwarg = 'name'
	#context_object_name = 'portfolio'

	def get_object(self, queryset=None):
		self.nom_slug = self.kwargs['slug']
		self.exh_year = self.kwargs['exh_year']

		qs = self.model.objects.filter(exhibition__slug=self.exh_year,nomination__slug=self.nom_slug)
		if qs:
			self.exhibitors = None
			self.nomination = qs[0].nomination
			return qs[0]
		else:
			# найдем участников, заявленных на выставке
			self.exhibitors = Exhibitors.objects.prefetch_related('exhibitors_for_exh').filter(exhibitors_for_exh__slug=self.exh_year).only('name', 'slug')
			# получим номинацию
			self.nomination = Nominations.objects.get(slug=self.nom_slug).only('title', 'description')
			return None


	def get_context_data(self, **kwargs):
		#self.portfolio = Portfolio.objects.filter(exhibition__slug=exh_year,nominations__in=q)
		#self.portfolio = Portfolio.objects.select_related('exhibition').filter(exhibition__slug=exh_year).prefetch_related('nominations')
		context = super().get_context_data(**kwargs)
		portfolio = None
		try:
			#portfolio = Portfolio.objects.prefetch_related('images').get(exhibition__slug=self.exh_year,nominations=self.nom_slug, owner=winner.exhibitor.id, pk=winner.portfolio_id)
			if self.object and self.object.portfolio:
				portfolio = Portfolio.objects.get(pk=self.object.portfolio.id)
			else:
				portfolio = Portfolio.objects.get(
					exhibition=self.object.exhibition,
					nominations=self.object.nomination,
					owner=self.object.exhibitor
				)
		except (Portfolio.DoesNotExist, Portfolio.MultipleObjectsReturned):
			pass

		context['html_classes'] = ['project']
		context['portfolio'] = portfolio
		context['exhibitors'] = self.exhibitors
		context['nomination'] = self.nomination
		context['parent_link'] = '/exhibition/%s/' % self.exh_year
		context['exh_year'] = self.exh_year

		rate = 0
		if portfolio:
			score = Rating.calculate(portfolio)
			rate = score.average

		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(portfolio=portfolio, user=self.request.user).values_list('star',flat=True).first()
		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['round_rate'] = math.ceil(rate)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])
		context['cache_timeout'] = 86400

		return context


""" Project detail """
class project_detail(MetaSeoMixin, DetailView):
	model = Portfolio
	context_object_name = 'portfolio'
	#slug_url_kwarg = 'slug'
	#template_name = 'exhibition/portfolio_detail.html'

	def get_object(self, queryset=None):
#	def get_queryset(self):
		self.owner = self.kwargs['owner']
		self.project = self.kwargs['project_id']

		# Найдем портфолио и победу в номинациях если есть
		q = None
		if self.owner and self.project:
			try:
				q = self.model.objects.get(project_id=self.project, owner__slug=self.owner)
				#q = self.model.objects.prefetch_related('portfolio_for_winner').annotate(win_year=Coalesce('portfolio_for_winner__exhibition__slug',None)).get(project_id=self.project, owner__slug=self.owner)
			except self.model.DoesNotExist:
				pass

		return q


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['project']
		context['victories'] = Winners.objects.filter(portfolio=self.object.id, exhibitor__slug=self.owner)
		context['owner'] = self.owner
		context['project_id'] = self.project

		if self.request.META.get('HTTP_REFERER') == None:
			q = self.object.nominations.filter(category__slug__isnull=False).first()
			if q and self.object:
				context['parent_link'] = '/category/%s/' % q.category.slug
			else:
				context['parent_link'] = '/category/'

		score = Rating.calculate(self.object)
		rate = score.average
		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(portfolio=self.object, user=self.request.user).values_list('star',flat=True).first()
		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['round_rate'] = math.ceil(rate)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])
		context['cache_timeout'] = 86400

		return context



""" Отправка сообщения с формы обратной связи """
def contacts(request):
	if request.method == 'GET':
		form = FeedbackForm()
	elif request.method == 'POST':
		# если метод POST, проверим форму и отправим письмо
		form = FeedbackForm(request.POST)
		if form.is_valid():
			template = render_to_string('contacts/confirm_email.html', {
				'name':form.cleaned_data['name'],
				'email':form.cleaned_data['from_email'],
				'message':form.cleaned_data['message'],
			})

			if SendEmail('Получено новое сообщение с сайта sd43.ru!', template):
				return redirect('/success/')

	context = {
		'html_classes': ['contacts'],
		'form': form,
	}
	return render(request, 'contacts.html', context)



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



class ProgressBarUploadHandler(FileUploadHandler):
	def receive_data_chunk(self, raw_data, start):
		print(start)
		return raw_data

	def file_complete(self, file_size):
		print(file_size)





""" Выгрузка нового портфолио """
@csrf_exempt
@login_required
def portfolio_upload(request, **kwargs):
	request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
	#upload_file_view(request)
	pk = kwargs.pop('pk',None)
	if pk:
		portfolio = Portfolio.objects.get(id=pk)
	else:
		portfolio = None #Portfolio()

	if not request.user.is_staff:
		owner = Exhibitors.objects.get(user=request.user)
	else:
		owner = 'staff'
	#owner = Exhibitors.objects.get(user=4)

	form = PortfolioForm(owner=owner, instance=portfolio)
	InlineFormSet = inlineformset_factory(Portfolio, Image, form=ImageForm, extra=0, can_delete=True)
	formset = InlineFormSet(instance=portfolio)
	formset_helper = ImageFormHelper()

	if request.method == 'POST':

		form = PortfolioForm(request.POST, request.FILES, request=request, instance=portfolio)

		if form.is_valid():
			formset = InlineFormSet(request.POST, request.FILES, instance=portfolio)
			portfolio = form.save(commit=False)

			if formset.is_valid():
				images = request.FILES.getlist('files')
				if not request.user.is_staff:
					portfolio.status = False
				portfolio.save(images=images)
				form.save_m2m()
				formset.save()

				context = {
					'user': '%s %s' % (request.user.first_name, request.user.last_name),
					'portfolio': portfolio,
					'files': images,
					'changed_fields': [],
					'new' : True
				}
				if pk:
					context['changed_fields'] = form.changed_data
					context['new'] = False

				#template = render_to_string('account/portfolio_upload_confirm.html', context)
				#SendEmailAsync('%s портфолио на сайте sd43.ru!' % ('Внесены изменения в' if pk else 'Добавлено новое'), template)

				if not pk:
					# MetaSEO.objects.create(
					# 	model=form.meta_model,
					# 	post_id=portfolio.id,
					# 	title=form.cleaned_data['meta_title'],
					# 	description=form.cleaned_data['meta_description'],
					# 	keywords=form.cleaned_data['meta_keywords'],
					# )
					return render(request, 'success_upload.html', { 'portfolio': portfolio, 'files': images })

				return redirect('/account')
			else:
				print(formset.errors)

	return render(request, 'upload.html', { 'form': form, "formset": formset, 'portfolio_id': pk, 'formset_helper': formset_helper })


# @receiver(pre_save, sender=Portfolio)
# def on_change(sender, instance, **kwargs):
# 	if instance.pk:
# 		pass



""" Личный кабинет зарегистрированных пользователей """
@login_required
def account(request):
	try:
		#exhibitor = Exhibitors.objects.get(user=4)
		exhibitor = Exhibitors.objects.get(user=request.user)
	except Exhibitors.DoesNotExist:
		exhibitor = None

	designer = None
	exh_portfolio = None
	add_portfolio = None
	victories = None
	achievements = None
	customers = None
	if exhibitor:
		exh_portfolio = Portfolio.objects.filter(owner=exhibitor, exhibition__isnull=False).annotate(
			exh_year=F('exhibition__slug'),
			project_cover=Case(
				When(Q(cover__exact='') | Q(cover__isnull=True), then=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])),
				default='cover',
				output_field=CharField()
			)
		).order_by('-exh_year')

		try:
			#designer = Designer.objects.get(owner__user=4)
			designer = Designer.objects.get(owner=exhibitor)

			add_portfolio = designer.add_portfolio.all().annotate(
				project_cover=Case(
					When(Q(cover__exact='') | Q(cover__isnull=True), then=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])),
					default='cover',
					output_field=CharField()
				)
			).order_by('title')

			victories = Nominations.objects.prefetch_related('nomination_for_winner').filter(
				nomination_for_winner__exhibitor=exhibitor).annotate(
				exh_year=F('nomination_for_winner__exhibition__slug')
			).values('title', 'slug', 'exh_year').order_by('-exh_year')

			achievements = designer.achievements.all().order_by('group')
			#customers = designer.customers.all()

		except Designer.DoesNotExist:
			pass


	articles = Article.objects.filter(owner=request.user).only('title').order_by('title')
	rates = Rating.objects.filter(user=request.user)
	reviews = Reviews.objects.filter(user=request.user)

	return render(request, 'account/base.html', {
		'exhibitor': exhibitor,
		'designer': designer,
		'exh_portfolio': exh_portfolio,
		'add_portfolio': add_portfolio,
		'achievements': achievements,
		'victories': victories,
		'articles': articles,
		'rates': rates,
		'reviews': reviews
	})



""" Sending reset password emails to exhibitors """
@staff_member_required
def send_reset_password_email(request):
	if request.method == 'GET':
		form = UsersListForm()
	else:
		form = UsersListForm(request.POST)
		if form.is_valid():
			users_email = request.POST.getlist('users') or None
			for email in users_email:
				request.POST = {
					'email': email,
					#'csrfmiddlewaretoken': get_token(request) #HttpRequest()
				}
				# allauth reset password email send
				PasswordResetView.as_view()(request)

			#return render(request,'account/email/exhibitors/password_reset_key_message.html',self.data)
			return HttpResponse('<h1>Письма успешно отправлены!</h1>')
		else:
			return HttpResponse('<h1>Что-то пошло не так...</h1>')

	return render(request, 'account/send_password_reset_email.html', { 'form': form })




""" Удаление аккаунта пользователя """
@login_required
#@method_decorator(csrf_exempt, name='dispatch')
def deactivate_user(request):

	if request.method == 'GET':
		form = DeactivateUserForm()
	else:
		form = DeactivateUserForm(request.POST)
		if form.is_valid():
			try:
				user_allauth = EmailAddress.objects.get(user__username=request.user.username)
				user_allauth.delete()
			except EmailAddress.DoesNotExist:
				pass

			try:
				social_account = SocialAccount.objects.get(user__username=request.user.username)
				social_account.delete()
				social_account_removed.send(
					sender=SocialAccount,
					request=self.request,
					socialaccount=social_account
				)
			except SocialAccount.DoesNotExist:
				pass

			# User Deactivation
			request.user.is_active = False
			request.user.save()
			# Log user out.
			# logout(request)
			# Give them a success message
			# messages.success(request, 'Аккаунт удален!')
			# return redirect(reverse('index'))
			return HttpResponseRedirect(reverse_lazy('account_logout'))

	return render(request, 'account/deactivation.html', {'form': form})



""" Подслушаем событие регистрации нового пользователя и отправим письмо администратору """
# dispatch_uid: some.unique.string.id.for.allauth.user_signed_up
@receiver(user_signed_up, dispatch_uid="new_user")
def user_signed_up_(request, user, **kwargs):
	user = SetUserGroup(request, user)
	template = render_to_string('account/admin_email_confirm.html', {
		'name': '%s %s (%s)' % (user.first_name, user.last_name, user.username),
		'email': user.email,
		'group': list(user.groups.all().values_list('name', flat=True)),
	})
	SendEmailAsync('Регистрация нового пользователя на сайте sd43.ru!',template)


