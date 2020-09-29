from django.urls import path
from django.conf.urls import url
from . import views

# app_name = 'design'

urlpatterns = [
	path('', views.index, name='index'),
	# path('<str:section>/contacts/', views.contacts, name='contacts-url'),
	# path('<str:section>/about/', views.about_us, name='about-us-url'),
	# path('design/', views.design, name='design-url'),
	# # path('styling/', include('design.urls')),
	path('exhibitors/',views.exhibitors_list.as_view(), name='exhibitors-list-url'),
	path('exhibitors/<exh_year>/',views.exhibitors_list.as_view(), name='exhibitors-list-url'),
	path('winners/', views.winners_list.as_view(), name='winners-list-url'),
	path('winners/<exh_year>/', views.winners_list.as_view(), name='winners-list-url'),
	# path('<str:section>/contacts/', views.contacts, name='contacts-url'),
	# path('<str:section>/about/', views.about_us, name='about-us-url'),
]
