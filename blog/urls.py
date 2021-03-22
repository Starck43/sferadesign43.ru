from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
	path("articles/", views.article_list.as_view(), name='article-list-url'),
	path("articles/<int:pk>/", views.article_detail.as_view(), name="article-detail-url"),
]
