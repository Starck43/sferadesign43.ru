from django.urls import path
from . import views

app_name = 'rating'

urlpatterns = [
	path("add-rating/", views.add_rating.as_view(), name='add-rating'),
	path("review/<int:pk>/", views.add_review, name="add-review"),
]
