from django.urls import path, re_path
from . import views

# app_name = 'design'

urlpatterns = [
	path('', views.index, name='index'),

	path('exhibitions/',views.exhibitions_list.as_view(), kwargs={'exh_year': None}, name='exhibitions-list-url'),
	path('exhibition/<exh_year>/',views.exhibition_detail.as_view(), name='exhibition-detail-url'),
	path('exhibition/<exh_year>/<slug>/', views.winner_project_detail.as_view(), name='winner-detail-url'),

	path('category/',views.category_list.as_view(), kwargs={'slug': None}, name='category-list-url'),
	path('category/<slug>/',views.projects_list.as_view(), name='projects-list-url'),
	#path('category/<slug>/projects/',views.ajax_projects.as_view(), name='load-projects'), # for ajax
	path('projects/<owner>/project-<project_id>/', views.project_detail.as_view(), name='project-detail-url'),

	path('jury/',views.jury_list.as_view(), kwargs={'exh_year': None}, name='jury-list-url'),
	path('jury/<exh_year>/',views.jury_list.as_view(), name='jury-list-url'),
	path('jury/<slug>/detail/', views.jury_detail.as_view(), name='jury-detail-url'),

	path('partners/',views.partners_list.as_view(), kwargs={'exh_year': None}, name='partners-list-url'),
	path('partners/<exh_year>/',views.partners_list.as_view(), name='partners-list-url'),
	path('partner/<slug>/detail/', views.partner_detail.as_view(), name='partner-detail-url'),

	path('exhibitors/',views.exhibitors_list.as_view(), kwargs={'exh_year': None}, name='exhibitors-list-url'),
	path('exhibitors/<exh_year>/',views.exhibitors_list.as_view(), name='exhibitors-list-url'),
	path('exhibitor/<slug>/detail/', views.exhibitor_detail.as_view(), name='exhibitor-detail-url'),

	path('winners/', views.winners_list.as_view(), kwargs={'exh_year': None}, name='winners-list-url'),
	path('winners/<exh_year>/', views.winners_list.as_view(), name='winners-list-url'),

	path('events/', views.events_list.as_view(), kwargs={'exh_year': None}, name='events-list-url'),
	path('events/<exh_year>/', views.events_list.as_view(), name='events-list-url'),
	path('events/<exh_year>/<pk>/', views.event_detail.as_view(), name='event-detail-url'),


	#path('exhibition/events/<pk>/', views.event_detail.as_view(), name='event-detail-url'),
	#path('exhibition/<exh_year>/events/<pk>/', views.event_detail.as_view(), name='event-detail-url'),
	path('contacts/', views.contacts, name='contacts-url'),
	path('policy/', views.registration_policy, name='policy-url'),

	re_path(r'^search/', views.search_site.as_view(), name='search-results'),
	path('account/', views.account, name='account-url'),
	path('account/deactivate/',views.deactivate_user, name="deactivate-user"),
	path('reset_password/', views.send_reset_password_email),
	path('upload/', views.portfolio_upload, name='portfolio-upload-url'),
	re_path(r'^success/$', views.success_message, name='success-message-url'),

	# path('<str:section>/about/', views.about_us, name='about-us-url'),
	# path('about/', views.about_us, name='about-us-url'),
]
