
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
	return HttpResponse('Сообщение отправлено! Спасибо за вашу заявку.')


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
		context['exhibition'] = self.slug

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
		context['exhibition'] = self.slug

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
		context['exhibition'] = self.slug

		return context


""" Exhibitons view """
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
		context['exhibition'] = self.slug

		return context


""" Projects view """
class projects_list(ListView):
	model = Portfolio
	template_name = 'exhibition/projects_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['slug']
		# Выбранные опции checkbox в GET запросе (?nominations=[])
		filter_list = self.request.GET.getlist("filter-group", None)
		filter_query = Q(nominations__category__slug=self.slug)
		#nominations_list = Nominations.objects.filter(category__slug=self.slug).values_list('id',flat=True)
		#nominations_query = Q(nominations__in=list(nominations_list))

		# Если выбраны опции фильтра, то найдем все номинации в текущей категории "self.slug"
		if filter_list and filter_list[0] != '0':
			filter_query.add(Q(attributes__in=filter_list), Q.AND)

		subqry = Subquery(Image.objects.filter(portfolio=OuterRef('pk')).values('file')[:1])
		subqry2 = Subquery(Winners.objects.filter(
			portfolio_id=OuterRef('pk'),
			nomination__category__slug=self.slug
		).values('exhibition__slug'))

		posts = self.model.objects.filter(
			filter_query &
			#Q(nominations__category__slug=self.slug) &
			Q(project_id__isnull=False)
		).distinct().prefetch_related('rated_portfolio').annotate(
			cat_title=F('nominations__category__title'),
			average=Avg('rated_portfolio__star'),
			exh_year=subqry2,
			cover=subqry
		).order_by('-exhibition__date_start')

		return posts

	def get_context_data(self, **kwargs):
		#attributes = self.object_list.distinct().filter(attributes__group__isnull=False).annotate(attribute_id=F('attributes'), group=F('attributes__group'), name=F('attributes__name'))#.values('group', 'name', 'attribute_id').order_by('group', 'name')
		# Отсортируем и сгруппируем словарь аттрибутов по ключу group
		# keyfunc = lambda x:x['group']
		# attributes = [list(data) for _, data in groupby(sorted(data, key=keyfunc), key=keyfunc)]
		attributes = PortfolioAttributes.objects.prefetch_related('attributes_for_portfolio').filter(id__in=self.object_list.values_list('attributes',flat=True),group__isnull=False).distinct()
		#print(attributes)
		attributes_dict = attributes.values('id','name','group')
		filter_attributes = defaultdict(list)
		for i,item in enumerate(attributes_dict):
			attributes_dict[i].update({'group_name':attributes[i].get_group_display()})
			filter_attributes[item['group']].append(attributes_dict[i])

		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['projects',]
		context['absolute_url'] = self.slug
		context['filter_attributes'] = list(filter_attributes.values())

		#context['nominations'] = self.nominations
		return context

	def get(self, request, *args, **kwargs):
		filter_list = request.GET.getlist("filter-group", None)
		if filter_list and filter_list != '0':
			queryset = self.get_queryset().values('id','title','average','owner__name','owner__slug','project_id','cover')
			for i,q in enumerate(queryset):
				thumb_320 = get_thumbnail(q['cover'], '320', crop='center', quality=settings.THUMBNAIL_QUALITY)
				thumb_576 = get_thumbnail(q['cover'], '576', crop='center', quality=settings.THUMBNAIL_QUALITY)
				queryset[i].update({'thumb_xs':str(thumb_320)})
				queryset[i].update({'thumb_xs_w':thumb_320.width})
				queryset[i].update({'thumb_sm':str(thumb_576)})
				queryset[i].update({'thumb_sm_w':thumb_576.width})

			return JsonResponse({"projects_list": list(queryset), 'media_url': settings.MEDIA_URL, 'projects_url':'/projects/'}, safe=False)
		else:
			#print(self.paginate_by)
			#self.paginate_by = 2
			return super().get(request, **kwargs)



""" Winners view """
class winners_list(ListView):
	model = Winners
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		self.slug = self.kwargs['exh_year']

		if self.slug:
			posts = self.model.objects.select_related('exhibition').filter(exhibition__date_start__year=self.slug).values('exhibitor__name', 'exhibitor__slug').order_by('exhibitor__name')
		else:
			posts = self.model.objects.select_related('exhibitors').values('exhibitor__name', 'exhibitor__slug').distinct().order_by('exhibitor__name') #.annotate(exhibitors_count=Count('exhibitor_id'))

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants',]
		context['page_title'] = self.model._meta.verbose_name_plural
		context['absolute_url'] = self.model.__name__.lower
		context['exhibition'] = self.slug

		return context



""" Exhibitors detail """
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
		context['model_name'] = self.model.__name__.lower
		context['cache_timeout'] = 2592000

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
		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['extra_rate_percent'] = int((rate - int(rate))*100)
		context['rating_form'] = RatingForm(initial={'star': int(rate)}, user=self.request.user, score=context['user_score'])

		return context


""" Project detail """
class project_detail(DetailView):
	model = Portfolio
	#slug_url_kwarg = 'slug'
	context_object_name = 'portfolio'
	#template_name = 'exhibition/portfolio_detail.html'

	def get_object(self, queryset=None):
#	def get_queryset(self):
		self.owner = self.kwargs['owner']
		self.project = self.kwargs['project_id']
		if (self.owner != 'None' and self.project != 'None'):
			# Найдем портфолио и победу в номинациях если есть
			try:
				q = self.model.objects.get(project_id=self.project, owner__slug=self.owner)
				#q = self.model.objects.prefetch_related('portfolio_for_winner').annotate(win_year=Coalesce('portfolio_for_winner__exhibition__slug',None)).get(project_id=self.project, owner__slug=self.owner)
			except self.model.DoesNotExist:
				q = None
		else:
			q = None
		return q

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['project']
		context['parent_link'] = self.request.META.get('HTTP_REFERER')
		context['victories'] = Winners.objects.filter(portfolio=self.object.id, exhibitor__slug=self.owner)
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
		context['cache_timeout'] = 86400
		context['model_name'] = self.model.__name__.lower

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
					'protocol': 'https' if request.is_secure() else 'http',
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

