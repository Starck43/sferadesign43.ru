from django.contrib import admin

from .models import Rating, Reviews


admin.site.site_title = 'Рейтинг портфолио'
admin.site.site_header = 'Рейтинг'

"""Рейтинг"""
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
	list_display = ('star', 'portfolio', 'user_name', 'ip')
	readonly_fields = ('ip',)
	list_filter = ('star',)

	def user_name(self, obj):
		if not obj.user:
			return None

		if (not obj.user.first_name) and (not obj.user.last_name) :
			return obj.user.username
		else:
			return '%s %s' % (obj.user.first_name, obj.user.last_name)
	user_name.short_description = 'Пользователь'


"""Отзывы на странице фильма"""
class ReviewInline(admin.TabularInline):
	model = Reviews
	extra = 0
	show_change_link = True
	readonly_fields = ('fullname', 'portfolio', 'message', 'posted_date')


"""Отзывы к фильму"""
@admin.register(Reviews)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('id', 'group', 'portfolio', 'fullname', 'parent', 'message', 'posted_date', )


