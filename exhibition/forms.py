from django import forms
from .models import Winners

class WinnersModelForm(forms.ModelForm):
	class Meta:
		model = Winners
		fields = '__all__'
