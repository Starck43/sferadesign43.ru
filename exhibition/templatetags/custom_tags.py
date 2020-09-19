
from django import template
register = template.Library()


@register.filter
def verbose_name(obj):
	return obj._meta.verbose_name


@register.filter
def verbose_name_plural(obj):
	return obj._meta.verbose_name_plural


@register.filter
def to_string(obj):
	return " ".join(obj)