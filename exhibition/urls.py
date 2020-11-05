from django.urls import path, re_path
from . import views

# app_name = 'design'

urlpatterns = [
	path('', views.index, name='index'),
	# path('<str:section>/contacts/', views.contacts, name='contacts-url'),
	# path('<str:section>/about/', views.about_us, name='about-us-url'),
	# path('design/', views.design, name='design-url'),
	# # path('styling/', include('design.urls')),
	path('exhibitions/',views.exhibitions_list.as_view(), kwargs={'exh_year': None}, name='exhibitions-list-url'),
	path('exhibitions/<slug>/',views.exhibition_detail.as_view(), name='exhibition-detail-url'),
	path('exhibitions/<slug>/<name>/', views.nomination_detail.as_view(), name='nomination-detail-url'),

	#path('nominations/',views.nominations_list.as_view(), kwargs={'exh_year': None}, name='nominations-list-url'),
	# path('nominations/<exh_year>/',views.nominations_list.as_view(), name='nominations-by-year-list-url'),
	# path('nominations/<exh_year>/<name>/detail/', views.nomination_detail.as_view(), name='nomination-detail-url'),

	path('jury/',views.jury_list.as_view(), kwargs={'exh_year': None}, name='jury-list-url'),
	path('jury/<exh_year>/',views.jury_list.as_view(), name='jury-by-year-list-url'),
	path('jury/<slug>/detail/', views.jury_detail.as_view(), name='jury-detail-url'),

	path('partners/',views.partners_list.as_view(), kwargs={'exh_year': None}, name='partners-list-url'),
	path('partners/<exh_year>/',views.partners_list.as_view(), name='partners-by-year-list-url'),
	path('partner/<slug>/detail/', views.partner_detail.as_view(), name='partner-detail-url'),

	path('exhibitors/',views.exhibitors_list.as_view(), kwargs={'exh_year': None}, name='exhibitors-list-url'),
	path('exhibitors/<exh_year>/',views.exhibitors_list.as_view(), name='exhibitors-by-year-list-url'),
	path('exhibitor/<slug>/detail/', views.exhibitor_detail.as_view(), name='exhibitor-detail-url'),

	path('winners/', views.winners_list.as_view(), kwargs={'exh_year': None}, name='winners-list-url'),
	path('winners/<exh_year>/', views.winners_list.as_view(), name='winners-by-year-list-url'),

	path('events/<exh_year>/', views.events_list.as_view(), name='events-list-url'),
	#path('events/<exh_year>/<pk>/', views.event_detail.as_view(), name='event-detail-url'),


	#path('exhibition/events/<pk>/', views.event_detail.as_view(), name='event-detail-url'),
	#path('exhibition/<exh_year>/events/<pk>/', views.event_detail.as_view(), name='event-detail-url'),
	#
	path('contacts/', views.contacts, name='contacts-url'),
	# path('<str:section>/about/', views.about_us, name='about-us-url'),
]
