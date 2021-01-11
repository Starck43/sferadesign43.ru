
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

#from allauth.account.decorators import verified_email_required

from .models import Rating, Reviews
from exhibition.models import Portfolio
from .forms import RatingForm, ReviewForm


"""Добавление рейтинга фильму"""
#@login_required()
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
		form = RatingForm(request.POST, user=request.user)
		score = int(request.POST.get("star"))
		portfolio_id = int(request.POST.get("portfolio"))
		existing_rating = Rating.objects.filter(portfolio_id=portfolio_id, user=request.user).first()
		if existing_rating:
			raise ValidationError('Оценка уже выставлена!')
		else:
			if form.is_valid():
				Rating.objects.create(
					ip=self.get_client_ip(request),
					user=request.user,
					portfolio_id=portfolio_id,
					star=score,
				)
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
			new_comment = {
				'id': instance.pk,
				'group': instance.group_id,
				'author': instance.fullname,
				'message': instance.message,
			}
			#print(new_comment)
		return JsonResponse(new_comment, safe=False)

	else:
		form = ReviewForm(request.POST)
		if form.is_valid():
			portfolio = Portfolio.objects.get(id=pk)
			review = form.save(commit=False)
			review.user = request.user
			review.portfolio = portfolio

			if parent and group:
				review.parent_id = int(parent)
				review.group_id = int(group)

			# сохраним комментарий, если это или корневой комментарий или подкоментарий где есть и parent и group ids
			if (parent and group) or (not parent and not group):
				review.save()

		return redirect(portfolio)


