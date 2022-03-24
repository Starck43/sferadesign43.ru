"""crm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

from django.contrib.sitemaps.views import sitemap
from exhibition.sitemap import sitemaps


urlpatterns = [
	re_path(r'^admin/', admin.site.urls),
	path('accounts/', include('allauth.urls')),
	path('designers/', include('designers.urls')),
	path('', include('exhibition.urls')),
	path('', include('rating.urls')),
	path('', include('blog.urls')),
	re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
	re_path(r'^chaining/', include('smart_selects.urls')),
	re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
	path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),

]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	import debug_toolbar
	urlpatterns = [
		path('__debug__/', include(debug_toolbar.urls)),
	] + urlpatterns

