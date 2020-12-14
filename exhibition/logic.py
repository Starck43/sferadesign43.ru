from django.conf import settings
from PIL import Image as Im
from io import BytesIO
from os import path, remove
from sys import getsizeof
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse
from django.template.loader	import render_to_string
from django.core.mail import EmailMessage, BadHeaderError

#from sorl.thumbnail import get_thumbnail, delete


DEFAULT_SIZE = getattr(settings, 'DJANGORESIZED_DEFAULT_SIZE', [1920, 1080])
DEFAULT_QUALITY = getattr(settings, 'DJANGORESIZED_DEFAULT_QUALITY', 80)
DEFAULT_KEEP_META = getattr(settings, 'DJANGORESIZED_DEFAULT_KEEP_META', True)



class MediaFileStorage(FileSystemStorage):

	# def get_available_name(self, name, max_length):
	# 	if self.exists(name):
	# 		remove(self.path(name))
	# 		#remove(os.path.join(settings.MEDIA_ROOT, name))
	# 	return name

	def save(self, name, content, max_length=None):
		if not self.exists(name):
			print('storage: new file '+name)
			return super().save(name, content, max_length)
		else:
			print('storage: exist file '+name)
			# prevent saving file on disk
			return name



def UploadFilename(instance, filename):
	# file will be uploaded to MEDIA_ROOT/uploads/<author>/<porfolio>/<filename>
	#basename, ext = os.path.splitext(filename)
	#return os.path.join('uploads/', instance.portfolio.owner.slug.lower(), instance.portfolio.slug, filename)
	return 'uploads/{0}/{1}/{2}/{3}'.format(instance.portfolio.owner.slug.lower(), instance.portfolio.exhibition.slug, instance.portfolio.slug, filename)


def GalleryUploadTo(instance, filename):
	return 'gallery/{0}/{1}'.format(instance.exhibition.slug.lower(), filename)


def ImageResize(obj):
	if (obj.width > DEFAULT_SIZE[0] or obj.height > DEFAULT_SIZE[1]):
		if path.exists(obj.path):
			image = Im.open(obj.path)
		else:
			image = Im.open(obj)

		if image.mode != 'RGB':
			image = image.convert('RGB')

		#image = image.resize(DEFAULT_SIZE, Im.ANTIALIAS)
		image.thumbnail(DEFAULT_SIZE, Im.ANTIALIAS)

		meta = image.info
		if not DEFAULT_KEEP_META:
			meta.pop('exif', None)
		output = BytesIO()
		image.save(output, format='JPEG', quality=DEFAULT_QUALITY, **meta)
		output.seek(0)
		file = InMemoryUploadedFile(output, 'ImageField', obj.name, 'image/jpeg', getsizeof(output), None)
		#obj = File(output.getvalue())
		if file:
			if path.exists(obj.path):
				with open(obj.path, 'wb+') as f:
					for chunk in file.chunks():
						f.write(chunk)
				return None
		else:
			return obj

		return file
	else:
		# Nothing to compress
		return None



""" Return True if the request comes from a mobile device """
def IsMobile(request):
	import re

	MOBILE_AGENT_RE=re.compile(r".*(iphone|mobile|androidtouch)",re.IGNORECASE)

	if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
		return True
	else:
		return False


def SendEmail(data):
	print(settings.EMAIL_HOST_USER)
	print(settings.EMAIL_RICIPIENTS)
	template = render_to_string('contacts/confirm_email.html', {
		'name':data['name'],
		'email':data['from_email'],
		'message':data['message'],
	})
	email = EmailMessage(
		'Новое сообщение с сайта!',
		template,
		settings.EMAIL_HOST_USER,
		settings.EMAIL_RICIPIENTS,

	)
	email.content_subtype = "html"
	email.html_message = True
	email.fail_silently=False

	try:
		email.send()
	except BadHeaderError:
		return HttpResponse('Ошибка в заголовке письма!')
	return True

