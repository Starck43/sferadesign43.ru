from django.urls import path
from . import views

app_name = 'designers'

urlpatterns = [
	path("<str:slug>/", views.main_page.as_view(), name="designer-page-url"),
	path("<str:slug>/portfolio", views.portfolio_page.as_view(), name="portfolio-page-url"),
	path("<str:slug>/send_message", views.send_message, name="send-message"),
]
