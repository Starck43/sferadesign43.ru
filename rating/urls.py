from django.urls import path
from . import views

app_name = 'rating'

urlpatterns = [
	path("add-rating/", views.AddRating.as_view(), name='add-rating'),
	path("review/<int:pk>/", views.add_review, name="add-review"),
	path("review/edit/<int:pk>/", views.edit_review, name="edit-review"),
	path("review/delete/<int:pk>/", views.delete_review, name="delete-review"),
]
