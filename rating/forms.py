from django import forms
from .models import Rating, Reviews, JuryRating


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


class JuryRatingForm(forms.ModelForm):
	"""Форма добавления оценки жюри"""
	star = forms.ChoiceField(
		widget=forms.RadioSelect(attrs={'class': 'jury-rating-stars'}), 
		choices=stars_choices,
		label='Ваша оценка как члена жюри'
	)

	class Meta:
		model = JuryRating
		fields = ("star",)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user', None)
		self.score = kwargs.pop('score', None)
		self.can_rate = kwargs.pop('can_rate', False)
		super().__init__(*args, **kwargs)
		
		if not self.can_rate or self.score:
			self.fields['star'].widget.attrs['disabled'] = True
		
		if self.score:
			self.fields['star'].initial = 6 - self.score  # Инверсия для stars_choices


class ReviewForm(forms.ModelForm):
	"""Форма отзывов"""
	class Meta:
		model = Reviews
		fields = ("message",)

