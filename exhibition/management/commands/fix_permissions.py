from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.management import create_permissions
from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
	help = 'Recreate permissions from scratch'

	def handle(self, *args, **options):
		# Run this method via shell whenever any amendments in any of the tables is made

		#print("Deleting existing user permissions...")
		#Permission.objects.all().delete()
		apps_list = []
		#apps_list.append(apps.get_app_config('auth'))
		#apps_list.append(apps.get_app_config('sites'))
		#apps_list.append(apps.get_app_config('contenttypes'))
		#apps_list.append(apps.get_app_config('allauth'))
		apps_list.append(apps.get_app_config('exhibition'))
		#apps_list.append(apps.get_app_config('blog'))
		#apps_list.append(apps.get_app_config('ads'))
		#apps_list.append(apps.get_app_config('rating'))
		#apps_list.append(apps.get_app_config('thumbnail'))
		#apps_list.append(apps.get_app_config('watson'))
		for app_config in apps_list:
			print(f"Adding user permissions for {app_config}...")
			app_config.models_module = True
			create_permissions(app_config, apps=apps, verbosity=0)
			app_config.models_module = None

		print("DONE.")