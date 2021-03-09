
import base64
import hashlib
import hmac

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
#from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView #, MultipleObjectMixin
from django.views.generic.detail import DetailView
from django.db.models import Q, OuterRef, Subquery, Prefetch, Max, Count, Avg
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from allauth.account.views import PasswordResetView
from allauth.account.models import EmailAddress
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.signals import social_account_removed

from sorl.thumbnail import get_thumbnail
from watson import search as watson
from watson.views import SearchMixin
#from django.views.generic import View
from django.views import View

from django import forms
from .models import *

from rating.models import Rating, Reviews
from .forms import ImagesUploadForm, FeedbackForm, UsersListForm, DeactivateUserForm
from rating.forms import RatingForm
from .logic import SendEmail, SetUserGroup

#from itertools import groupby
from collections import defaultdict

def success_message(request):
	return HttpResponse('<h1>Сообщение отправлено!</h1><p>Спасибо за обращение</p>')


""" Main page """
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


""" Main page """
def registration_policy(request):
	return render(request, 'policy.html')


""" Send email on Contacts page """
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

			if SendEmail('Отправлено новое сообщение с сайта sd43.ru!', template):
				return redirect('/success/')

	context = {
		'html_classes': ['contacts'],
		'form': form,
	}
	return render(request, 'contacts.html', context)


""" Exhibitors view """
class exhibitors_list(ListView):
	model = Exhibitors
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']

		if self.slug:
			return self.model.objects.prefetch_related('exhibitors_for_exh').filter(exhibitors_for_exh__slug=self.slug)
		else:
			return self.model.objects.prefetch_related('exhibitors_for_exh').all()
			#return super().get_queryset()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants',]
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower
		context['exh_year'] = self.slug

		return context


""" Partners view """
class partners_list(ListView):
	model = Partners
	template_name = 'exhibition/partners_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']

		if self.slug:
			q = Q(partners_for_exh__slug=self.slug)
		else:
			last_year = Exhibitions.objects.values_list('slug', flat=True).first()
			# Only not in last year
			q = ~Q(partners_for_exh__slug=last_year)

		posts = self.model.objects.prefetch_related('partners_for_exh').filter(q)

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'partners',]
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower
		context['exh_year'] = self.slug

		return context



""" Jury view """
class jury_list(ListView):
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
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower
		context['exh_year'] = self.slug

		return context


""" Exhibitons view """
class exhibitions_list(ListView):
	model = Exhibitions

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibitions',]
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


""" Nominations view """
class nominations_list(ListView):
	model = Categories
	template_name = 'exhibition/nominations_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['nominations',]
		context['absolute_url'] = 'category'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['cache_timeout'] = 2592000

		return context


""" Events view """
class events_list(ListView):
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
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower
		context['exh_year'] = self.slug

		return context


""" Projects view """
class projects_list(ListView):
	model = Portfolio
	template_name = 'exhibition/projects_list.html'
	PAGE_SIZE = getattr(settings, 'PORTFOLIO_COUNT_PER_PAGE', 20) # Количество выводимых записей на странице

	def get_queryset(self):
		self.slug = self.kwargs['slug']

		# self.page - текущая страница для получения диапазона выборки записей,  (см. функцию get ниже )
		self.page = int(self.page) if self.page else 1

		start_page = (self.page-1)*self.PAGE_SIZE # начало диапазона
		end_page = self.page*self.PAGE_SIZE # конец диапазона

		query = Q(nominations__category__slug=self.slug)
		#nominations_list = Nominations.objects.filter(category__slug=self.slug).values_list('id',flat=True)
		#nominations_query = Q(nominations__in=list(nominations_list))

		# Если выбраны опции фильтра, то найдем все номинации в текущей категории "self.slug"
		if self.filters_group and self.filters_group[0] != '0':
			query.add(Q(attributes__in=self.filters_group), Q.AND)

		subqry = Subquery(Image.objects.filter(portfolio=OuterRef('pk')).values('file')[:1]) # Подзапрос для получения первого фото в портфолио
		subqry2 = Subquery(Winners.objects.filter(
			portfolio_id=OuterRef('pk'),
			nomination__category__slug=self.slug
		).values('exhibition__slug')[:1]) # Подзапрос для получения статуса победителя

		posts = self.model.objects.filter(
			query &
			Q(project_id__isnull=False)
		).distinct().prefetch_related('rated_portfolio').annotate(
			last_exh_year=F('exhibition__slug'),
			cat_title=F('nominations__category__title'),
			average=Avg('rated_portfolio__star'),
			win_year=subqry2,
			cover=subqry
		).order_by('-last_exh_year','-win_year', '-average')[start_page:end_page+1] # +1 сделано для выявления наличия следующей страницы

		self.is_next_page = True if posts.count() > self.PAGE_SIZE else False
		return posts[:self.PAGE_SIZE]


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
		context['absolute_url'] = self.slug
		context['category_title'] = self.object_list.first().cat_title if self.object_list else None
		context['next_page'] = self.is_next_page
		context['filter_attributes'] = list(filter_attributes.values())
		context['cache_timeout'] = 86400 # one day

		#context['nominations'] = self.nominations
		return context

	def get(self, request, *args, **kwargs):
		self.page = self.request.GET.get('page', None) # Параметр GET запроса ?page текущей страницы
		self.filters_group = self.request.GET.getlist("filter-group", None) # Выбранные опции checkbox в GET запросе (?nominations=[])
		if self.filters_group or self.page:
			queryset = self.get_queryset().values('id','title','win_year','average','owner__name','owner__slug','project_id','cover')
			for i,q in enumerate(queryset):
				if q['cover']:
					thumb_320 = get_thumbnail(q['cover'], '320', crop='center', quality=settings.THUMBNAIL_QUALITY)
					thumb_576 = get_thumbnail(q['cover'], '576', crop='center', quality=settings.THUMBNAIL_QUALITY)
					queryset[i].update({'thumb_xs':str(thumb_320)})
					queryset[i].update({'thumb_xs_w':thumb_320.width})
					queryset[i].update({'thumb_sm':str(thumb_576)})
					queryset[i].update({'thumb_sm_w':thumb_576.width})

		#	print( list(queryset).sort(key=lambda k:('last_exh_year' not in k, k.get("last_exh_year", None)) ))

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



""" Winners view """
class winners_list(ListView):
	model = Winners
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']

		if self.slug:
			posts = self.model.objects.filter(exhibition__slug=self.slug).values('exhibitor__name', 'exhibitor__slug')
		else:
			posts = self.model.objects.values('exhibitor__name', 'exhibitor__slug').distinct() #.annotate(exhibitors_count=Count('exhibitor_id'))

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants','winners']
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower
		context['exh_year'] = self.slug

		return context



""" Exhibitors detail """
class exhibitor_detail(DetailView):
	model = Exhibitors
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		slug = self.kwargs['slug']
		portfolio = Portfolio.objects.filter(owner__slug=slug).annotate(
			exh_year=F('exhibition__slug'),
			win_year=Subquery(Winners.objects.filter(portfolio_id=OuterRef('pk')).values('exhibition__slug')[:1]),
			cover=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])
		).order_by('-exh_year')
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant']
		context['winners_list'] = Nominations.objects.prefetch_related('nomination_for_winner').filter(nomination_for_winner__exhibitor__slug=slug).annotate(exh_year=F('nomination_for_winner__exhibition__slug')).values('title', 'slug', 'exh_year').order_by('exh_year')
		context['object_list'] = portfolio
		#context['exh_list'] = ', '.join(Exhibitions.objects.filter(exhibitors=self.object).values_list('title', flat=True))
		context['parent_link'] = self.model.__name__.lower
		context['cache_timeout'] = 86400
		return context


""" Jury detail """
class jury_detail(DetailView):
	model = Jury
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'jury']
		context['parent_link'] = self.model.__name__.lower
		context['cache_timeout'] = 86400
		return context


""" Partners detail """
class partner_detail(DetailView):
	model = Partners
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'partner']
		context['parent_link'] = self.model.__name__.lower
		context['cache_timeout'] = 86400
		return context


""" Event detail """
class event_detail(DetailView):
	model = Events
	template_name = 'exhibition/event_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['event']
		context['parent_link'] = self.model.__name__.lower
		return context


""" Exhibitions detail """
class exhibition_detail(DetailView):
	model = Exhibitions
	def get_object(self, queryset=None):
		slug = self.kwargs['exh_year']
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
		context['nominations_list'] = win_nominations if win_nominations else self.object.nominations.all
		context['events_title'] = Events._meta.verbose_name_plural
		context['gallery_title'] = Gallery._meta.verbose_name_plural
		context['last_exh'] = self.model.objects.only('slug')[:1].first().slug
		context['exh_year'] = self.kwargs['exh_year']
		context['today'] = now().date()
		context['model_name'] = self.model.__name__.lower
		context['cache_timeout'] = 2592000
		return context


""" Winner project detail """
class winner_project_detail(DetailView):
	model = Winners
	template_name = 'exhibition/nominations_detail.html'
	#slug_url_kwarg = 'name'
	#context_object_name = 'portfolio'

	def get_object(self, queryset=None):
		self.nom_slug = self.kwargs['slug']
		self.exh_year = self.kwargs['exh_year']

		q = self.model.objects.filter(exhibition__slug=self.exh_year,nomination__slug=self.nom_slug)[0]
		if q:
			self.exhibitors = None
			self.nomination = q.nomination
			return q
		else:
			self.exhibitors = Exhibitors.objects.prefetch_related('exhibitors_for_exh').filter(exhibitors_for_exh__slug=self.exh_year).only('name', 'slug')
			self.nomination = Nominations.objects.only('title', 'description').get(slug=self.nom_slug)
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
			portfolio = None

		context['html_classes'] = ['project']
		context['portfolio'] = portfolio
		context['exhibitors'] = self.exhibitors
		context['nomination'] = self.nomination
		context['parent_link'] = '/exhibition/%s/' % self.exh_year
		context['exh_year'] = self.exh_year
		context['nomination_slug'] = self.nom_slug

		if portfolio:
			score = Rating.calculate(portfolio)
			rate = score.average
		else:
			rate = 0

		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(portfolio=portfolio, user=self.request.user).values_list('star',flat=True).first()
		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])
		context['cache_timeout'] = 86400

		return context


""" Project detail """
class project_detail(DetailView):
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
		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])
		context['model_name'] = self.model.__name__.lower
		context['cache_timeout'] = 86400

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


""" Подслушаем событие регистрации нового пользователя и отправим письмо администратору """
# dispatch_uid: some.unique.string.id.for.allauth.user_signed_up
@receiver(user_signed_up, dispatch_uid="2020")
def user_signed_up_(request, user, **kwargs):
	user = SetUserGroup(request, user)
	template = render_to_string('account/admin_email_confirm.html', {
		'name': '%s %s (%s)' % (user.first_name, user.last_name, user.username),
		'email': user.email,
		'group': list(user.groups.all().values_list('name', flat=True)),
	})
	SendEmail('Регистрация нового пользователя на сайте sd43.ru!',template)

""" Личный кабинет зарегистрированных пользователей """
@login_required
def account(request):
	# try:
	# 	profile = Exhibitors.objects.get(user=request.user)
	# except Exhibitors.DoesNotExist:
	# 	profile = None

	profile = None
	rates = Rating.objects.filter(user=request.user)
	reviews = Reviews.objects.filter(user=request.user)

	return render(request, 'account/base.html', { 'profile': profile, 'rates': rates, 'reviews': reviews })


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

