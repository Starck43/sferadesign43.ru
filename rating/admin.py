from django.contrib import admin

from .models import Rating, Reviews


admin.site.site_title = 'Рейтинг портфолио'
admin.site.site_header = 'Рейтинг'

"""Рейтинг"""
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
	fields = ('fullname',)
	list_display = ('star', 'portfolio', 'fullname', 'ip',)
	readonly_fields = ('ip',)
	list_filter = ('star',)


"""Комментарии к работам"""
@admin.register(Reviews)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('id', 'group', 'portfolio', 'fullname', 'parent', 'message', 'posted_date', )


"""Форма вывода рейтинга у портфолио в админке"""
class RatingInline(admin.TabularInline):
	model = Rating
	extra = 0
	show_change_link = False
	fields = ('user', 'star',)
	readonly_fields = ('star', 'user')


"""Форма вывода комментариев у портфолио в админке"""
class ReviewInline(admin.StackedInline):
	model = Reviews
	extra = 0
	show_change_link = False
	fields = ('fullname', 'portfolio', 'message', 'posted_date')
	readonly_fields = ('user', 'group', 'parent', 'fullname', 'portfolio', 'message', 'posted_date')


