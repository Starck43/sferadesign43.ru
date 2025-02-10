import logging
import re
import unicodedata

from threading import Thread
from PIL import ImageFile, Image as Im
from io import BytesIO
from os import path, remove
from sys import getsizeof

import PIL
from PIL import Image as PILImage, ImageOps
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import EmailMessage, BadHeaderError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.forms.widgets import ClearableFileInput
from django.contrib.auth.models import Group  # ,User

from sorl.thumbnail import get_thumbnail
from uuslug import slugify

ImageFile.LOAD_TRUNCATED_IMAGES = True

DEFAULT_SIZE = getattr(settings, 'DJANGORESIZED_DEFAULT_SIZE', [1500, 1024])
DEFAULT_QUALITY = getattr(settings, 'DJANGORESIZED_DEFAULT_QUALITY', 85)
DEFAULT_KEEP_META = getattr(settings, 'DJANGORESIZED_DEFAULT_KEEP_META', False)


def get_image_html(obj):
	# if path.isfile(os.path.join(settings.MEDIA_ROOT,obj.name)):
	if obj and path.isfile(path.join(settings.MEDIA_ROOT, obj.name)):
		size = '%sx%s' % (settings.ADMIN_THUMBNAIL_SIZE[0], settings.ADMIN_THUMBNAIL_SIZE[1])
		thumb = get_thumbnail(obj.name, size, crop='center', quality=settings.ADMIN_THUMBNAIL_QUALITY)
		return format_html('<img src="{0}" width="50"/>', thumb.url)
	else:
		return format_html('<img src="/media/no-image.png" width="50"/>')


class MediaFileStorage(FileSystemStorage):

	def get_valid_name(self, name):
		filename, ext = path.splitext(name)
		name = slugify(filename) + ext.lower()
		return super().get_valid_name(name)

	def save(self, name, content, max_length=None):
		if not self.exists(name):
			return super().save(name, content, max_length)
		else:
			# prevent saving file on disk
			return name


def designers_upload_to(instance, filename):
	""" Designer files will be uploaded to MEDIA_ROOT/uploads/<author>/<filename> """
	return '{0}{1}/{2}'.format(
		settings.FILES_UPLOAD_FOLDER,
		instance.owner.slug.lower(),
		filename
	)


def portfolio_upload_to(instance, filename):
	""" portfolio files will be uploaded to MEDIA_ROOT/uploads/<author>/<exhibition>/<porfolio>/<filename> """
	exhibition_slug = instance.portfolio.exhibition.slug if instance.portfolio.exhibition else 'non-exhibition'
	return '{0}{1}/{2}/{3}/{4}'.format(
		settings.FILES_UPLOAD_FOLDER,
		instance.portfolio.owner.slug.lower(),
		exhibition_slug,
		instance.portfolio.slug,
		filename
	)


def cover_upload_to(instance, filename):
	""" portfolio cover will be uploaded to MEDIA_ROOT/uploads/<author>/<exhibition>/<porfolio>/<filename> """
	exhibition_slug = instance.exhibition.slug if instance.exhibition else 'non-exhibition'
	return '{0}{1}/{2}/{3}/{4}'.format(
		settings.FILES_UPLOAD_FOLDER,
		instance.owner.slug.lower(),
		exhibition_slug,
		instance.slug,
		filename
	)


def gallery_upload_to(instance, filename):
	""" gallery files will be uploaded to MEDIA_ROOT/gallery/<exh_year>/<filename> """
	return 'gallery/{0}/{1}'.format(instance.exhibition.slug.lower(), filename)


def image_resize(obj, size=None, uploaded_file=None):
	""" Adjusting image size before saving """
	if not obj:
		return

	if not size:
		size = DEFAULT_SIZE

	filename, ext = path.splitext(obj.name)

	if ext.lower() != '.webp' or (obj.width > size[0] or obj.height > size[1] or uploaded_file):
		try:
			fn = obj.path if path.exists(obj.path) else obj
			image = Im.open(fn)

			content_type = 'image/webp'
			image_format = 'WEBP'
			ext = '.webp'

			if int(PIL.__version__.split('.')[0]) < 10:
				image.thumbnail(size, Im.ANTIALIAS)
			else:
				image = ImageOps.contain(image, size, method=PILImage.Resampling.LANCZOS)

			output = BytesIO()
			image.save(output, format=image_format, quality=DEFAULT_QUALITY)
			output.seek(0)

			file = InMemoryUploadedFile(
				file=output,
				field_name='ImageField',
				name=filename + ext,
				content_type=content_type,
				size=getsizeof(output),
				charset=None
			)

			if file:
				if path.exists(obj.path):
					with open(obj.path, 'wb+') as f:
						for chunk in file.chunks():
							f.write(chunk)
					return None
				return file
			return obj
		except IOError as e:
			logging.error('Ошибка открытия файла %s!' % e)
			raise ValidationError('Ошибка открытия файла %s!' % e)
	# return 'error'
	else:
		# Nothing to compress
		return None


def limit_file_size(file):
	""" Image file size validator """
	limit = settings.FILE_UPLOAD_MAX_MEMORY_SIZE if hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE') else 2.5 * 1024 * 1024
	if path.exists(file.path) and file.size > limit:
		raise ValidationError(
			'Размер файла превышает лимит %s Мб. Рекомендуемый размер фото 1500x1024 пикс.' % (limit / (1024 * 1024))
		)


class CustomClearableFileInput(ClearableFileInput):
	template_name = 'admin/exhibition/widgets/file_input.html'


def SendEmail(subject, template, email_ricipients=settings.EMAIL_RECIPIENTS):
	""" Sending email """
	email = EmailMessage(
		subject,
		template,
		settings.EMAIL_HOST_USER,
		email_ricipients,
	)

	email.content_subtype = "html"
	email.html_message = True
	email.fail_silently = False

	try:
		email.send()
	except BadHeaderError:
		return HttpResponse('Ошибка в заголовке письма!')

	return True


class EmailThread(Thread):
	""" Async email sending class """
	def __init__(self, subject, template, email_ricipients):
		self.subject = subject
		self.html_content = template
		self.recipient_list = email_ricipients
		Thread.__init__(self)

	def run(self):
		return SendEmail(self.subject, self.html_content, self.recipient_list)


def SendEmailAsync(subject, template, email_ricipients=settings.EMAIL_RECIPIENTS):
	""" Sending email to recipients """
	EmailThread(subject, template, email_ricipients).start()


def portfolio_upload_confirmation(images, request, obj):
	""" Отправим сообщение автору портфолио с уведомлением о добавлении фото """
	if images and obj.owner.user and obj.owner.user.email:  # new portfolio with images
		protocol = 'https' if request.is_secure() else 'http'
		host_url = "{0}://{1}".format(protocol, request.get_host())

		# Before email notification we need to get a list of uploaded thumbs [100x100]
		uploaded_images = []
		size = '%sx%s' % (settings.ADMIN_THUMBNAIL_SIZE[0], settings.ADMIN_THUMBNAIL_SIZE[1])
		for im in images:
			image = path.join(settings.FILES_UPLOAD_FOLDER, obj.owner.slug, obj.exhibition.slug, obj.slug, im.name)
			thumb = get_thumbnail(image, size, crop='center', quality=settings.ADMIN_THUMBNAIL_QUALITY)
			uploaded_images.append(thumb)

		subject = 'Добавление фотографий на сайте Сфера Дизайна'
		template = render_to_string('exhibition/new_project_notification.html', {
			'project': obj,
			'host_url': host_url,
			'uploaded_images': uploaded_images,
		})
		SendEmailAsync(subject, template, [obj.owner.user.email])


def set_user_group(request, user):
	""" Set User group on SignupForm via account/social account"""

	is_exhibitor = request.POST.get('exhibitor', False)
	if is_exhibitor == 'on':
		group_name = "Exhibitors"
	else:
		group_name = "Members"

	try:
		group = Group.objects.get(name=group_name)
		user.groups.add(group)
		user.save()
	except Group.DoesNotExist:
		pass

	return user


def IsMobile(request):
	""" Return True if the request comes from a mobile device """
	import re

	agent = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)

	if agent.match(request.META['HTTP_USER_AGENT']):
		return True
	else:
		return False


def delete_cached_fragment(fragment_name, *args):
	""" Reset cache """
	key = make_template_fragment_key(fragment_name, args or None)
	cache.delete(key)
	return key


def unicode_emoji(data, direction='encode'):
	""" Encoding/decoding emoji in string data """
	if data:
		if direction == 'encode':
			emoji_pattern = re.compile(
				u"["
				u"\u2600-\u26FF"  # Unicode Block 'Miscellaneous Symbols'
				u"\U0001F600-\U0001F64F"  # emoticons
				u"\U0001F300-\U0001F5FF"  # symbols & pictographs
				u"\U0001F680-\U0001F6FF"  # transport & map symbols
				u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
				"]",
				flags=re.UNICODE
			)

			return re.sub(emoji_pattern, lambda y: ':' + unicodedata.name(y.group(0)) + ':', data)
		elif direction == 'decode':
			return re.sub(r':([^a-z]+?):', lambda y: unicodedata.lookup(y.group(1)), data)
		else:
			return data
	else:
		return ''


def update_google_sitemap():
	...
