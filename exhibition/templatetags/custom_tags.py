import re
import unicodedata
import hashlib
import threading

from os import path
from django.conf import settings


from django import template
register = template.Library()


@register.filter
def verbose_name(obj):
	return obj._meta.verbose_name


@register.filter
def verbose_name_plural(obj):
	return obj._meta.verbose_name_plural


@register.filter
def file_exists(obj):
	return True if path.exists(obj.path) else False


@register.filter
def filename(obj):
	return obj.rsplit('/', 1)[-1]


@register.filter
def to_string(obj):
	return " ".join(obj)


@register.filter
def admin_change_url(model, app="exhibition"):
	return 'admin:%s_%s_change' % (app, model)


@register.filter
def decode_emoji(obj):
	return re.sub(r':([^a-z]+?):', lambda y: unicodedata.lookup(y.group(1)), obj)


#return unique query list
@register.filter
def distinct(items, attr_name):
	return set([getattr(i, attr_name) for i in items])


@register.filter
def count_range(value, start_index=0):
	return range(start_index, value+start_index)


class UrlCache(object):
	_md5_sum = {}
	_lock = threading.Lock()

	@classmethod
	def get_md5(cls, file):
		try:
			return cls._md5_sum[file]
		except KeyError:
			with cls._lock:
				try:
					if settings.DEBUG:
						filepath = settings.STATICFILES_DIRS[0]
					else:
						filepath = settings.STATIC_ROOT

					md5 = cls.calc_md5(path.join(filepath, file))[:8]
					value = '%s%s?v=%s' % (settings.STATIC_URL, file, md5)
				except IsADirectoryError:
					value = settings.STATIC_URL + file
				cls._md5_sum[file] = value
				return value

	@classmethod
	def calc_md5(cls, file_path):
		with open(file_path, 'rb') as fh:
			m = hashlib.md5()
			while True:
				data = fh.read(8192)
				if not data:
					break
				m.update(data)
			return m.hexdigest()


@register.simple_tag
def md5url(model_object):
	return UrlCache.get_md5(model_object)



@register.filter('input_type')
def input_type(ob):
	'''
	Extract form field type
	:param ob: form field
	:return: string of form field widget type
	'''
	return ob.field.widget.__class__.__name__


@register.filter(name='add_classes')
def add_classes(value, arg):
	'''
	Add provided classes to form field
	:param value: form field
	:param arg: string of classes seperated by ' '
	:return: edited field
	'''
	css_classes = value.field.widget.attrs.get('class', '')
	# check if class is set or empty and split its content to list (or init list)
	if css_classes:
		css_classes = css_classes.split(' ')
	else:
		css_classes = []
	# prepare new classes to list
	args = arg.split(' ')
	for a in args:
		if a not in css_classes:
			css_classes.append(a)
	# join back to single string
	return value.as_widget(attrs={'class': ' '.join(css_classes)})


