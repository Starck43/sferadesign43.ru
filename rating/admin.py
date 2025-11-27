from django.contrib import admin

from exhibition.logic import delete_cached_fragment
from .models import Rating, Reviews

admin.site.site_title = 'Рейтинг портфолио'
admin.site.site_header = 'Рейтинг'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
	list_display = ('get_exhibition', 'portfolio', 'star', 'fullname', 'is_jury_rating',)
	readonly_fields = ('ip',)
	list_filter = ('star',)

	@admin.display(description='Выставка')
	def get_exhibition(self, obj):
		return obj.portfolio.exhibition

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		delete_cached_fragment('portfolio', obj.portfolio.id)


class RatingInline(admin.TabularInline):
	model = Rating
	extra = 0
	show_change_link = False
	fields = ('user', 'star',)
	readonly_fields = ('star', 'user')


@admin.register(Reviews)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('id', 'group', 'portfolio', 'fullname', 'parent', 'message', 'posted_date',)

	# def save_model(self, request, obj, form, change):
	# 	super().save_model(request, obj, form, change)

	# 	delete_cached_fragment('portfolio_review', obj.portfolio.id)


class ReviewInline(admin.StackedInline):
	model = Reviews
	extra = 0
	show_change_link = False
	fields = ('fullname', 'portfolio', 'message', 'posted_date')
	readonly_fields = ('user', 'group', 'parent', 'fullname', 'portfolio', 'message', 'posted_date')
