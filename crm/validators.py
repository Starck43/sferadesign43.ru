import os
import xml.etree.ElementTree as ET
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class SVGValidator:
	def __call__(self, value):
		# Проверяем расширение файла
		ext = os.path.splitext(value.name)[1].lower()
		if ext != '.svg':
			raise ValidationError('Разрешены только SVG файлы')

		# Проверяем содержимое файла
		try:
			value.file.seek(0)
			tree = ET.parse(value.file)
			root = tree.getroot()
			if root.tag != '{http://www.w3.org/2000/svg}svg':
				raise ValidationError('Файл не является валидным SVG')
			value.file.seek(0)  # Возвращаем указатель
		except ET.ParseError:
			raise ValidationError('Некорректный XML в SVG файле')


svg_validator = SVGValidator()
