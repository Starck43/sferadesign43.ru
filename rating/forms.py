from django import forms
from .models import Rating, Reviews


def stars_choices():
	return [(6 - r, r) for r in range(1, 6)]


class RatingForm(forms.ModelForm):
	"""Форма добавления рейтинга"""
	star = forms.ChoiceField(widget=forms.RadioSelect(), choices=stars_choices)

	class Meta:
		model = Rating
		fields = ("star",)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user', None)
		self.score = kwargs.pop('score', None)
		super().__init__(*args, **kwargs)
		if not self.user.is_authenticated or self.score:
			self.fields['star'].widget.attrs['disabled'] = True  # radio / checkbox


class ReviewForm(forms.ModelForm):
	"""Форма отзывов"""
	class Meta:
		model = Reviews
		fields = ("message",)

