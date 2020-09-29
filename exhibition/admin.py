from django.contrib import admin
from django.shortcuts import get_object_or_404
from .models import *
from crm import models

from sorl.thumbnail.admin import AdminImageMixin
from multiupload.admin import MultiUploadAdmin

# Exhibitors, Jury, Partners, Events, Nominations, Exhibitions, Portfolio, Image

class PersonAdmin(admin.ModelAdmin):

	fields = ('photo_thumb', 'name', 'slug', 'description')
	list_display = ('photo_thumb', 'name', 'description')
	search_fields = ('name', 'slug', 'description',)
	prepopulated_fields = {"slug": ('name',)} # adding name to slug field
	list_display_links = ('photo_thumb', 'name',)
	list_per_page = 20


class ProfileAdmin(admin.ModelAdmin):

	list_display = ('phone',)
	fieldsets = (
        (None, {
            'fields': ('address', 'phone', 'email', 'logo_thumb',)
        }),
        ('Дополнительно', {
            'classes': ('collapse',),
            'fields': ('logo', 'site', 'vk', 'fb', 'instagram')
        }),
    )
	

class ExhibitorsAdmin(PersonAdmin, ProfileAdmin):

	fields = PersonAdmin.fields + ProfileAdmin.fields
	list_display = ('photo_thumb', 'name', 'full_user_name')
	search_fields = PersonAdmin.search_fields + ('user__first_name', 'user__last_name')
	
	def full_user_name(self, obj):
        return ("%s %s" % (obj.first_name, obj.last_name))
    full_user_name.short_description = 'ФИО'


class ExhibitorsInlineAdmin(admin.TabularInline):

	model = Exhibitors
	extra = 1 #new blank record count
	fields = ('name', 'slug', 'description', 'avatar', 'photo_thumb',)
	list_display = ('photo_thumb', 'name',)
	

class JuryAdmin(PersonAdmin):
	pass


class PartnersAdmin(PersonAdmin, ProfileAdmin):

	fields = PersonAdmin.fields + ProfileAdmin.fields
	fields_exclude = ('photo_thumb')
	list_display = ('logo_thumb', 'name', 'phone')


class NominationsAdmin(admin.ModelAdmin):

	list_display = ('name', 'description', 'logo_thumb')
	

class NominationsInlineAdmin(admin.TabularInline):

	model = Nominations
	extra = 1 #new blank record count
	fields = ('title', 'slug', 'description', 'logo', 'logo_thumb',)
	list_display = ('title', 'logo_thumb',)
	#readonly_fields = ['logo_thumb',]


class ExhibitionsAdmin(admin.ModelAdmin):

	list_display = ('title', 'date_start', 'date_end', 'location', 'description',)
	date_hierarchy = 'date_start'
	filter_horizontal = ('exhibitors', 'nominations')
	list_select_related = ('exhibitors', 'nominations')
	inlines = (NominationsInlineAdmin, ExhibitorsInlineAdmin)


class WinnersAdmin(admin.ModelAdmin):
	def queryset(self, request):
		return super().queryset(request).select_related('exhibition')
	#def formfield_for_foreignkey(self, db_field, request, **kwargs):
        #if db_field.name == "exhibition":
            #kwargs["queryset"] = Winners.objects.all().select_related('exhibition')

        #return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
class EventsAdmin(admin.ModelAdmin):

	list_display = ('title', 'date_event', 'time_start', 'time_end', 'hoster', 'exhibition__title')
	search_fields = ('title', 'hoster', 'lector')
	list_filter = ('exhibition__date_start', 'date_event')


class GalleryMultiuploadMixing(object):

	def process_uploaded_file(self, uploaded, project, request):
		if project:
			image = project.images.create(file=uploaded)
		else:
			image = Image.objects.create(file=uploaded, project=None)
		return {
			'url': image.file.url,
			'thumbnail_url': image.file.url,
			'id': image.id,
			'name': image.filename
		}


class ImageInlineAdmin(admin.TabularInline):
	model = Image
	extra = 1 #new blank record count
	fields = ('title', 'description', 'file', 'file_thumb',)
	list_display = ('title', 'description', 'file_thumb',)
	readonly_fields = ('file_thumb',)


class ImageAdmin(AdminImageMixin, GalleryMultiuploadMixing, MultiUploadAdmin, admin.ModelAdmin):

	fields = ('title', 'description', 'file_thumb', 'file', 'name')
	list_display = ('title', 'description', 'file_thumb', 'name')
	readonly_fields = ('file_thumb')

	multiupload_form = False
	multiupload_list = True
	multiupload_limitconcurrentuploads = 50


class PortfolioAdmin(GalleryMultiuploadMixing, MultiUploadAdmin, admin.ModelAdmin):
	# fields = ['title',]
	list_display = ('title',)
	radio_fields = {"portfolio": admin.VERTICAL} #radio button list for foreignKey field
	# raw_id_fields = ("portfolio",) #input widget instead of select
	# list_filter = []
	# sortable_by = []
	# list_editable = ['title',]
	# list_display_links = ['title',]
	# readonly_fields = []
	# search_fields = ['title', ]
	# inlines = ['TagsInline',]
	# prepopulated_fields = {"slug": ("title",)} # adding name to slug field
	save_on_top = true # adding save button on top bar
	

	inlines = (ImageInlineAdmin)
	multiupload_form = True
	multiupload_list = False

	def delete_file(self, pk, request):
		obj = get_object_or_404(Image, pk=pk)
		return obj.delete()

	def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "nominations":
            kwargs["queryset"] = Nominations.objects.filter(pk=request.id)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
        

admin.site.register(Exhibitors, ExhibitorsAdmin)
admin.site.register(Jury, JuryAdmin)
admin.site.register(Partners, PartnersAdmin)

admin.site.register(Nominations, NominationsAdmin)
admin.site.register(Events, EventsAdmin)
admin.site.register(Winners, WinnersAdmin)
admin.site.register(Exhibitions, ExhibitionsAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(Image, ImageAdmin)

