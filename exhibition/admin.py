import os
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import get_object_or_404
from .models import *
from crm import models

from sorl.thumbnail.admin import AdminImageMixin
from multiupload.admin import MultiUploadAdmin
# Exhibitors, Jury, Partners, Events, Nominations, Exhibitions, Portfolio, Image

class PersonAdmin(admin.ModelAdmin):
	model = Person

	fieldsets = (
		(None, {
			'classes': ('person-block',),
			'fields': ( ('avatar', ), 'name', 'slug', 'description',)
		}),
	)
	prepopulated_fields = {"slug": ('name',)} # adding name to slug field
	list_display = ('photo_thumb', 'name', 'description',)
	search_fields = ('name', 'slug', 'description',)
	list_display_links = ('photo_thumb', 'name',)
	list_per_page = 20


class ProfileAdmin(admin.ModelAdmin):
	model = Profile

	fieldsets = (
		('Профиль', {
			'classes': ('profile-block',),
			'fields': (('logo',), 'address', 'phone', 'email', 'site', 'vk', 'fb', 'instagram',)
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

	list_display = ('photo_thumb', 'user_name', 'name', 'phone', )
	search_fields = PersonAdmin.search_fields + ('user',)
	def user_name(self, obj):
		if (not obj.user.first_name) and (not obj.user.last_name) :
			return obj.user.username
		else:
			return ("%s %s" % (obj.user.first_name, obj.user.last_name))
	user_name.short_description = 'Пользователь'


class JuryAdmin(PersonAdmin):
	pass


class OrganizerAdmin(PersonAdmin):
	pass


class PartnersAdmin(PersonAdmin, ProfileAdmin):

	#fields = PersonAdmin.fields + ProfileAdmin.fields
	fields_exclude = ('avatar',)
	list_display = ('logo_thumb', 'name', 'phone',)
	list_display_links = ('logo_thumb', 'name', 'phone',)


class NominationsAdmin(admin.ModelAdmin):

	fields = ('title', 'slug', 'description', 'logo',)
	list_display = ('logo_thumb', 'title', )
	list_display_links = ('logo_thumb', 'title', )


class EventsInlineAdmin(admin.TabularInline):

	model = Events
	extra = 1 #new blank record count
	fields = ('title', 'date_event', 'time_start', 'lector',)
	save_on_top = True # adding save button on top bar


class EventsAdmin(admin.ModelAdmin):

	list_display = ('title', 'date_event', 'time_event', 'hoster', 'exhibition',)
	search_fields = ('title', 'description', 'hoster', 'lector',)
	list_filter = ('exhibition__date_start', 'date_event',)
	date_hierarchy = 'exhibition__date_start'
	save_on_top = True # adding save button on top bar


class WinnersAdmin(admin.ModelAdmin):

	list_display = ('exh_year', 'nomination', 'exhibitor',)
	list_display_links = ('exhibitor', 'nomination', 'exh_year',)
	save_on_top = True # adding save button on top bar

	# def formfield_for_foreignkey(self, db_field, request, **kwargs):
	# 	if db_field.name == "nomination":
	# 		query = Exhibitions.objects.select_related('nominations').values_list('pk', 'nominations__id')
	# 		print(query)

	# 	return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GalleryMultiuploadMixing(object):

	def process_uploaded_file(self, uploaded, portfolio, request):
		title = request.POST['title'] or os.path.splitext(uploaded.name)[0]

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


class ImageInlineAdmin(admin.TabularInline):
	model = Image
	extra = 3 #new blank record count
	fields = ('title', 'description', 'file', 'file_thumb',)
	readonly_fields = ('file_thumb',)


class ImageAdmin(AdminImageMixin, GalleryMultiuploadMixing, MultiUploadAdmin, admin.ModelAdmin):

	fields = ('portfolio', 'title', 'description', 'file_thumb', 'file',)
	list_display = ('title', 'description', 'file_thumb',)
	readonly_fields = ('file_thumb',)
	save_on_top = True # adding save button on top bar

	multiupload_form = True
	multiupload_list = True
	multiupload_limitconcurrentuploads = 50


class PortfolioAdmin(GalleryMultiuploadMixing, MultiUploadAdmin, admin.ModelAdmin):
	# fields = ['title',]
	list_display = ('exhibition', 'owner', 'title', 'nominations_list')
	#radio_fields = {"portfolio": admin.VERTICAL} #radio button list for foreignKey field
	# raw_id_fields = ("portfolio",) #input widget instead of select
	# sortable_by = []
	# list_editable = ['title',]
	# list_display_links = ['title',]
	# readonly_fields = []
	search_fields = ('title', 'description',)
	list_filter = ('exhibition__date_start', 'owner', 'nominations', )

	# prepopulated_fields = {"slug": ("title",)} # adding name to slug field
	save_on_top = True # adding save button on top bar
	date_hierarchy = 'exhibition__date_start'

	inlines = [ImageInlineAdmin,]
	multiupload_form = True
	multiupload_list = False

	def nominations_list(self, obj):
		return ', '.join(obj.nominations.values_list('title', flat=True))
	nominations_list.short_description = 'Номинации'

	def delete_file(self, pk, request):
		obj = get_object_or_404(Image, pk=pk)
		return obj.delete()

	# def formfield_for_manytomany(self, db_field, request, **kwargs):
	# 	if db_field.name == "nominations":
	# 		kwargs["queryset"] = Nominations.objects.filter(pk=request.id)
	# 	return super().formfield_for_manytomany(db_field, request, **kwargs)


class ExhibitionsAdmin(admin.ModelAdmin):

	#fields = ('title', 'slug', 'description', 'date_start', 'date_end', 'location',)
	list_display = ('title', 'date_start', 'date_end', 'location',)
	date_hierarchy = 'date_start'
	#filter_horizontal = ('events',)
	#list_select_related = ('events',)
	prepopulated_fields = {"slug": ('date_start',)} # adding name to slug field
	inlines = [EventsInlineAdmin,]


admin.site.register(Exhibitors, ExhibitorsAdmin)
admin.site.register(Jury, JuryAdmin)
admin.site.register(Partners, PartnersAdmin)
admin.site.register(Organizer, OrganizerAdmin)

admin.site.register(Nominations, NominationsAdmin)
admin.site.register(Events, EventsAdmin)
admin.site.register(Winners, WinnersAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(Image, ImageAdmin)

admin.site.register(Exhibitions, ExhibitionsAdmin)

