from django import forms
from .models import Rating, Reviews

def stars_choices():
	return [(6-r,r) for r in range(1, 6)]

"""Форма добавления рейтинга"""
class RatingForm(forms.ModelForm):
	star = forms.ChoiceField(widget=forms.RadioSelect(), choices=stars_choices)

	class Meta:
		model = Rating
		fields = ("star",)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user',None)
		super().__init__(*args, **kwargs)
		if not self.user:
			self.fields['star'].widget.attrs['disabled'] = True # radio / checkbox



"""Форма отзывов"""
class ReviewForm(forms.ModelForm):
	class Meta:
		model = Reviews
		fields = ("message",)
