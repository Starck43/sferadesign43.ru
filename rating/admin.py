from django.contrib import admin

from exhibition.logic import delete_cached_fragment
from .models import Rating, Reviews, JuryRating


admin.site.site_title = 'Рейтинг портфолио'
admin.site.site_header = 'Рейтинг'

"""Рейтинг"""
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
	fields = ('user', 'portfolio', 'star',)
	list_display = ('star', 'portfolio', 'fullname', 'ip',)
	readonly_fields = ('ip',)
	list_filter = ('star',)

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		delete_cached_fragment('portfolio', obj.portfolio.id)


"""Оценки жюри"""
@admin.register(JuryRating)
class JuryRatingAdmin(admin.ModelAdmin):
	fields = ('jury', 'portfolio', 'exhibition', 'star', 'created_date', 'ip')
	list_display = ('star', 'portfolio', 'exhibition', 'fullname', 'created_date', 'ip')
	readonly_fields = ('created_date', 'ip')
	list_filter = ('star', 'exhibition', 'created_date')
	search_fields = ('portfolio__title', 'jury__first_name', 'jury__last_name', 'jury__username')
	date_hierarchy = 'created_date'
	
	def get_queryset(self, request):
		return super().get_queryset(request).select_related('jury', 'portfolio', 'exhibition')

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		delete_cached_fragment('portfolio', obj.portfolio.id)
		delete_cached_fragment('project', obj.portfolio.id)


"""Комментарии к работам"""
@admin.register(Reviews)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('id', 'group', 'portfolio', 'fullname', 'parent', 'message', 'posted_date', )

	# def save_model(self, request, obj, form, change):
	# 	super().save_model(request, obj, form, change)

	# 	delete_cached_fragment('portfolio_review', obj.portfolio.id)


"""Форма вывода рейтинга у портфолио в админке"""
class RatingInline(admin.TabularInline):
	model = Rating
	extra = 0
	show_change_link = False
	fields = ('user', 'star',)
	readonly_fields = ('star', 'user')


"""Форма вывода оценок жюри у портфолио в админке"""
class JuryRatingInline(admin.TabularInline):
	model = JuryRating
	extra = 0
	show_change_link = False
	fields = ('jury', 'exhibition', 'star', 'created_date')
	readonly_fields = ('jury', 'exhibition', 'star', 'created_date')


"""Форма вывода комментариев у портфолио в админке"""
class ReviewInline(admin.StackedInline):
	model = Reviews
	extra = 0
	show_change_link = False
	fields = ('fullname', 'portfolio', 'message', 'posted_date')
	readonly_fields = ('user', 'group', 'parent', 'fullname', 'portfolio', 'message', 'posted_date')


