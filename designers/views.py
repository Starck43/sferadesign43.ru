from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse, JsonResponse
from django.views.generic.detail import DetailView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader	import render_to_string
from django.db.models import Q, OuterRef, Subquery, Prefetch, CharField, Case, When
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce

from .models import Designer, Customer, Achievement
from .forms import FeedbackForm
from exhibition.logic import SendEmail
from exhibition.models import Exhibitors, Categories, Nominations, Winners, Portfolio, Image, PortfolioAttributes
from exhibition.mixins import MetaSeoMixin
from collections import defaultdict
from itertools import chain


""" Главная страница дизайнера """
#@method_decorator(csrf_exempt, name='dispatch')
class main_page(MetaSeoMixin, DetailView):
	model = Designer
	template_name = 'designers/main_page.html'
	form_class = FeedbackForm


	def get(self, request, **kwargs):
		self.slug = self.kwargs['slug']
		try:
			q = self.model.objects.get(slug=self.slug)
			if q.status != 2: # сайт не разрешен для доступа (на модерации или не оплачен)
				return redirect(q.owner)
		except self.model.DoesNotExist:
			raise Http404('Страница с таким адресом не существует!')

		return super().get(request, **kwargs)


	def get_context_data(self, **kwargs):
		designer = self.object

		exh_portfolio = self.object.exh_portfolio.annotate(
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

		victories = Nominations.objects.prefetch_related('nomination_for_winner').filter(
			nomination_for_winner__exhibitor=designer.owner).annotate(
			exh_year=F('nomination_for_winner__exhibition__slug')
		).values('title', 'slug', 'exh_year').order_by('-exh_year')

		competitions = Achievement.objects.filter(designer=designer, group=1)
		publications = Achievement.objects.filter(designer=designer, group=2)

		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['designer-page']
		context['about'] = self.object.about if self.object.about else self.object.owner.description
		context['portfolio_list'] = exh_portfolio
		context['exh_victories_list'] = victories
		context['competitions'] = competitions
		context['publications'] = publications
		context['form'] = FeedbackForm()

		return context


""" Страница со всеми проектами """
class portfolio_page(MetaSeoMixin, DetailView):
	model = Designer
	template_name = 'designers/portfolio_page.html'
	form_class = FeedbackForm

	def get(self, request, **kwargs):
		self.slug = self.kwargs['slug']
		try:
			q = self.model.objects.get(slug=self.slug)
			if q.status != 2: # сайт не разрешен для доступа (на модерации или не оплачен)
				return redirect(q.owner)
		except self.model.DoesNotExist:
			raise Http404('Страница с таким адресом не существует!')

		return super().get(request, **kwargs)


	def get_context_data(self, **kwargs):
		#designer = self.object

		exh_ids =  self.object.exh_portfolio.values_list('pk', flat=True)
		add_ids =  self.object.add_portfolio.values_list('pk', flat=True)
		owner_portfolio_ids = list(chain(exh_ids, add_ids))

		all_portfolio = Portfolio.objects.filter(pk__in=owner_portfolio_ids).prefetch_related(
			Prefetch('nominations', queryset=Nominations.objects.order_by('slug'), to_attr='nominations_list')
		).prefetch_related(
			Prefetch('categories', queryset=Categories.objects.order_by('slug'), to_attr='categories_list')
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


		exh_category = self.object.exh_portfolio.prefetch_related('nominations__category').annotate(
			category_slug=F('nominations__category__slug'),
			category_name=F('nominations__category__title')
		).values_list('category_slug', 'category_name')
		add_category = self.object.add_portfolio.prefetch_related('categories').annotate(
			category_slug=F('categories__slug'),
			category_name=F('categories__title')
		).values_list('category_slug', 'category_name')

		context = super().get_context_data(**kwargs)
		context['html_classes'] = ['designer-page', 'portfolio']
		context['portfolio_list'] = all_portfolio
		context['filter_attributes'] = list(filter(lambda x: x[0] is not None, set(tuple(exh_category) + tuple(add_category))))

		context['form'] = FeedbackForm()
		return context



""" Отправка сообщения с формы обратной связи """
@csrf_exempt
def send_message(request, slug):

	try:
		designer = Designer.objects.get(slug=slug)
		if designer.owner.email:
			recepients = [designer.owner.email]
		else:
			recepients = [designer.owner.user.email]

		print('Получатели сообщения:', recepients)
		if request.is_ajax():
			data = {
				'subdomain' :designer.slug,
				'name'  	:request.GET.get("name", None),
				'email' 	:request.GET.get("from_email", None),
				'message' 	:request.GET.get("message", None)
			}

			if email_confirmation(data,recepients):
				return JsonResponse({'status':'success'}, safe=False)
				#return HttpResponse(status=201)
			else:
				return JsonResponse({'status': 'error'}, safe=False)
				#return HttpResponse(status=400)

			# form = FeedbackForm(request.POST)
			# if form.is_valid():
			# 	data = {
			# 		'subdomain' :designer.slug,
			# 		'name'		:form.cleaned_data['name'],
			# 		'email'		:form.cleaned_data['from_email'],
			# 		'message'	:form.cleaned_data['message']
			# 	}
			# 	print(data, recepients)
			# 	if email_confirmation(data, recepients):
			# 		return redirect('/success/')

	except Designer.DoesNotExist:
		redirect(designer)


""" Отправка уведомления дизайнеру на почту """
def email_confirmation(data, recepients):
	if data['message'] and data['email']:
		template = render_to_string('designers/confirm_email.html', {
			'subdomain' :data['subdomain'],
			'name':data['name'],
			'email':data['email'],
			'message':data['message'],
		})
		# отправка письма на почту дизайнера
		return SendEmail('Сообщение с сайта', template, recepients)

