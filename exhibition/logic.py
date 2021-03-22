import re
import unicodedata

from django.conf import settings
from threading import Thread
from PIL import Image as Im
from io import BytesIO
from os import path, remove
from sys import getsizeof

from django.http import HttpResponse
from django.core.mail import EmailMessage, BadHeaderError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

#from sorl.thumbnail import get_thumbnail, delete

from django.contrib.auth.models import Group #,User


DEFAULT_SIZE = getattr(settings, 'DJANGORESIZED_DEFAULT_SIZE', [1500, 1024])
DEFAULT_QUALITY = getattr(settings, 'DJANGORESIZED_DEFAULT_QUALITY', 85)
DEFAULT_KEEP_META = getattr(settings, 'DJANGORESIZED_DEFAULT_KEEP_META', False)



class MediaFileStorage(FileSystemStorage):

	# def get_available_name(self, name, max_length):
	# 	if self.exists(name):
	# 		remove(self.path(name))
	# 		#remove(os.path.join(settings.MEDIA_ROOT, name))
	# 	return name

	def save(self, name, content, max_length=None):
		if not self.exists(name):
			#print('storage: new file '+name)
			return super().save(name, content, max_length)
		else:
			#print('storage: exist file '+name)
			# prevent saving file on disk
			return name



def UploadFilename(instance, filename):
	# file will be uploaded to MEDIA_ROOT/uploads/<author>/<porfolio>/<filename>
	return 'uploads/{0}/{1}/{2}/{3}'.format(
		instance.portfolio.owner.slug.lower(),
		instance.portfolio.exhibition.slug,
		instance.portfolio.slug,
		filename
	)


def GalleryUploadTo(instance, filename):
	return 'gallery/{0}/{1}'.format(instance.exhibition.slug.lower(), filename)


""" Adjusting image size before saving """
def ImageResize(obj):
	filename, ext = path.splitext(obj.name)
	if obj.width > DEFAULT_SIZE[0] or obj.height > DEFAULT_SIZE[1] or ext.upper() == '.PNG' :
		try :
			fn = obj.path if path.exists(obj.path) else obj
			image = Im.open(fn)

			if image.mode != 'RGB':
				image = image.convert('RGB')

			#image = image.resize(DEFAULT_SIZE, Im.ANTIALIAS)
			image.thumbnail(DEFAULT_SIZE, Im.ANTIALIAS)

			meta = image.info
			if not DEFAULT_KEEP_META:
				meta.pop('exif', None)
			output = BytesIO()
			image.save(output, format='JPEG', quality=DEFAULT_QUALITY, optimize=True, **meta)
			output.seek(0)
			file = InMemoryUploadedFile(output, 'ImageField', filename + '.jpg', 'image/jpeg', getsizeof(output), None)
			if file:
				if path.exists(obj.path):
					with open(obj.path, 'wb+') as f:
						for chunk in file.chunks():
							f.write(chunk)
					return None
			else:
				return obj

			return file
		except IOError:
			return HttpResponse('Ошибка открытия файла %s!' % fn)
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


""" Sending email """
def SendEmail(subject, template, email_ricipients=settings.EMAIL_RICIPIENTS):
	email = EmailMessage(
		subject,
		template,
		settings.EMAIL_HOST_USER,
		email_ricipients,
	)

	email.content_subtype = "html"
	email.html_message = True
	email.fail_silently=False

	try:
		email.send()
	except BadHeaderError:
		return HttpResponse('Ошибка в заголовке письма!')

	return True

""" Acync email sending """
class EmailThread(Thread):
	def __init__(self, subject, template, email_ricipients):
		self.subject = subject
		self.html_content = template
		self.recipient_list = email_ricipients
		Thread.__init__(self)

	def run(self):
		return SendEmail(self.subject, self.html_content, self.recipient_list)


""" Sending email to recipients """
def SendEmailAsync(subject, template, email_ricipients):
	EmailThread(subject, template, email_ricipients).start()


""" Set User group on SignupForm via account/social account"""
def SetUserGroup(request, user):

	is_exhibitor = request.POST.get('exhibitor',False)
	if is_exhibitor == 'on':
		group_name = "Exhibitors"
	else:
		group_name = "Members"

	try:
		group = Group.objects.get(name=group_name)
		user.groups.add(group)
		#print(group_name)
		user.save()
	except Group.DoesNotExist:
		pass

	return user


""" Reset cache """
def delete_cached_fragment(fragment_name, *args):
	#print(args)
	key = make_template_fragment_key(fragment_name, args or None)
	cache.delete(key)
	return key

""" Encoding/decoding emoji in string data """
def unicode_emoji(data, direction='encode'):
	if data:
		if direction == 'encode':
			emoji_pattern = re.compile(u"["
				u"\u2600-\u26FF"  			# Unicode Block 'Miscellaneous Symbols'
				u"\U0001F600-\U0001F64F"	# emoticons
				u"\U0001F300-\U0001F5FF"	# symbols & pictographs
				u"\U0001F680-\U0001F6FF"	# transport & map symbols
				u"\U0001F1E0-\U0001F1FF"	# flags (iOS)
			"]", flags= re.UNICODE)

			return re.sub(emoji_pattern, lambda y: ':'+unicodedata.name(y.group(0))+':', data)
		elif direction == 'decode':
				return re.sub(r':([^a-z]+?):', lambda y: unicodedata.lookup(y.group(1)), data)
		else:
			return data
	else:
		return ''



def update_google_sitemap():
	try:
		ping_google() #сообщим Google о изменениях в sitemap.xml
	except Exception:
		pass


