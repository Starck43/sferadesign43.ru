from os import path
#from django.conf import settings
#from django.shortcuts import get_object_or_404
from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.template.loader	import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.forms.widgets import Select
from functools import partial

from django_tabbed_changeform_admin.admin import DjangoTabbedChangeformAdmin
from sorl.thumbnail.admin import AdminImageMixin

# Exhibitors, Jury, Partners, Events, Nominations, Exhibitions, Portfolio, Image
from crm import models
from .models import *
from blog.models import Article

from .forms import ExhibitionsForm, PortfolioForm, ImageForm, MetaSeoFieldsForm
from .logic import delete_cached_fragment, PortfolioUploadConfirmation, CustomClearableFileInput
from rating.admin import RatingInline, ReviewInline


admin.site.unregister(User)  # нужно что бы снять с регистрации модель User


# Creating a model's sort function for admin
def get_app_list(self, request):
	ordered_models = [
		('exhibition', [
			'Portfolio',
			'Image',
			'Gallery',
			'Categories',
			'Nominations',
			'Exhibitors',
			'Organizer',
			'Partners',
			'Jury',
			'Exhibitions',
			'Events',
			'Winners',
			'PortfolioAttributes',
			'MetaSEO'
		])
	]
	app_dict = self._build_app_dict(request)

	for app_name, object_list in ordered_models:
		app = app_dict.get(app_name, None)
		if app:
			app['models'].sort(key=lambda x: object_list.index(x['object_name']))
		#yield app

	return sorted(app_dict.values(), key=lambda x: x['name'].lower())

admin.AdminSite.get_app_list = get_app_list



class MetaSeoFieldsAdmin:
	form = MetaSeoFieldsForm

	meta_fields = ('meta_title', 'meta_description', 'meta_keywords')
	fieldsets = (
		('СЕО', {
			'classes': ('meta-block',),
			'fields': meta_fields
		}),
	)

	# def get_form(self, request, obj=None, **kwargs):
	# 	form = super().get_form(request, obj, **kwargs)
	# 	return form

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		if obj.pk and not change and form.changed_data:
			MetaSEO.objects.create(
				model=form.meta_model,
				post_id=obj.pk,
				title=form.cleaned_data['meta_title'],
				description=form.cleaned_data['meta_description'],
				keywords=form.cleaned_data['meta_keywords'],
			)



@admin.register(User)
class UserAdmin(BaseUserAdmin):
	prepopulated_fields = {"username": ('email',)}
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
			'fields': ( 'user', ( 'logo', ), 'name', 'slug', 'description', 'sort', )
		}),
	)
	prepopulated_fields = {"slug": ('name',)} # adding name to slug field
	list_display = ('logo_thumb', 'name', 'description',)
	search_fields = ('name', 'slug', 'description',)
	list_display_links = ('logo_thumb', 'name',)
	list_per_page = 20

	def save_model(self, request, obj, form, change):
		if change and obj.user:
			articles = Article.objects.filter(owner=obj.user)
			for article in articles:
				delete_cached_fragment('article', article.id)
		delete_cached_fragment('articles')
		obj.save(request)



class ProfileAdmin(admin.ModelAdmin):
	model = Profile

	fieldsets = (
		('Профиль', {
			'classes': ('profile-block',),
			'fields': ('address', 'phone', 'email', 'site', 'vk', 'fb', 'instagram',)
		}),
	)
	list_display = ('phone',)


class ExhibitorsAdmin(PersonAdmin, ProfileAdmin, MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = PersonAdmin.fieldsets + ProfileAdmin.fieldsets + MetaSeoFieldsAdmin.fieldsets
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
		delete_cached_fragment('persons','exhibitors', 'all')
		exhibitions = Exhibitions.objects.filter(exhibitors=obj.id).only('slug')
		for exh in exhibitions:
			delete_cached_fragment('persons','exhibitors', exh.slug)
			delete_cached_fragment('exhibition_content', exh.slug)

		super().save_model(request, obj, form, change)



class JuryAdmin(PersonAdmin, MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('logo', 'name', 'slug', 'excerpt', 'description', 'sort',),
		}),
	) + MetaSeoFieldsAdmin.fieldsets

	list_display = ('logo_thumb', 'name', 'excerpt',)
	list_display_links = ('logo_thumb', 'name', )

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('persons','jury', 'all')
		exhibitions = Exhibitions.objects.filter(jury=obj.id).only('slug')
		for exh in exhibitions:
			delete_cached_fragment('persons','jury', exh.slug)
			delete_cached_fragment('exhibition_content', exh.slug)

		super().save_model(request, obj, form, change)



class OrganizerAdmin(PersonAdmin, ProfileAdmin, MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = PersonAdmin.fieldsets + ProfileAdmin.fieldsets + MetaSeoFieldsAdmin.fieldsets
	list_display = ('logo_thumb', 'name', 'description_html',)
	list_display_links = ('logo_thumb', 'name', )
	ordering = ('sort',)

	def description_html(self, obj):
		return format_html(obj.description)

	description_html.short_description = 'Описание для главной страницы'

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('index_page')
		super().save_model(request, obj, form, change)



class PartnersAdmin(PersonAdmin, ProfileAdmin, MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = PersonAdmin.fieldsets + ProfileAdmin.fieldsets + MetaSeoFieldsAdmin.fieldsets
	list_display = ('logo_thumb', 'name', 'phone',)
	list_display_links = ('logo_thumb', 'name', 'phone',)

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		delete_cached_fragment('index_page')
		delete_cached_fragment('persons','partners', 'all')

		exhibitions = Exhibitions.objects.filter(partners=obj).only('slug')
		for exh in exhibitions:
			delete_cached_fragment('persons','partners', exh.slug)
			delete_cached_fragment('exhibition_content', exh.slug)



@admin.register(Categories)
class CategoriesAdmin(MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('title', 'slug', 'description', 'logo', 'sort',),
		}),
	) + MetaSeoFieldsAdmin.fieldsets

	list_display = ('logo_thumb', 'title', 'nominations_list', 'description',)
	list_display_links = ('logo_thumb', 'title',)

	def nominations_list(self, obj):
		return ', '.join(obj.nominations_set.all().values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'

	def save_model(self, request, obj, form, change):
		delete_cached_fragment('categories_list')
		super().save_model(request, obj, form, change)



@admin.register(Nominations)
class NominationsAdmin(MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('category', 'title', 'slug', 'description', 'sort',),
		}),
	) + MetaSeoFieldsAdmin.fieldsets

	list_display = ('category', 'title', 'description_html',)
	list_display_links = ('title',)
	list_per_page = 20
	empty_value_display = '<пусто>'

	def description_html(self, obj):
		return format_html(obj.description)

	description_html.short_description = 'Описание'

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		portfolio = Portfolio.objects.filter(nominations=obj)
		for item in portfolio:
			delete_cached_fragment('portfolio_list', item.owner.slug, item.project_id, True)
			delete_cached_fragment('portfolio_list', item.owner.slug, item.project_id, False)



class EventsInlineAdmin(admin.StackedInline):
	model = Events
	extra = 1 #new blank record count
	fields = ('title', 'date_event', 'time_start', 'time_end', 'lector',)
	classes = ['events-inline-tab',]
	#save_on_top = True # adding save button on top bar
	verbose_name_plural = ""



class EventsAdmin(MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('exhibition', 'title', 'date_event', 'time_start', 'time_end', 'location', 'hoster', 'lector', 'description',),
		}),
	) + MetaSeoFieldsAdmin.fieldsets

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



class WinnersAdmin(MetaSeoFieldsAdmin, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'classes': ('user-block',),
			'fields': ('exhibition', 'nomination', 'exhibitor','portfolio',),
		}),
	) + MetaSeoFieldsAdmin.fieldsets

	list_display = ('exh_year', 'nomination', 'exhibitor','portfolio')
	list_display_links = list_display
	#search_fields = ('nomination__title', 'exhibitor__name',)
	list_filter = ('exhibition__date_start', 'nomination', 'exhibitor')
	date_hierarchy = 'exhibition__date_start'
	ordering = ('-exhibition__date_start',)

	list_per_page = 30
	save_as = True
	save_on_top = True # adding save button on top bar


	""" Отобразим список участников с указанием сортировки по новому полю """
	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == "exhibitor":
			kwargs["queryset"] = Exhibitors.objects.order_by('name')

		return super().formfield_for_foreignkey(db_field, request, **kwargs)


	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		delete_cached_fragment('persons', 'winners', 'all')
		exhibitions = Exhibitions.objects.all()
		for exh in exhibitions:
			delete_cached_fragment('persons', 'winners', exh.slug)

		delete_cached_fragment('exhibition_content', obj.exhibition.slug)
		delete_cached_fragment('participant_detail', obj.portfolio.id)



class ImagesInline(admin.StackedInline):
	#form = ImageForm
	model = Image
	template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 1 #new blank record count
	show_change_link = True
	fields = ('file_thumb', 'file', 'title', 'sort', 'filename', )
	list_display = ('file_thumb', 'title',)
	readonly_fields = ('file_thumb', 'filename',)
	list_editable = ['title','sort']

	formfield_overrides = {
		models.ImageField: {'widget': CustomClearableFileInput()},
	}



class ImageAdmin(AdminImageMixin, admin.ModelAdmin):
	form = ImageForm

	fields = ('portfolio', 'title', 'description', 'file', 'sort')
	readonly_fields = ('file_thumb',)
	list_display = ('file_thumb', 'portfolio', 'title', 'author', 'sort',)
	list_display_links = ('file_thumb', 'portfolio', 'title',)
	list_filter = ('portfolio__owner', 'portfolio',)
	search_fields = ('title', 'file', 'portfolio__title', 'portfolio__owner__slug', 'portfolio__owner__name', 'portfolio__owner__user__first_name', 'portfolio__owner__user__last_name',)

	list_per_page = 50
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



class PortfolioAdmin(MetaSeoFieldsAdmin, admin.ModelAdmin):
	form = PortfolioForm
	#fields = MetaSeoFieldsAdmin.meta_fields
	fieldsets = (
		(None, {
			'classes': ('portfolio-block',),
			'fields': ('owner', 'exhibition', 'categories', 'nominations', 'title', 'description', 'cover', 'files', 'attributes','status',),
		}),
	) + MetaSeoFieldsAdmin.fieldsets

	list_display = ('owner', '__str__', 'exhibition', 'nominations_list', 'status')
	list_display_links = ('owner', '__str__')
	search_fields = ('title', 'owner__name', 'owner__user__first_name', 'owner__user__last_name', 'exhibition__title', 'nominations__title')
	list_filter = ('nominations__category', 'nominations', 'owner', 'status')
	date_hierarchy = 'exhibition__date_start'
	ordering = ('-exhibition__date_start','-project_id',)

	list_per_page = 30
	save_on_top = True # adding save button on top bar
	save_as = True
	view_on_site = True
	inlines = [ImagesInline, RatingInline, ReviewInline]

	# class Media:
	# 	css = {
    #          'all': ['/static/bootstrap/css/bootstrap.min.css']
    #          }
	# 	js = ['/static/js/jquery.min.js','/static/bootstrap/js/bootstrap.min.js','/static/js/files-upload.min.js','/static/js/project-upload.min.js']

	def nominations_list(self, obj):
		return ', '.join(obj.nominations.values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'
	nominations_list.admin_order_field = 'nominations__title'


	# def attributes_list(self, obj):
	# 	return ', '.join(obj.attributes.values_list('name', flat=True))
	# attributes_list.short_description = 'Аттрибуты для фильтра'
	# attributes_list.admin_order_field = 'attributes__group'


	""" Отобразим список участников с указанием сортировки по новому полю """
	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == "owner":
			kwargs["queryset"] = Exhibitors.objects.order_by('name')

		return super().formfield_for_foreignkey(db_field, request, **kwargs)


	def get_form(self, request, obj=None, **kwargs):
		form = super().get_form(request, obj=obj, **kwargs)
		form.request = request
		return form


	def save_model(self, request, obj, form, change):
		images = request.FILES.getlist('files')
		obj.save(images=images) # сохраним портфолио и связанные фотографии

		delete_cached_fragment('portfolio_list', obj.owner.slug, obj.project_id, True)
		delete_cached_fragment('portfolio_list', obj.owner.slug, obj.project_id, False)
		delete_cached_fragment('portfolio_slider', obj.owner.slug, obj.project_id)
		delete_cached_fragment('participant_detail', obj.owner.id)
		#delete_cached_fragment('exhibition_header', obj.exhibition.slug)

		for nomination in obj.nominations.all():
			if nomination.category:
				delete_cached_fragment('projects_list', nomination.category.slug)
				delete_cached_fragment('sidebar', nomination.category.slug)

		victories = Winners.objects.filter(portfolio=obj)
		for victory in victories:
			delete_cached_fragment('portfolio_list', victory.exhibition.slug, victory.nomination.slug, True)
			delete_cached_fragment('portfolio_list', victory.exhibition.slug, victory.nomination.slug, False)
			delete_cached_fragment('portfolio_slider', victory.exhibition.slug, victory.nomination.slug)




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
	verbose_name_plural = "Загруженные фотографии"
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

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		delete_cached_fragment('exhibition_overlay', obj.exhibition.slug)
		delete_cached_fragment('exhibition_gallery', obj.exhibition.slug)



@admin.register(Exhibitions)
class ExhibitionsAdmin(DjangoTabbedChangeformAdmin, MetaSeoFieldsAdmin, admin.ModelAdmin):
	form = ExhibitionsForm
	list_display = ('banner_thumb', 'title', 'date_start', 'date_end', )
	list_display_links = ('banner_thumb', 'title',)
	date_hierarchy = 'date_start'
	filter_horizontal = ('nominations', 'exhibitors',)
	#list_select_related = ('events',)
	# prepopulated_fields = {"slug": ('date_start',)} # adding name to slug field but not only DateFields
	save_on_top = True # adding save button on top bar
	list_per_page = 10
	view_on_site = True

	inlines = [EventsInlineAdmin, GalleryInlineAdmin,]

	fieldsets = (
		(None, {
			'classes': ('basic-tab',),
			'fields' : ('title', 'slug', 'banner', 'description', 'date_start', 'date_end', 'location',)
		}),
		(None, {
			'classes': ('exhibitors-tab',),
			'fields' : ('exhibitors',)
		}),
		(None, {
			'classes': ('nominations-tab',),
			'fields' : ('nominations',)
		}),
		(None, {
			'classes': ('jury-tab',),
			'fields' : ('jury',)
		}),
		(None, {
			'classes': ('partners-tab',),
			'fields' : ('partners',)
		}),
		(None, {
			'classes': ('files-upload-tab',),
			'fields' : ('files',)
		}),
		(None, {
			'classes': ('meta-tab', '',),
			'fields' : MetaSeoFieldsAdmin.meta_fields
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
		("СЕО", ['meta-tab']),
	)


	""" Отобразим список участников с указанием сортировки по новому полю """
	def formfield_for_manytomany(self, db_field, request, **kwargs):
		if db_field.name == "exhibitors":
			kwargs["queryset"] = Exhibitors.objects.order_by('name')
		return super().formfield_for_manytomany(db_field, request, **kwargs)

	# def formfield_for_foreignkey(self, db_field, request, **kwargs):
	# 	return super().formfield_for_foreignkey(db_field, request, **kwargs)


	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		#сохраним связанные с выставкой фото
		images = request.FILES.getlist('files')
		for image in images:
			upload_filename = path.join('gallery/', obj.slug, image.name)
			file_path = path.join(settings.MEDIA_ROOT,upload_filename)

			instance = Gallery(exhibition=obj, file=image)
			instance.save()


		delete_cached_fragment('navbar')
		delete_cached_fragment('exhibition_banner', obj.slug)
		delete_cached_fragment('exhibition_content', obj.slug)
		delete_cached_fragment('exhibition_events', obj.slug)
		delete_cached_fragment('exhibition_gallery', obj.slug)
		delete_cached_fragment('exhibition_overlay', obj.slug)
		if not change:
			delete_cached_fragment('exhibitions_list')



@admin.register(MetaSEO)
class MetaAdmin(admin.ModelAdmin):
	#form = MetaForm
	#fields = ('model','post_id','title','description','keywords',)
	list_display = ('model', 'root', 'title', 'description')
	list_display_links = ('model', 'title',)
	ordering = ('model','-post_id')
	search_fields = ('title', 'description', 'model')
	#list_filter = ('model',)

	def formfield_for_dbfield(self, db_field, request, **kwargs):
		if not ( self.meta and self.meta.model) and db_field.name == "model":
			kwargs["queryset"] = ContentType.objects.filter(
				model__in=['article', 'portfolio', 'exhibitions', 'categories', 'winners', 'exhibitors', 'partners', 'jury', 'events']
			)

		if self.meta and self.meta.model and db_field.name == "post_id":
			model = MetaSEO.get_model(self.meta.model.model)
			post_list = model.objects.all()
			CHOICES = [[None,'--------']] + list((x.id, x.__str__) for x in post_list )
			#CHOICES = [['','--------']] + list(post_list.values_list('id', 'name'))
			kwargs["widget"] = Select(choices=CHOICES)

		return super().formfield_for_dbfield(db_field, request, **kwargs)


	def get_form(self, request, obj=None, **kwargs):
		self.meta = obj
		if obj and obj.model:
			self.readonly_fields = ('model', )
		else:
			self.readonly_fields = ('post_id',)

		return super().get_form(request, obj, **kwargs)


	""" заменим название модели в ContentType """
	def get_name(self):
		verbose_name = self.model_class()._meta.verbose_name
		return verbose_name if verbose_name else self.__str__()

	ContentType.add_to_class('__str__', get_name)


	def root(self, obj):
		if obj.post_id:
			model = MetaSEO.get_model(obj.model.model)
			post = model.objects.get(pk=obj.post_id)
		else:
			post = '---'
		return post

	root.short_description = 'запись'

	# def formfield_for_choice_field(self, db_field, request, **kwargs):
	# 	return super().formfield_for_choice_field(db_field, request, **kwargs)



admin.site.register(Exhibitors, ExhibitorsAdmin)
admin.site.register(Jury, JuryAdmin)
admin.site.register(Partners, PartnersAdmin)
admin.site.register(Organizer, OrganizerAdmin)

admin.site.register(Events, EventsAdmin)
admin.site.register(Winners, WinnersAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(Image, ImageAdmin)

