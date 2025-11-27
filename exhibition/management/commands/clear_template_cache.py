from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key


class Command(BaseCommand):
	help = 'Clear template fragments cache with smart argument detection'

	def add_arguments(self, parser):
		parser.add_argument('--all', action='store_true', help='Clear all fragments')
		parser.add_argument('--verbose', action='store_true', help='Verbose output')

	def handle(self, *args, **options):
		if not options['all']:
			self.stdout.write(self.style.WARNING("Use --all to clear fragments"))
			return

		cleared = self.clear_with_variants(options['verbose'])
		self.stdout.write(self.style.SUCCESS(f"Cleared {cleared} fragment(s)"))

	def clear_with_variants(self, verbose=False):
		"""Clear fragments with different argument variants"""
		fragments = [
			# Без аргументов
			'articles', 'categories_list', 'exhibitions_list', 'index_page', 'navbar',

			# С одним аргументом
			'exhibition_content', 'exhibition_events', 'exhibition_overlay',
			'exhibition_gallery', 'exhibition_banner', 'participant_detail',
			'projects_list', 'sidebar',

			# С двумя аргументами
			'persons', 'portfolio_slider',

			# С тремя аргументами
			'portfolio_list',
		]

		cleared = 0

		for fragment in fragments:
			# Пробуем разные варианты аргументов
			variants = self.get_argument_variants(fragment)

			for variant in variants:
				key = make_template_fragment_key(fragment, variant)
				if cache.delete(key):
					if verbose:
						self.stdout.write(f"✓ {fragment} {variant}")
					cleared += 1

		return cleared

	def get_argument_variants(self, fragment_name):
		"""Return possible argument variants for a fragment"""
		if fragment_name in ['articles', 'categories_list', 'exhibitions_list', 'index_page', 'navbar']:
			return [[]]  # Без аргументов

		elif fragment_name == 'persons':
			return [
				['exhibitors', None], ['exhibitors', ''],
				['jury', None], ['jury', ''],
				['winners', None], ['winners', ''],
				['partners', None], ['partners', ''],
			]

		elif fragment_name in ['portfolio_list']:
			return [
				['', '', True], ['', '', False],
			]

		elif fragment_name in ['portfolio_slider']:
			return [['', '']]

		else:
			# Для остальных - пробуем пустой аргумент
			return [[None], ['']]
