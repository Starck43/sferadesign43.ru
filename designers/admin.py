from django.contrib import admin

from exhibition.admin import MetaSeoFieldsAdmin
from .forms import DesignerForm
from .models import Designer, Customer, Achievement

admin.site.site_title = 'Сайты дизайнеров'
admin.site.site_header = 'Сайты дизайнеров'


class CustomerInline(admin.StackedInline):
	model = Customer
	# template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 1
	show_change_link = True
	fields = ('name', 'link', 'logo',)
	# list_display = ('logo', 'name',)
	# list_editable = ['name']
	classes = ['customers-inline-tab']


class AchievementInline(admin.StackedInline):
	model = Achievement
	# template = 'admin/exhibition/edit_inline/stacked.html'
	extra = 0
	show_change_link = True
	fields = ('cover', 'title', 'subtitle', 'description', 'group', 'link', 'date', )
	list_display = ('title', 'group', 'date',)
	# list_editable = ['title']
	classes = ['achievements-inline-tab']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	fields = ('designer', 'name', 'excerpt', 'logo', 'link')
	list_display = ('designer', 'name', 'excerpt')
	list_display_links = ('designer', 'name')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
	fields = ('designer', 'title', 'description', 'date', 'group', 'link')
	list_display = ('designer', 'title', 'subtitle', 'date', 'group')
	list_display_links = ('designer', 'title', 'date', 'group')


@admin.register(Designer)
class DesignerAdmin(MetaSeoFieldsAdmin, admin.ModelAdmin):
	class Media:
		js = ['/static/js/designers.min.js']

	form = DesignerForm
	list_display = ('id', 'owner', 'logo', 'slug', 'status')
	list_display_links = ('id', 'owner')
	filter_horizontal = ('exh_portfolio', 'add_portfolio')
	search_fields = ('title', 'slug')
	list_per_page = 50

	inlines = [AchievementInline, CustomerInline]

	fieldsets = (
		(
			"Общая информация", {
				"fields": (
					'owner', 'slug', 'avatar', 'logo', 'title', 'about', 'background', 'whatsapp', 'telegram',
					'show_phone', 'show_email', 'status', 'pub_date_start', 'pub_date_end', 'comment',
				),
				"classes": ('',)
			}
		),
		(
			"Портфолио", {
				'fields': ('exh_portfolio', 'add_portfolio'),
				"classes": ('',)
			},
		),
		(
			"Партнеры", {
				'fields': ('partners',),
				"classes": ('',)
			},
		),
		(
			"CEO", {
				'fields': MetaSeoFieldsAdmin.meta_fields,
				"classes": ('',)
			},
		),
	)

