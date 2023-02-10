from django.contrib import admin
from django.db.models import Q

from .models import Designer, Customer, Achievement
from .forms import DesignerForm
from exhibition.models import Portfolio
from exhibition.admin import MetaSeoFieldsAdmin

from django_tabbed_changeform_admin.admin import DjangoTabbedChangeformAdmin


admin.site.site_title = 'Страницы дизайнеров'
admin.site.site_header = 'Страницы дизайнеров'



class CustomerInline(admin.TabularInline):
	model = Customer
	#template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 1
	show_change_link = True
	fields = ('name', 'link','logo',)
	#list_display = ('logo', 'name',)
	#list_editable = ['name']
	classes = ['customers-inline-tab']



class AchievementInline(admin.TabularInline):
	model = Achievement
	#template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 0
	show_change_link = True
	fields = ('title', 'link', 'date', 'group',)
	list_display = ('title', 'date',)
	#list_editable = ['title']
	classes = ['achievements-inline-tab']



@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	fields = ('designer', 'name', 'excerpt', 'logo', 'link')
	list_display = ('designer', 'name', 'excerpt')
	list_display_links = ('designer', 'name')



@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
	fields = ('designer', 'title', 'description', 'date', 'group', 'link')
	list_display = ('designer', 'title', 'date', 'group')
	list_display_links = ('designer', 'title', 'date', 'group')



@admin.register(Designer)
class DesignerAdmin(DjangoTabbedChangeformAdmin, MetaSeoFieldsAdmin, admin.ModelAdmin):

	class Media:
		js = ['/static/js/designers.min.js']


	form = DesignerForm
	#fields = ('name', 'slug', 'title')
	list_display = ('avatar', 'logo', 'name', 'slug', 'status')
	list_display_links = ('avatar', 'logo', 'name', 'slug')
	search_fields = ('name', 'slug')
	#raw_id_fields = ('exh_portfolio','add_portfolio',)

	save_on_top = True # adding save button on top bar
	view_on_site = True
	inlines = [AchievementInline, CustomerInline]


	fieldsets = (
		(None, {
			'classes': ('basic-tab',),
			'fields' : ('owner', 'slug', 'avatar', 'logo', 'title', 'about', 'background', 'whatsapp','telegram','show_email', 'status', 'pub_date_start', 'pub_date_end', 'comment',)
		}),
		(None, {
			'classes': ('exh_portfolio-tab',),
			'fields' : ('exh_portfolio',)
		}),
		(None, {
			'classes': ('add_portfolio-tab',),
			'fields' : ('add_portfolio',)
		}),
		(None, {
			'classes': ('partners-tab',),
			'fields' : ('partners',)
		}),
		(None, {
			'classes': ('meta-tab',),
			'fields' : MetaSeoFieldsAdmin.meta_fields
		}),
	)

	tabs = (
		("Общая информация", ['basic-tab']),
		("Выставочные работы", ['exh_portfolio-tab']),
		("Вневыставочные работы", ['add_portfolio-tab']),
		("Достижения", ['achievements-inline-tab']),
		("Главные заказчики", ['customers-inline-tab']),
		("Партнеры", ['partners-tab']),
		("СЕО", ['meta-tab']),
	)

	def save_model(self, request, obj, form, change):
		obj.save(request)

	def name(self, obj):
		return obj.owner.name

	name.short_description = 'Дизайнер'

	# def formfield_for_manytomany(self, db_field, request, **kwargs):
	# 	if db_field.name == "exh_portfolio":
	# 		kwargs["queryset"] = Portfolio.objects.filter(owner=)
	# 	return super().formfield_for_manytomany(db_field, request, **kwargs)
