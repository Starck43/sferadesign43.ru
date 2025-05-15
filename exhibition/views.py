import math
from collections import defaultdict

from allauth.account.models import EmailAddress
from allauth.account.signals import user_signed_up
from allauth.account.views import PasswordResetView
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.signals import social_account_removed
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.files.uploadhandler import FileUploadHandler
from django.db.models import Q, OuterRef, Subquery, Avg, CharField, Case, When
from django.dispatch import receiver
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.timezone import now
# from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
# from django.views.generic import View
from django.views.generic.list import ListView
from sorl.thumbnail import get_thumbnail
from watson.views import SearchMixin

from blog.models import Article
from designers.models import Designer
from rating.forms import RatingForm
from rating.models import Rating, Reviews
from .forms import PortfolioForm, ImageForm, ImageFormHelper, FeedbackForm, UsersListForm, DeactivateUserForm
from .logic import SendEmail, SendEmailAsync, set_user_group
from .mixins import ExhibitionYearListMixin, BannersMixin, MetaSeoMixin
from .models import *


def success_message(request):
	return HttpResponse('<h1>Сообщение отправлено!</h1><p>Спасибо за обращение</p>')


def registration_policy(request):
	""" Policy page """
	return render(request, 'policy.html')


def index(request):
	""" Main page """
	context = {
		'html_classes': ['home'],
		'organizers': Organizer.objects.all().only('logo', 'name', 'description').order_by('sort', 'name'),
	}
	return render(request, 'index.html', context)


class ExhibitorsList(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	""" Exhibitors view """
	model = Exhibitors
	queryset = Exhibitors.objects.all().order_by('name')
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		if self.kwargs.get('exh_year'):
			return self.queryset.prefetch_related('exhibitors_for_exh').filter(
				exhibitors_for_exh__slug=self.kwargs['exh_year']
			)
		else:
			return self.queryset.prefetch_related('exhibitors_for_exh')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', ]
		context['cache_timeout'] = 2592000

		return context


class PartnersList(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	""" Partners view """
	model = Partners
	template_name = 'exhibition/partners_list.html'

	def get_queryset(self):
		if self.kwargs.get('exh_year'):
			q = Q(partners_for_exh__slug=self.kwargs['exh_year'])
		else:
			last_exh = Exhibitions.objects.values_list('slug', flat=True).first()
			q = ~Q(partners_for_exh__slug=last_exh)  # except last exhibition

		posts = self.model.objects.prefetch_related('partners_for_exh').filter(q)
		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'partners', ]
		context['cache_timeout'] = 2592000

		return context


class JuryList(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	""" Jury view """
	model = Jury
	queryset = model.objects.all()
	template_name = 'exhibition/persons_list.html'

	def get_queryset(self):
		if self.kwargs.get('exh_year'):
			return self.queryset.prefetch_related('jury_for_exh').filter(
				jury_for_exh__slug=self.kwargs['exh_year']
			)
		else:
			return self.queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'jury', ]
		context['cache_timeout'] = 2592000

		return context


class EventsList(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	""" Events view """
	model = Events
	template_name = 'exhibition/participants_list.html'

	def get_queryset(self):
		if self.kwargs.get('exh_year'):
			posts = self.model.objects.filter(exhibition__slug=self.kwargs['exh_year']).order_by('title')
		else:
			posts = self.model.objects.all().order_by('-exhibition__slug', 'title')

		return posts

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['events', ]

		return context


class ExhibitionsList(MetaSeoMixin, BannersMixin, ListView):
	""" Exhibition view """
	model = Exhibitions

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['exhibitions', ]
		context['page_title'] = self.model._meta.verbose_name_plural

		return context


class WinnersList(MetaSeoMixin, ExhibitionYearListMixin, ListView):
	""" Winners view """
	model = Winners
	queryset = Winners.objects.all()
	template_name = 'exhibition/winners_list.html'

	def get_queryset(self):
		query = self.queryset.select_related(
			'nomination', 'exhibitor', 'exhibition', 'portfolio'
		).annotate(
			exh_year=F('exhibition__slug'),
			nomination_title=F('nomination__title'),
			exhibitor_name=F('exhibitor__name'),
			exhibitor_slug=F('exhibitor__slug'),
			project_id=F('portfolio__project_id'),
		).values(
			'exh_year', 'nomination_title', 'exhibitor_name', 'exhibitor_slug', 'project_id'
		).order_by('exhibitor_name', '-exh_year')

		if self.kwargs.get('exh_year'):
			return query.filter(exhibition__slug=self.kwargs['exh_year'])

		return query

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participants', 'winners']
		context['cache_timeout'] = 2592000

		return context


class CategoryList(MetaSeoMixin, BannersMixin, ListView):
	""" Categories (grouped Nominations) view """
	model = Categories
	template_name = 'exhibition/category_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['nominations', ]
		context['absolute_url'] = 'category'
		context['page_title'] = self.model._meta.verbose_name_plural
		context['cache_timeout'] = 2592000
		return context


class ProjectsList(MetaSeoMixin, BannersMixin, ListView):
	""" Projects view """
	model = Categories
	template_name = 'exhibition/projects_list.html'
	PAGE_SIZE = getattr(settings, 'PORTFOLIO_COUNT_PER_PAGE', 20)  # Количество выводимых записей на странице

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.object = None
		self.slug = None
		self.page = None
		self.is_next_page = None
		self.filters_group = None

	# использовано для миксина MetaSeoMixin, где проверяется self.object
	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.slug = self.kwargs.get('slug')
		if self.slug:
			self.object = self.model.objects.get(slug=self.slug)

	def get_queryset(self):
		# Текущая страница для получения диапазона выборки записей (см.функцию get ниже)
		self.page = int(self.page) if self.page else 1

		start_page = (self.page - 1) * self.PAGE_SIZE  # начало диапазона
		end_page = self.page * self.PAGE_SIZE  # конец диапазона

		query = Q(nominations__category__slug=self.slug)

		# Если выбраны опции фильтра, то найдем все номинации в текущей категории "self.slug"
		if self.filters_group and self.filters_group[0] != '0':
			query.add(Q(attributes__in=self.filters_group), Q.AND)

		# Подзапрос для получения первого фото в портфолио
		subquery = Subquery(Image.objects.filter(portfolio=OuterRef('pk')).values('file')[:1])

		subquery2 = Subquery(Winners.objects.filter(
			portfolio_id=OuterRef('pk'),
			nomination__category__slug=self.slug
		).values('exhibition__slug')[:1])  # Подзапрос для получения статуса победителя

		posts = Portfolio.objects.filter(
			Q(exhibition__isnull=False) & Q(project_id__isnull=False) & query
		).distinct().prefetch_related('rated_portfolio').annotate(
			last_exh_year=F('exhibition__slug'),
			# cat_title=F('nominations__category__title'),
			average=Avg('rated_portfolio__star'),
			win_year=subquery2,
			project_cover=Case(
				When(Q(cover__exact='') | Q(cover__isnull=True), then=subquery),
				default='cover',
				output_field=CharField()
			)
		).values(
			'id', 'title', 'last_exh_year', 'win_year', 'average', 'owner__name', 'owner__slug', 'project_id',
			'project_cover'
		).order_by(
			'-last_exh_year', '-win_year', '-average'
		)[start_page:end_page]  # +1 сделано для выявления наличия следующей страницы

		self.is_next_page = False if len(posts) < self.PAGE_SIZE else True
		return posts  # [:self.PAGE_SIZE]

	def get(self, request, *args, **kwargs):
		self.page = self.request.GET.get('page', None)  # Параметр GET запроса ?page текущей страницы
		self.filters_group = self.request.GET.getlist('filter-group', None)
		# Выбранные опции checkbox в GET запросе (?nominations=[])

		if self.filters_group or self.page:
			default_quality = getattr(settings, 'THUMBNAIL_QUALITY', 85)
			admin_thumbnail_size = getattr(settings, 'ADMIN_THUMBNAIL_SIZE', [100, 100])
			admin_default_size = '%sx%s' % (admin_thumbnail_size[0], admin_thumbnail_size[1])
			admin_default_quality = getattr(settings, 'ADMIN_THUMBNAIL_QUALITY', 75)

			queryset = self.get_queryset()

			for i, q in enumerate(queryset):
				if q['project_cover']:
					thumb_mini = get_thumbnail(
						q['project_cover'],
						admin_default_size,
						crop='center',
						quality=admin_default_quality
					)
					thumb_320 = get_thumbnail(q['project_cover'], '320', quality=default_quality)
					thumb_576 = get_thumbnail(q['project_cover'], '576', quality=default_quality)
					queryset[i].update({
						'thumb_mini': str(thumb_mini),
						'thumb_xs': str(thumb_320),
						'thumb_sm': str(thumb_576),
						'thumb_xs_w': 320,
						'thumb_sm_w': 576
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

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		# Отсортируем и сгруппируем словарь аттрибутов по ключу group
		# keyfunc = lambda x:x['group']
		# attributes = [list(data) for _, data in groupby(sorted(data, key=keyfunc), key=keyfunc)]

		# найдем аттрибуты для фильтра в портфолио, если они есть в текущей категории
		attributes = PortfolioAttributes.objects.prefetch_related('attributes_for_portfolio').filter(
			attributes_for_portfolio__nominations__category__slug=self.slug,
			group__isnull=False,
		).distinct()

		# Формирование групп аттрибутов фильтра
		attributes_dict = attributes.values('id', 'name', 'group')
		filter_attributes = defaultdict(list)
		for i, item in enumerate(attributes_dict):
			attributes_dict[i].update({'group_name': attributes[
				i].get_group_display()})  # {queryset_row}.get_group_display() - get choice field name
			filter_attributes[item['group']].append(attributes_dict[i])

		context['html_classes'] = ['projects', ]
		context['parent_link'] = '/category'
		context['absolute_url'] = self.slug
		context['object'] = self.object
		context['next_page'] = self.is_next_page
		context['filter_attributes'] = list(filter_attributes.values())
		context['cache_timeout'] = 86400  # one day
		return context


class ProjectsListByYear(ListView):
	""" Projects by year view """
	model = Portfolio
	template_name = 'exhibition/projects_by_year.html'

	def get_queryset(self):
		# Подзапрос для получения первого фото в портфолио
		subquery = Subquery(Image.objects.filter(portfolio=OuterRef('pk')).values('file')[:1])

		return self.model.objects.filter(
			Q(exhibition__slug=self.kwargs['exh_year']) & Q(project_id__isnull=False)
		).distinct().prefetch_related('rated_portfolio').annotate(
			project_cover=Case(
				When(Q(cover__exact='') | Q(cover__isnull=True), then=subquery),
				default='cover',
				output_field=CharField()
			)
		).values('id', 'title', 'owner__name', 'owner__slug', 'project_id', 'project_cover').order_by('owner__slug')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['year'] = self.kwargs['exh_year']
		return context


class ExhibitorDetail(MetaSeoMixin, DetailView):
	""" Exhibitor detail """
	model = Exhibitors
	template_name = 'exhibition/participant_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context['object_list'] = Portfolio.objects.filter(
			owner__slug=self.kwargs['slug'],
			exhibition__isnull=False
		).annotate(
			exh_year=F('exhibition__slug'),
			win_year=Subquery(Winners.objects.filter(portfolio_id=OuterRef('pk')).values('exhibition__slug')[:1]),
			project_cover=Case(
				When(
					Q(cover__exact='') | Q(cover__isnull=True),
					then=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])
				),
				default='cover',
				output_field=CharField()
			)
		).order_by('-exh_year')

		context['article_list'] = Article.objects.filter(
			owner=self.object.user
		).only('title').order_by('title') if self.object.user else None

		context['awards_list'] = Nominations.objects.prefetch_related('nomination_for_winner').filter(
			nomination_for_winner__exhibitor__slug=self.kwargs['slug']
		).annotate(
			exh_year=F('nomination_for_winner__exhibition__slug')
		).values('title', 'slug', 'exh_year').order_by('-exh_year')

		context['html_classes'] = ['participant']
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 86400

		return context


class JuryDetail(MetaSeoMixin, BannersMixin, DetailView):
	""" Jury detail """
	model = Jury
	template_name = 'exhibition/jury_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'jury']
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 86400
		return context


class PartnerDetail(MetaSeoMixin, BannersMixin, DetailView):
	""" Partners detail """
	model = Partners
	template_name = 'exhibition/partner_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['participant', 'partner']
		context['model_name'] = self.model.__name__.lower()
		context['cache_timeout'] = 86400
		return context


class EventDetail(MetaSeoMixin, BannersMixin, DetailView):
	""" Event detail """
	model = Events
	template_name = 'exhibition/event_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['event']
		context['model_name'] = self.model.__name__.lower()
		context['exh_year'] = self.kwargs['exh_year']
		return context


class ExhibitionDetail(MetaSeoMixin, BannersMixin, DetailView):
	""" Exhibitions detail """
	model = Exhibitions

	def get_object(self, queryset=None):
		slug = self.kwargs['exh_year']
		self.kwargs['id'] = 1
		try:
			q = self.model.objects.prefetch_related('events', 'gallery').get(slug=slug)
		except self.model.DoesNotExist:
			q = None
		return q

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		win_nominations = self.object.nominations.filter(
			nomination_for_winner__exhibition_id=self.object.id
		).annotate(
			exhibitor_name=F('nomination_for_winner__exhibitor__name'),
			exhibitor_slug=F('nomination_for_winner__exhibitor__slug'),
		).values('id', 'exhibitor_name', 'exhibitor_slug', 'title', 'slug')

		# Добавляем слайды в баннер (основной + первые фото победных проектов)
		banner_slider = []
		if self.object.banner and self.object.banner.width > 0:
			banner_slider.append(self.object.banner)
			context['banner_height'] = f"{self.object.banner.height / self.object.banner.width * 100}%"

		for nom in win_nominations:
			cover = Image.objects.filter(
				portfolio__exhibition=self.object.id,
				portfolio__nominations=nom['id'],
				portfolio__owner__slug=nom['exhibitor_slug'],
			).values('file').first()

			if cover:
				banner_slider.append(cover['file'])

		context['html_classes'] = ['exhibition']
		context['banner_slider'] = banner_slider
		context['win_nominations'] = win_nominations
		context['events_title'] = Events._meta.verbose_name_plural
		context['gallery_title'] = Gallery._meta.verbose_name_plural
		context['last_exh'] = self.model.objects.only('slug').first().slug
		context['exh_year'] = self.kwargs['exh_year']
		context['model_name'] = self.model.__name__.lower()
		context['today'] = now().date()
		context['cache_timeout'] = 2592000
		return context


class WinnerProjectDetail(MetaSeoMixin, BannersMixin, DetailView):
	""" Winner project detail """
	model = Winners
	template_name = 'exhibition/nominations_detail.html'
	# slug_url_kwarg = 'name'

	def get_object(self, queryset=None):
		return self.model.objects.filter(
			exhibition__slug=self.kwargs['exh_year'],
			nomination__slug=self.kwargs['slug']
		).first()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		portfolio = None
		if self.object:
			context['nomination'] = self.object.nomination
			context['exhibitors'] = None
			try:
				if self.object.portfolio:
					portfolio = Portfolio.objects.get(pk=self.object.portfolio.id)
				else:
					portfolio = Portfolio.objects.get(
						exhibition=self.object.exhibition,
						nominations=self.object.nomination,
						owner=self.object.exhibitor
					)
			except (Portfolio.DoesNotExist, Portfolio.MultipleObjectsReturned):
				pass

		else:
			context['nomination'] = Nominations.objects.get(slug=self.kwargs['slug']).only('title', 'description')
			context['exhibitors'] = Exhibitors.objects.prefetch_related('exhibitors_for_exh').filter(
				exhibitors_for_exh__slug=self.kwargs['exh_year']
			).only('name', 'slug')

		context['html_classes'] = ['project']
		context['portfolio'] = portfolio
		context['exh_year'] = self.kwargs['exh_year']
		context['parent_link'] = '/exhibition/%s/' % self.kwargs['exh_year']

		rate = 0
		if portfolio:
			score = Rating.calculate(portfolio)
			rate = score.average

		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(
				portfolio=portfolio,
				user=self.request.user
			).values_list('star', flat=True).first()

		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['round_rate'] = math.ceil(rate)
		context['extra_rate_percent'] = int((rate - int(rate)) * 100)
		context['rating_form'] = RatingForm(
			initial={'star': int(rate)},
			user=self.request.user,
			score=context['user_score']
		)
		context['cache_timeout'] = 86400

		return context


class ProjectDetail(MetaSeoMixin, DetailView):
	""" Project detail """
	model = Portfolio
	context_object_name = 'portfolio'
	template_name = 'exhibition/portfolio_detail.html'
	# slug_url_kwarg = 'slug'

	def get_object(self, queryset=None):
		# Найдем портфолио и победу в номинациях если есть
		obj = None
		if self.kwargs.get('owner') and self.kwargs.get('project_id'):
			try:
				obj = self.model.objects.get(
					project_id=self.kwargs['project_id'],
					owner__slug=self.kwargs['owner']
				)
			except self.model.DoesNotExist:
				pass

		return obj

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		context['victories'] = Winners.objects.filter(
			portfolio=self.object.id,
			exhibitor__slug=self.kwargs['owner']
		) if self.object else None

		if self.request.META.get('HTTP_REFERER') is None:
			nomination = self.object.nominations.filter(category__slug__isnull=False).first()
			if nomination and self.object:
				context['parent_link'] = '/category/%s/' % nomination.category.slug
			else:
				context['parent_link'] = '/category/'

		rate = Rating.calculate(self.object).average
		if self.request.user.is_authenticated:
			context['user_score'] = Rating.objects.filter(
				portfolio=self.object,
				user=self.request.user
			).values_list('star', flat=True).first()
		else:
			context['user_score'] = None

		context['average_rate'] = round(rate, 2)
		context['round_rate'] = math.ceil(rate)
		context['extra_rate_percent'] = int((rate - int(rate)) * 100)
		context['rating_form'] = RatingForm(
			initial={'star': int(rate)},
			user=self.request.user,
			score=context['user_score']
		)
		context['html_classes'] = ['project']
		context['owner'] = self.kwargs['owner']
		context['project_id'] = self.kwargs['project_id']
		context['cache_timeout'] = 86400

		return context


def contacts(request):
	""" Отправка сообщения с формы обратной связи """
	if request.method == 'POST':
		# если метод POST, проверим форму и отправим письмо
		form = FeedbackForm(request.POST)
		if form.is_valid():
			template = render_to_string('contacts/confirm_email.html', {
				'name': form.cleaned_data['name'],
				'email': form.cleaned_data['from_email'],
				'message': form.cleaned_data['message'],
			})

			if SendEmail('Получено новое сообщение с сайта sd43.ru!', template):
				return redirect('/success/')

	else:
		form = FeedbackForm()

	context = {
		'html_classes': ['contacts'],
		'form': form,
	}
	return render(request, 'contacts.html', context)


class SearchSite(SearchMixin, ListView):
	""" Watson model's search """
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
		return raw_data

	def file_complete(self, file_size):
		...


@csrf_exempt
@login_required
def portfolio_upload(request, **kwargs):
	""" Выгрузка нового портфолио """
	request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
	# upload_file_view(request)
	pk = kwargs.pop('pk', None)
	if pk:
		portfolio = Portfolio.objects.get(id=pk)
	else:
		portfolio = None  # Portfolio()

	if not request.user.is_staff:
		owner = Exhibitors.objects.get(user=request.user)
	else:
		owner = 'staff'
	# owner = Exhibitors.objects.get(user=4)

	form = PortfolioForm(owner=owner, instance=portfolio)
	inline_form_set = inlineformset_factory(Portfolio, Image, form=ImageForm, extra=0, can_delete=True)
	formset = inline_form_set(instance=portfolio)
	formset_helper = ImageFormHelper()

	if request.method == 'POST':
		form = PortfolioForm(request.POST, request.FILES, request=request, instance=portfolio)

		if form.is_valid():
			formset = inline_form_set(request.POST, request.FILES, instance=portfolio)
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
					'new': True
				}
				if pk:
					context['changed_fields'] = form.changed_data
					context['new'] = False

				# template = render_to_string('account/portfolio_upload_confirm.html', context)
				# SendEmailAsync('%s портфолио на сайте sd43.ru!' % ('Внесены изменения в' if pk else 'Добавлено новое'), template)

				if not pk:
					# MetaSEO.objects.create(
					# 	model=form.meta_model,
					# 	post_id=portfolio.id,
					# 	title=form.cleaned_data['meta_title'],
					# 	description=form.cleaned_data['meta_description'],
					# 	keywords=form.cleaned_data['meta_keywords'],
					# )
					return render(request, 'success_upload.html', {'portfolio': portfolio, 'files': images})

				return redirect('/account')
			else:
				print(formset.errors)

	return render(
		request,
		'upload.html',
		{'form': form, "formset": formset, 'portfolio_id': pk, 'formset_helper': formset_helper}
	)


# @receiver(pre_save, sender=Portfolio)
# def on_change(sender, instance, **kwargs):
# 	if instance.pk:
# 		pass


@login_required
def account(request):
	""" Личный кабинет зарегистрированных пользователей """
	try:
		# exhibitor = Exhibitors.objects.get(user=4)
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
				When(
					Q(cover__exact='') | Q(cover__isnull=True),
					then=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])
				),
				default='cover',
				output_field=CharField()
			)
		).order_by('-exh_year')

		try:
			# designer = Designer.objects.get(owner__user=4)
			designer = Designer.objects.get(owner=exhibitor)

			add_portfolio = designer.add_portfolio.all().annotate(
				project_cover=Case(
					When(
						Q(cover__exact='') | Q(cover__isnull=True),
						then=Subquery(Image.objects.filter(portfolio_id=OuterRef('pk')).values('file')[:1])
					),
					default='cover',
					output_field=CharField()
				)
			).order_by('title')

			victories = Nominations.objects.prefetch_related('nomination_for_winner').filter(
				nomination_for_winner__exhibitor=exhibitor).annotate(
				exh_year=F('nomination_for_winner__exhibition__slug')
			).values('title', 'slug', 'exh_year').order_by('-exh_year')

			achievements = designer.achievements.all().order_by('group')
		# customers = designer.customers.all()

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


@staff_member_required
def send_reset_password_email(request):
	""" Sending reset password emails to exhibitors """
	if request.method == 'POST':
		form = UsersListForm(request.POST)
		if form.is_valid():
			users_email = request.POST.getlist('users') or None
			for email in users_email:
				request.POST = {
					'email': email,
					# 'csrfmiddlewaretoken': get_token(request) #HttpRequest()
				}
				# allauth reset password email send
				PasswordResetView.as_view()(request)

			# return render(request,'account/email/exhibitors/password_reset_key_message.html',self.data)
			return HttpResponse('<h1>Письма успешно отправлены!</h1>')
		else:
			return HttpResponse('<h1>Что-то пошло не так...</h1>')

	else:
		form = UsersListForm()

	return render(request, 'account/send_password_reset_email.html', {'form': form})


@login_required
# @method_decorator(csrf_exempt, name='dispatch')
def deactivate_user(request):
	""" Удаление аккаунта пользователя """
	if request.method == 'POST':
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
					request=request,
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

	else:
		form = DeactivateUserForm()

	return render(request, 'account/deactivation.html', {'form': form})


# dispatch_uid: some.unique.string.id.for.allauth.user_signed_up
@receiver(user_signed_up, dispatch_uid="new_user")
def user_signed_up_(request, user, **kwargs):
	""" Подслушаем событие регистрации нового пользователя и отправим письмо администратору """
	user = set_user_group(request, user)
	template = render_to_string('account/admin_email_confirm.html', {
		'name': '%s %s (%s)' % (user.first_name, user.last_name, user.username),
		'email': user.email,
		'group': list(user.groups.all().values_list('name', flat=True)),
	})
	SendEmailAsync('Регистрация нового пользователя на сайте sd43.ru!', template)
