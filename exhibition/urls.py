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
	# path('design/<str:category>/',views.project_list.as_view(), name='projects-url'),
	# path('design/<str:category>/<str:slug>/', views.project_detail.as_view(), name='project-detail-url'),
	# path('<str:section>/contacts/', views.contacts, name='contacts-url'),
	# path('<str:section>/about/', views.about_us, name='about-us-url'),
]
