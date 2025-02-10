from django.urls import path
from . import views

app_name = 'designers'

urlpatterns = [
	path("<str:slug>/", views.MainPage.as_view(), name="designer-page-url"),
	path("<str:slug>/portfolio/", views.PortfolioPage.as_view(), name="portfolio-page-url"),
	path("<str:slug>/portfolio/<int:project_id>/", views.PortfolioDetailPage.as_view(), name="portfolio-detail-page-url"),
	path("<str:slug>/send_message", views.send_message, name="send-message"),
]
