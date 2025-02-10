from itertools import chain

from django.contrib.sitemaps import Sitemap
from django.db.models import Q, Count

from designers.models import Designer
from exhibition.models import *
from blog.models import Article


class StaticViewSitemap(Sitemap):
	priority = 0.5  # Приоритет
	changefreq = 'daily'  # Частота проверки

	def items(self):
		return [
			'exhibition:index',
			'exhibition:contacts-url',
			'exhibition:exhibitions-list-url',
			'exhibition:category-list-url',
			'exhibition:winners-list-url',
			'exhibition:events-list-url',
			'exhibition:exhibitors-list-url',
			'exhibition:jury-list-url',
			'exhibition:partners-list-url',
			'blog:article-list-url',
		]

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


class ArticleSitemap(Sitemap):
	priority = 1
	changefreq = 'daily'

	def items(self):
		return Article.objects.all()


class DesignersSitemap(Sitemap):
	priority = 1
	changefreq = 'weekly'

	def items(self):
		return Designer.objects.all()


class DesignerPortfolioSitemap(Sitemap):
	priority = 1.0
	changefreq = 'weekly'

	def items(self):
		return Designer.objects.filter(status=2)

	def location(self, item):
		return reverse('designers:portfolio-page-url', args=[item.slug])


class DesignersPortfolioSitemap(Sitemap):
	priority = 1.0
	changefreq = 'weekly'

	def items(self):
		portfolios = (
			Designer.objects
			.filter(status=2)
			.prefetch_related('exh_portfolio', 'add_portfolio')
			.annotate(
				exh_portfolio_count=Count('exh_portfolio', filter=Q(exh_portfolio__status=True)),
				add_portfolio_count=Count('add_portfolio', filter=Q(add_portfolio__status=True)),
			)
			.filter(
				Q(exh_portfolio_count__gt=0) | Q(add_portfolio_count__gt=0)
			)
		)

		return [(d, p) for d in portfolios for p in (d.exh_portfolio.all() | d.add_portfolio.all())]

	def location(self, item):
		designer, portfolio = item
		return reverse('designers:portfolio-detail-page-url', args=[designer.slug, portfolio.project_id])


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
	'article': ArticleSitemap,
	'designers': DesignersSitemap,
	'designer_portfolio': DesignerPortfolioSitemap,
	'portfolios': DesignersPortfolioSitemap,
}
