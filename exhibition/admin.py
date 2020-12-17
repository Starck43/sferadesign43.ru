from os import path
#from django.conf import settings
#from django.shortcuts import get_object_or_404
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from django_tabbed_changeform_admin.admin import DjangoTabbedChangeformAdmin
from sorl.thumbnail.admin import AdminImageMixin
from multiupload.admin import MultiUploadAdmin

# Exhibitors, Jury, Partners, Events, Nominations, Exhibitions, Portfolio, Image
from crm import models
from .models import *
from .forms import ExhibitionsForm, ImagesUploadForm, CustomClearableFileInput
from .logic import UploadFilename, ImageResize

from django.utils.html import format_html

admin.site.unregister(User)  # нужно что бы снять с регистрации модель User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
	prepopulated_fields = {"username": ('email',)} # adding name to slug field
	#add_form = PersonUserForm

	add_fieldsets = (
		(None, {
			'fields': ('first_name', 'last_name', 'email','username','password1', 'password2'),
			}),
		('Права доступа', {
			'fields': ('is_active', 'groups','date_joined', 'last_login',),
			}),
		)


class PersonAdmin(admin.ModelAdmin):
	model = Person

	fieldsets = (
		(None, {
			'classes': ('person-block',),
			'fields': ( ('logo', ), 'name', 'slug', 'description', 'sort', )
		}),
	)
	prepopulated_fields = {"slug": ('name',)} # adding name to slug field
	list_display = ('logo_thumb', 'name', 'description',)
	search_fields = ('name', 'slug', 'description',)
	list_display_links = ('logo_thumb', 'name',)
	list_per_page = 20
	#summernote_fields = ('description',) # Fields name of Models for using WYSIWYG editor instead of plain text


class ProfileAdmin(admin.ModelAdmin):
	model = Profile

	fieldsets = (
		('Профиль', {
			'classes': ('profile-block',),
			'fields': ('address', 'phone', 'email', 'site', 'vk', 'fb', 'instagram',)
		}),
	)
	list_display = ('phone',)


class ExhibitorsAdmin(PersonAdmin, ProfileAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'fields': ('user',)
		}),
	) + PersonAdmin.fieldsets + ProfileAdmin.fieldsets
	#prepopulated_fields = {"slug": ('name',)} # adding name to slug field

	list_display = ('logo_thumb', 'name', 'user_name',)
	search_fields = PersonAdmin.search_fields #+ ('user',)
	#list_editable = ['user']
	#add_form = PersonUserForm

	def user_name(self, obj):
		if not obj.user:
			return None

		if (not obj.user.first_name) and (not obj.user.last_name) :
			return obj.user.username
		else:
			return "%s %s" % (obj.user.first_name, obj.user.last_name)
	user_name.short_description = 'Пользователь'


class JuryAdmin(PersonAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('logo', 'name', 'slug', 'excerpt', 'description', 'sort',),
		}),
	)
	list_display = ('logo_thumb', 'name', 'excerpt',)
	list_display_links = ('logo_thumb', 'name', )


class OrganizerAdmin(PersonAdmin, ProfileAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('logo', 'user', 'name', 'slug', 'description', 'sort',),
		}),
	) + ProfileAdmin.fieldsets
	list_display = ('logo_thumb', 'name', 'description_html',)
	list_display_links = ('logo_thumb', 'name', )
	ordering = ('sort',)

	def description_html(self, obj):
		return format_html(obj.description)

	description_html.short_description = 'Описание для главной страницы'


class PartnersAdmin(PersonAdmin, ProfileAdmin):
	fieldsets = (
		(None, {
			'classes': ('person-block',),
			'fields': ('logo', 'name', 'slug', 'description',)
		}),
	) + ProfileAdmin.fieldsets

	list_display = ('logo_thumb', 'name', 'phone',)
	list_display_links = ('logo_thumb', 'name', 'phone',)


@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
	fields = ('title', 'slug', 'description', 'logo', 'sort',)
	list_display = ('logo_thumb', 'title', 'nominations_list', 'description',)
	list_display_links = ('logo_thumb', 'title',)

	def nominations_list(self, obj):
		return ', '.join(obj.nominations_set.all().values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'


class NominationsAdmin(admin.ModelAdmin):
	fields = ('category', 'title', 'slug', 'description', 'sort',)
	list_display = ('category', 'title', 'description',)
	list_display_links = ('title',)
	list_per_page = 20
	empty_value_display = '<пусто>'


class EventsInlineAdmin(admin.StackedInline):
	model = Events
	extra = 1 #new blank record count
	fields = ('title', 'date_event', 'time_start', 'time_end', 'lector',)
	classes = ['events-inline-tab',]
	#save_on_top = True # adding save button on top bar
	verbose_name_plural = ""

class EventsAdmin(admin.ModelAdmin):
	list_display = ('title', 'date_event', 'time_event', 'hoster', 'exhibition',)
	search_fields = ('title', 'description', 'hoster', 'lector',)
	list_filter = ('exhibition__date_start', 'date_event',)
	date_hierarchy = 'exhibition__date_start'
	#summernote_fields = ('description',) # Fields name of Models for using WYSIWYG editor instead of plain text
	list_per_page = 20

	save_as = True
	#save_on_top = True # adding save button on top bar


class WinnersAdmin(admin.ModelAdmin):
	list_display = ('exh_year', 'nomination', 'exhibitor',)
	list_display_links = list_display
	#search_fields = ('nomination__title', 'exhibitor__name',)
	list_filter = ('exhibition__date_start', 'nomination', 'exhibitor')
	date_hierarchy = 'exhibition__date_start'

	list_per_page = 30
	save_as = True
	save_on_top = True # adding save button on top bar

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == "portfolio":
			query = Portfolio.objects.prefetch_related('nominations_for_exh').all()
			print(db_field)

		return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GalleryMultiuploadMixing(object):

	def process_uploaded_file(self, uploaded, portfolio, request):
		title = request.POST['title'] or path.splitext(uploaded.name)[0]

		if portfolio:
			image = portfolio.images.create(file=uploaded, title=title)  # images - related name for Image model
		else:
			image = Image.objects.create(file=uploaded, portfolio=None, title=title)

		return {
			'url': image.file.url,
			'thumbnail_url': image.file.url,
			'id': image.id,
			'name': title,
		}


class ImageInlineAdmin(admin.StackedInline):
	model = Image
	template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 0 #new blank record count
	show_change_link = True
	fields = ('file_thumb', 'file', 'title', 'filename',)
	list_display = ('file_thumb', 'title',)
	readonly_fields = ('file_thumb', 'filename',)
	list_editable = ['title']

	formfield_overrides = {
		models.ImageField: {'widget': CustomClearableFileInput()},
	}

class ImageAdmin(AdminImageMixin, admin.ModelAdmin):
	fields = ('portfolio', 'title', 'description', 'file',)
	list_display = ('file_thumb', 'author', 'portfolio', 'title',)
	list_display_link = list_display
	list_filter = ('portfolio__owner', 'portfolio',)
	readonly_fields = ('file_thumb',)

	list_per_page = 30
	# def save_model(self, request, obj, form, change):
	# 	obj.save()
	# 	for image in request.FILES.getlist('images'):
	# 		obj.create(image=image)

	def author(self, obj):
		author = None
		if obj.portfolio:
			author = obj.portfolio.owner
		return author
	author.short_description = 'Автор'


class PortfolioAdmin(GalleryMultiuploadMixing, admin.ModelAdmin):
	form = ImagesUploadForm
	list_display = ('exhibition', 'owner', 'title', 'nominations_list')
	search_fields = ('title', 'owner__name', 'exhibition__title', 'nominations__title')
	list_filter = ('nominations', 'owner',)
	list_per_page = 30

	save_on_top = True # adding save button on top bar
	date_hierarchy = 'exhibition__date_start'
	save_as = True
	view_on_site = True
	inlines = [ImageInlineAdmin,]


	def nominations_list(self, obj):
		return ', '.join(obj.nominations.values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'
	nominations_list.admin_order_field = 'nominations__title'

	# def delete_file(self, pk, request):
	# 	obj = get_object_or_404(Image, pk=pk)
	# 	return obj.delete()

	def save_model(self, request, obj, form, change):
		#request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
		obj.save(request.FILES.getlist('files'))


	# def clean_file(self):
	# 	files = self.cleaned_data['file']
	# 	print(files)
	# 	raise ValidationError('File already exists')
	# 	if path.isfile(file_path):
	# 		raise ValidationError('File already exists')
	# 		return self.cleaned_data

	# def formfield_for_manytomany(self, db_field, request, **kwargs):
	# 	if db_field.name == "nominations":
	# 		kwargs["queryset"] = Nominations.objects.filter(pk=request.id)
	# 	return super().formfield_for_manytomany(db_field, request, **kwargs)




class GalleryInlineAdmin(admin.StackedInline):
	model = Gallery
	template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 0 #new blank record count
	show_change_link = True
	fields = ('file_thumb', 'file', 'title', 'filename',)
	list_display = ('file_thumb', 'title',)
	readonly_fields = ('file_thumb', 'filename',)
	list_editable = ['title']
	classes = ['gallery-inline-tab',]
	verbose_name_plural = ""
	list_per_page = 30

	formfield_overrides = {
		models.ImageField: {'widget': CustomClearableFileInput()},
	}


@admin.register(Gallery)
class GalleryAdmin(AdminImageMixin, admin.ModelAdmin):
	fields = ('exhibition', 'title', 'file',)
	list_display = ('file_thumb', 'exhibition', 'title',)
	list_display_links = list_display
	search_fields = ('title', 'exhibition__title', 'exhibition__slug',)
	list_filter = ('exhibition__date_start',)
	date_hierarchy = 'exhibition__date_start'
	list_per_page = 30

	readonly_fields = ('file_thumb',)
	save_on_top = True # adding save button on top bar



@admin.register(Exhibitions)
class ExhibitionsAdmin(DjangoTabbedChangeformAdmin, admin.ModelAdmin):
	form = ExhibitionsForm
	list_display = ('banner_thumb', 'title', 'date_start', 'date_end', )
	date_hierarchy = 'date_start'
	filter_horizontal = ('nominations', 'exhibitors',)
	#list_select_related = ('events',)
	# prepopulated_fields = {"slug": ('date_start',)} # adding name to slug field but not only DateFields
	save_on_top = True # adding save button on top bar
	list_per_page = 30
	view_on_site = True

	inlines = [EventsInlineAdmin, GalleryInlineAdmin,]

	fieldsets = (
		(None, {
			'classes': ('basic-tab',),
			'fields' : ('title', 'slug', 'banner', 'description', 'date_start', 'date_end', 'location',)
		}),
		(None, {
			'classes': ('exhibitors-tab','hidden-label',),
			'fields' : ('exhibitors',)
		}),
		(None, {
			'classes': ('nominations-tab','hidden-label',),
			'fields' : ('nominations',)
		}),
		(None, {
			'classes': ('jury-tab','hidden-label',),
			'fields' : ('jury',)
		}),
		(None, {
			'classes': ('partners-tab','hidden-label',),
			'fields' : ('partners',)
		}),
		(None, {
			'classes': ('files-upload-tab', 'hidden-label',),
			'fields' : ('files',)
		}),
	)

	tabs = (
		("Общая информация", ['basic-tab']),
		("Участники", ['exhibitors-tab']),
		("Номинации", ['nominations-tab']),
		("Жюри", ['jury-tab']),
		("Партнеры", ['partners-tab']),
		("Мероприятия", ['events-inline-tab']),
		("Фоторепортаж", ['files-upload-tab', 'gallery-inline-tab']),
	)
	#summernote_fields = ('description',) # Fields name of Models for using WYSIWYG editor instead of plain text

	def save_model(self, request, obj, form, change):
		# сохраним связанные с выставкой фото
		images = request.FILES.getlist('files')
		for image in images:
			upload_filename = path.join('gallery/', obj.slug, image.name)
			file_path = path.join(settings.MEDIA_ROOT,upload_filename)

			instance = Gallery(exhibition=obj, file=image)

			instance.save()

		obj.save()

	# def get_form(self, request, obj=None, **kwargs):
	# 	form = super().get_form(request, obj, **kwargs)
	# 	form.base_fields["exhibitors"].widget = forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
	# 	form.base_fields["partners"].widget = forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
	# 	form.base_fields["jury"].widget = forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
	# 	form.base_fields["nominations"].widget = forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
	# 	#form.base_fields["exhibitors"].label = ""
	# 	return form

@admin.register(MetaSEO)
class MetaAdmin(admin.ModelAdmin):
	fields = ('page', 'description', 'keywords',)
	list_display = fields


admin.site.register(Exhibitors, ExhibitorsAdmin)
admin.site.register(Jury, JuryAdmin)
admin.site.register(Partners, PartnersAdmin)
admin.site.register(Organizer, OrganizerAdmin)

admin.site.register(Nominations, NominationsAdmin)
admin.site.register(Events, EventsAdmin)
admin.site.register(Winners, WinnersAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(Image, ImageAdmin)

#admin.site.register(Exhibitions, ExhibitionsAdmin)

