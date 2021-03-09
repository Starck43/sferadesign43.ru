from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from django.contrib.sitemaps import ping_google

from .models import *


def update_google_sitemap():
	try:
		ping_google() #сообщим Google о изменениях в sitemap.xml
	except Exception:
		pass


class StaticViewSitemap(Sitemap):
	priority = 0.5          # Приоритет
	changefreq = 'weekly'   # Частота проверки

	def items(self):
		return ['index', 'contacts-url']

	def location(self, item):
		return reverse(item)


class ExhibitionsSitemap(Sitemap):
	priority = 0.6
	changefreq = 'daily'

	def items(self):
		return Exhibitions.objects.all()


class WinnersSitemap(Sitemap):
	priority = 0.6
	changefreq = 'daily'

	def items(self):
		return Winners.objects.all()


class EventsSitemap(Sitemap):
	priority = 0.6
	changefreq = 'weekly'

	def items(self):
		return Events.objects.all()


class CategoriesSitemap(Sitemap):
	priority = 0.6
	changefreq = 'weekly'
	def items(self):
		return Categories.objects.all()


class PortfolioSitemap(Sitemap):
	priority = 1
	changefreq = 'daily'
	def items(self):
		return Portfolio.objects.all()


class ExhibitorsSitemap(Sitemap):
	priority = 0.9
	changefreq = 'daily'
	def items(self):
		return Exhibitors.objects.all()


class JurySitemap(Sitemap):
	priority = 0.7
	changefreq = 'monthly'
	def items(self):
		return Jury.objects.all()


class PartnersSitemap(Sitemap):
	priority = 0.7
	changefreq = 'monthly'
	def items(self):
		return Partners.objects.all()


sitemaps = {
	'static': StaticViewSitemap,
	'exhibitions': ExhibitionsSitemap,
	'winners': WinnersSitemap,
	'events': EventsSitemap,
	'categories': CategoriesSitemap,
	'portfolio': PortfolioSitemap,
	'exhibitors': ExhibitorsSitemap,
	'jury': JurySitemap,
	'partners': PartnersSitemap,
}
