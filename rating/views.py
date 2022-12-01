
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils.cache import get_cache_key
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.template.loader	import render_to_string

#from allauth.account.decorators import verified_email_required

from .models import Rating, Reviews
from exhibition.models import Portfolio
from exhibition.logic import delete_cached_fragment, SendEmailAsync
from .forms import RatingForm, ReviewForm


"""Добавление рейтинга проекту"""
@method_decorator(csrf_exempt, name='dispatch')
class add_rating(View):
	def get_client_ip(self, request):
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			ip = x_forwarded_for.split(',')[0]
		else:
			ip = request.META.get('REMOTE_ADDR')
		return ip


	def get(self, request):
		form = RatingForm(user=request.user)

	def post(self, request):
		score = int(request.GET.get("star"))
		portfolio_id = int(request.GET.get("portfolio"))
		rating_exists = Rating.objects.filter(portfolio_id=portfolio_id, user=request.user).first()
		if not rating_exists:
		# 	raise ValidationError('Оценка уже выставлена!')
		# 	return HttpResponse(status=400)
			Rating.objects.create(
				ip=self.get_client_ip(request),
				user=request.user,
				portfolio_id=portfolio_id,
				star=score,
			)

		delete_cached_fragment('portfolio', portfolio_id)
		delete_cached_fragment('project', portfolio_id)

		if request.is_ajax():
			portfolio = Portfolio.objects.get(id=portfolio_id)
			score_avg = Rating.calculate(portfolio).average
			# round_rate = math.ceil(score_avg)
			return JsonResponse({
				'score': score,
				'score_avg': score_avg,
				#'round_rate': round_rate,
				'author': portfolio.owner.name
			}, safe=False)
		else:
			form = RatingForm(request.POST, user=request.user)
			if form.is_valid():
				form.save();
				return HttpResponse(status=201)
			else:
				return HttpResponse(status=400)


"""Комментарии"""
@csrf_exempt
def add_review(request, pk):
	parent = request.GET.get("parent", None)
	group = request.GET.get("group", None)
	if request.is_ajax():
		new_comment = {};
		message = request.GET.get("message", None)
		if message:
			instance = Reviews.objects.create(
				user=request.user,
				portfolio_id=pk,
				parent_id=parent,
				group_id=group,
				message=message,
			)

			# Асинхронная отправка письма с ответом на комментарий
			if parent:
				portfolio = Portfolio.objects.get(id=pk)
				reply_review = Reviews.objects.get(id=parent)

				protocol = 'https' if request.is_secure() else 'http'
				project_link = "{0}://{1}/{2}".format(protocol, request.get_host(), portfolio.get_absolute_url().strip("/"))
				reply_link = "{0}://{1}/{2}#{3}".format(protocol, request.get_host(), portfolio.get_absolute_url().strip("/"), reply_review.id)
				subject = 'Ответ на ваш комментарий на сайте Сфера Дизайна'
				template = render_to_string('rating/reply_notification.html', {
					'project': portfolio,
					'project_link': project_link,
					'reply_link': reply_link,
					'comment': reply_review.message,
					'reply_name': '%s %s' % (request.user.first_name, request.user.last_name),
					'reply_comment': message,
				})
				SendEmailAsync(subject, template, [reply_review.user.email])

			#delete_cached_fragment('portfolio_review', pk)

			# Подсчитаем количество подкомментариев у родителя
			if instance.parent_id:
				reply_count = Reviews.objects.get(id=instance.parent_id).reply_count()
			else:
				reply_count = 0

			new_comment = {
				'id': instance.pk,
				'parent': instance.parent_id,
				'group': instance.group_id,
				'author': instance.fullname,
				'message': message,
				'reply_count': reply_count,
			}

		return JsonResponse(new_comment, safe=False)

	else:
		form = ReviewForm(request.POST)
		portfolio = Portfolio.objects.get(id=pk)
		if form.is_valid():
			review = form.save(commit=False)
			review.user = request.user
			review.portfolio = portfolio

			if parent and group:
				review.parent_id = int(parent)
				review.group_id = int(group)

			# сохраним комментарий, если это или корневой комментарий или подкоментарий где есть и parent и group ids
			if (parent and group) or (not parent and not group):
				delete_cached_fragment('portfolio_review', pk)
				review.save()

		return redirect(portfolio)


@csrf_exempt
@login_required
def edit_review(request, pk=None):
	message = request.GET.get("message", None)
	if message:
		try:
			instance = Reviews.objects.get(pk=pk, user=request.user)
			instance.message=message
			#instance.message=unicode_emoji(message)
			instance.save()
			#delete_cached_fragment('portfolio_review', instance.portfolio_id)

			if request.method == 'GET':
				return HttpResponse('<h1>Комментарий успешно изменен!</h1><br/><p>%s</p>' % instance.message)
			else:
				json = {
					'status': 'success',
					'message': 'Комментарий изменен!',
				}
		except Reviews.DoesNotExist:
			json = {
				'status': 'error',
				'message': 'Комментарий не существует! (ID:'+str(pk)+')',
			}
	else:
		json = {
			'status': 'warning',
			'message': 'Пустое сообщение!',
		}

	return JsonResponse(json, safe=False)


@csrf_exempt
@login_required
def delete_review(request, pk=None):

	try:
		instance = Reviews.objects.get(pk=pk, user=request.user)
		message = instance.message
		instance.delete()
		delete_cached_fragment('portfolio_review', instance.portfolio_id)

		if request.method == 'GET':
			return HttpResponse('<h1>Комментарий успешно удален!</h1><br/><p>%s</p>' % message)
		else:
			json = {
				'status': 'success',
				'message': 'Комментарий удален',
			}

	except Reviews.DoesNotExist:
		json = {
			'status': 'error',
			'message': 'Комментарий не существует! (ID:'+str(pk)+')',
		}

	return JsonResponse(json, safe=False)

