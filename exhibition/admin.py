from os import path
#from django.conf import settings
#from django.shortcuts import get_object_or_404
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.template.loader	import render_to_string

from django_tabbed_changeform_admin.admin import DjangoTabbedChangeformAdmin
from sorl.thumbnail.admin import AdminImageMixin

# Exhibitors, Jury, Partners, Events, Nominations, Exhibitions, Portfolio, Image
from crm import models
from .models import *
from .forms import ExhibitionsForm, ImagesUploadForm, CustomClearableFileInput
from .logic import UploadFilename, ImageResize, delete_cached_fragment, SendEmailAsync
from rating.admin import RatingInline, ReviewInline

admin.site.unregister(User)  # нужно что бы снять с регистрации модель User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	prepopulated_fields = {"username": ('email',)} # adding name to slug field
	#form = CustomSignupForm
	#add_form = CustomSignupForm

	add_fieldsets = (
		(None, {
			'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email',),
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

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('persons','exhibitors')
		super().save_model(request, obj, form, change)


class JuryAdmin(PersonAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('logo', 'name', 'slug', 'excerpt', 'description', 'sort',),
		}),
	)
	list_display = ('logo_thumb', 'name', 'excerpt',)
	list_display_links = ('logo_thumb', 'name', )

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('persons','jury')
		super().save_model(request, obj, form, change)



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

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('index_page')
		super().save_model(request, obj, form, change)



class PartnersAdmin(PersonAdmin, ProfileAdmin):
	fieldsets = (
		(None, {
			'classes': ('person-block',),
			'fields': ('logo', 'name', 'slug', 'description',)
		}),
	) + ProfileAdmin.fieldsets

	list_display = ('logo_thumb', 'name', 'phone',)
	list_display_links = ('logo_thumb', 'name', 'phone',)

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('persons','partners')

		if change:
			exhibitions = Exhibitions.objects.filter(partners=obj).only('slug')
			for exhibition in exhibitions:
				delete_cached_fragment('exhibition_content', exhibition.slug)
		super().save_model(request, obj, form, change)


@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
	fields = ('title', 'slug', 'description', 'logo', 'sort',)
	list_display = ('logo_thumb', 'title', 'nominations_list', 'description',)
	list_display_links = ('logo_thumb', 'title',)

	def nominations_list(self, obj):
		return ', '.join(obj.nominations_set.all().values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('categories')
		super().save_model(request, obj, form, change)


class NominationsAdmin(admin.ModelAdmin):
	fields = ('category', 'title', 'slug', 'description', 'sort',)
	list_display = ('category', 'title', 'description_html',)
	list_display_links = ('title',)
	list_per_page = 20
	empty_value_display = '<пусто>'

	def description_html(self, obj):
		return format_html(obj.description)

	description_html.short_description = 'Описание'


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
	list_per_page = 20
	save_as = True
	ordering = ('-exhibition__slug','date_event','time_start',)
	#save_on_top = True # adding save button on top bar

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		delete_cached_fragment('exhibition_events', obj.exhibition.slug)



class WinnersAdmin(admin.ModelAdmin):
	list_display = ('exh_year', 'nomination', 'exhibitor','portfolio')
	list_display_links = list_display
	#search_fields = ('nomination__title', 'exhibitor__name',)
	list_filter = ('exhibition__date_start', 'nomination', 'exhibitor')
	date_hierarchy = 'exhibition__date_start'
	ordering = ('-exhibition__date_start',)

	list_per_page = 30
	save_as = True
	save_on_top = True # adding save button on top bar

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == "portfolio":
			query = Portfolio.objects.prefetch_related('nominations_for_exh').all()
			#print(db_field)

		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		delete_cached_fragment('persons', 'winners')




class ImagesInline(admin.StackedInline):
	model = Image
	template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 0 #new blank record count
	show_change_link = True
	fields = ('file_thumb', 'file', 'title', 'filename', 'sort',)
	list_display = ('file_thumb', 'title',)
	readonly_fields = ('file_thumb', 'filename',)
	list_editable = ['title','sort']

	formfield_overrides = {
		models.ImageField: {'widget': CustomClearableFileInput()},
	}


class ImageAdmin(AdminImageMixin, admin.ModelAdmin):
	fields = ('portfolio', 'title', 'description', 'file', 'sort')
	list_display = ('file_thumb', 'portfolio', 'title', 'author', 'sort',)
	list_display_links = ('file_thumb', 'portfolio', 'title',)
	list_filter = ('portfolio__owner', 'portfolio',)
	readonly_fields = ('file_thumb',)
	search_fields = ('title', 'portfolio__title', 'portfolio__owner__slug', 'portfolio__owner__name',)

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



@admin.register(PortfolioAttributes)
class PortfolioAttributesAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ('name',)} # adding name to slug field
	search_fields = ('name',)
	list_per_page = 30

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		for category in Categories.objects.all():
			delete_cached_fragment('sidebar', category.slug)



class PortfolioAdmin(admin.ModelAdmin):
	form = ImagesUploadForm
	list_display = ('owner', 'title', 'exhibition', 'nominations_list', 'attributes_list')
	list_display_links = ('owner', 'title')
	search_fields = ('title', 'owner__name', 'exhibition__title', 'nominations__title')
	list_filter = ('nominations__category', 'nominations', 'owner',)
	list_per_page = 30

	save_on_top = True # adding save button on top bar
	date_hierarchy = 'exhibition__date_start'
	save_as = True
	view_on_site = True
	inlines = [ImagesInline, RatingInline, ReviewInline]

	class Media:
		js = ['/static/js/files-upload.min.js']

	def nominations_list(self, obj):
		return ', '.join(obj.nominations.values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'
	nominations_list.admin_order_field = 'nominations__title'

	# def category(self, obj):
	# 	categories = obj.nominations.filter(category__isnull=False).values_list('category__title', flat=True)
	# 	if categories:
	# 		return ', '.join(categories)
	# 	else:
	# 		return '<без категории'
	# category.short_description = 'Категория'

	def attributes_list(self, obj):
		return ', '.join(obj.attributes.values_list('name', flat=True))
	attributes_list.short_description = 'Аттрибуты для фильтра'
	attributes_list.admin_order_field = 'attributes__group'

	def save_model(self, request, obj, form, change):
		#request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
		image_list = request.FILES.getlist('files')
		obj.save(image_list) # сохраним портфолио и связанные фотографии

		if (not change) and obj.images : # new portfolio with images
			protocol = 'https' if request.is_secure() else 'http'
			host_url = "{0}://{1}".format(protocol, request.get_host())

			# get list of image thumbs 100x100
			images = []
			size = '%sx%s' % (settings.ADMIN_THUMBNAIL_SIZE[0], settings.ADMIN_THUMBNAIL_SIZE[1])
			for im in obj.images.all():
				thumb = get_thumbnail(im.file, size, crop='center', quality=75)
				images.append(thumb)

			subject = 'Добавление портфолио на сайте Сфера Дизайна'
			template = render_to_string('exhibition/new_project_notification.html', {
				'project': obj,
				'host_url': host_url,
				'uploaded_images': images,
			})
			SendEmailAsync(subject, template, [obj.owner.user.email])

		delete_cached_fragment('portfolio', obj.id, True)
		delete_cached_fragment('portfolio', obj.id, False)
		delete_cached_fragment('portfolio_slider', obj.id)
		for nomination in obj.nominations.all():
			if nomination.category:
				delete_cached_fragment('projects', nomination.category.slug)


	# def delete_file(self, pk, request):
	# 	obj = get_object_or_404(Image, pk=pk)
	# 	return obj.delete()

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
	list_display_links = ('banner_thumb', 'title',)
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

		delete_cached_fragment('exhibition_header', obj.slug)
		delete_cached_fragment('exhibition_content', obj.slug)
		delete_cached_fragment('exhibition_events', obj.slug)
		delete_cached_fragment('exhibition_gallery', obj.slug)
		delete_cached_fragment('exhibition_overlay', obj.slug)

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

