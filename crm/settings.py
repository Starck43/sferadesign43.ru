import os
import sys
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
if os.path.exists(BASE_DIR / '.env'):
	env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', False)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', list, ['localhost'])

# Application definition

INSTALLED_APPS = [
	'jazzmin',

	'django_static_jquery_ui',
	'django_tabbed_changeform_admin',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.sites',  # added for django-allauth
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django.contrib.sitemaps',
	'django.forms',
	'ckeditor',
	'ckeditor_uploader',
	'sorl.thumbnail',
	'crispy_forms',
	'crispy_bootstrap5',
	'smart_selects',
	'watson',
	'allauth',
	'allauth.account',
	'allauth.socialaccount',
	'allauth.socialaccount.providers.vk',
	'allauth.socialaccount.providers.odnoklassniki',
	'allauth.socialaccount.providers.google',
	# 'allauth.socialaccount.providers.mailru',
	# 'allauth.socialaccount.providers.yandex',

	'exhibition',
	'rating',
	'blog',
	'ads',
	'designers'
]

MIDDLEWARE = [
	# 'django.middleware.cache.CacheMiddleware',
	# 'django.middleware.cache.UpdateCacheMiddleware',

	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',

	'django.middleware.cache.FetchFromCacheMiddleware',
	# watson search
	# 'django.middleware.transaction.TransactionMiddleware',
	'watson.middleware.SearchContextMiddleware',
	'exhibition.middleware.AjaxMiddleware',  # custom middlewares
	'allauth.account.middleware.AccountMiddleware',
]

if DEBUG:
	INSTALLED_APPS.extend(['debug_toolbar'])
	MIDDLEWARE.extend(['debug_toolbar.middleware.DebugToolbarMiddleware'])

ROOT_URLCONF = 'crm.urls'

INTERNAL_IPS = ['localhost', ]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',

				# custom context for using in all templates
				'exhibition.context_processors.common_context',
			],
		},
	},
]

WSGI_APPLICATION = 'crm.wsgi.application'

db_config = env.db()

if db_config['ENGINE'] in ['django.db.backends.postgresql_psycopg2', 'django.db.backends.postgresql']:
	db_config['ENGINE'] = 'django.db.backends.postgresql'

DATABASES = {
	'default': db_config
}

CACHES = {
	'default': env.cache('REDIS_URL')
}

AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
		'OPTIONS': {
			'min_length': 6,
		}
	},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = (
	# Need to log in by username in Django admin, regardless of `allauth`
	'django.contrib.auth.backends.ModelBackend',
	# `allauth` specific authentication methods, such as login by e-mail
	'allauth.account.auth_backends.AuthenticationBackend',
)

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
	'google': {
		'SCOPE': [
			'profile',
			'email',
		],
		'AUTH_PARAMS': {
			'access_type': 'online',
		}
	},
	'odnoklassniki': {
		'SCOPE': ['VALUABLE_ACCESS', 'LONG_ACCESS_TOKEN', 'GET_EMAIL'],
		# 'FIELDS': [ 'uid', 'first_name', 'last_name', 'name', 'email', ],
	}

}

SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 14
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
# ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_MAX_EMAIL_ADDRESSES = 2
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"
SOCIALACCOUNT_AUTO_SIGNUP = False
LOGIN_REDIRECT_URL = "/account/"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_ADAPTER = "exhibition.adapter.CustomPasswordResetAdapter"
ACCOUNT_FORMS = {
	'signup': 'exhibition.forms.AccountSignupForm',
}
SOCIALACCOUNT_FORMS = {
	'signup': 'exhibition.forms.CustomSocialSignupForm',
}

EMAIL_CONFIG = env.email_url('EMAIL_URL')
EMAIL_RECIPIENTS = env('EMAIL_RECIPIENTS', list, [])
EMAIL_HOST_USER = EMAIL_CONFIG['EMAIL_HOST_USER']
DEFAULT_FROM_EMAIL = EMAIL_CONFIG['EMAIL_HOST_USER']
vars().update(EMAIL_CONFIG)

ADMINS = [('Starck', EMAIL_RECIPIENTS)]

FILE_UPLOAD_HANDLERS = [
	"django.core.files.uploadhandler.MemoryFileUploadHandler",
	"django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

STORAGES = {
	'default': {
		'BACKEND': 'django.core.files.storage.FileSystemStorage',
	},
	'staticfiles': {
		'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
	},
}
# sorl-thumbnail settings
THUMBNAIL_REDIS_URL = env('THUMBNAIL_REDIS_URL', str, None)
if THUMBNAIL_REDIS_URL:
	THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'

THUMBNAIL_QUALITY = 80
THUMBNAIL_UPSCALE = False
THUMBNAIL_FILTER_WIDTH = 600

ADMIN_THUMBNAIL_QUALITY = 75
ADMIN_THUMBNAIL_SIZE = [100, 100]

DJANGORESIZED_DEFAULT_QUALITY = 90
DJANGORESIZED_DEFAULT_SIZE = [1500, 1080]
DJANGORESIZED_DEFAULT_KEEP_META = False

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

CKEDITOR_UPLOAD_PATH = 'attachments/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
AWS_QUERYSTRING_AUTH = False
CKEDITOR_CONFIGS = {
	'default': {
		# 'skin': 'mono',
		'toolbar': [
			{'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize']},
			{
				'name': 'basicstyles',
				'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Superscript', '-', 'RemoveFormat']
			},
			{'name': 'colors', 'items': ['TextColor', 'BGColor']},
			{
				'name': 'paragraph',
				'items': [
					'NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', '-',
					'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl',
				]
			},
			{'name': 'tools', 'items': ['Image', 'Link', 'Maximize', 'ShowBlocks', 'Undo', 'Redo', ]},
		],
		'font_names': 'Corbel;Calibri;Arial;Tahoma;Sans serif;Helvetica;Symbol',
		'width': '100%',
		'height': 200,
		'tabSpaces': 4,
		'removePlugins': 'flash,iframe',
		# 'toolbarCanCollapse': True,
	},
}

X_FRAME_OPTIONS = 'SAMEORIGIN'

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'console': {
			'format': '%(asctime)s [%(levelname)s]: %(message)s'
		},
	},
	'handlers': {
		'console': {
			'class': 'logging.StreamHandler',
			'formatter': 'console'
		},
	},
	'loggers': {
		'': {
			'level': 'INFO',
			'handlers': ['console'],
			'propagate': True
		}
	},
}

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

PUBLIC_ROOT = env('PUBLIC_ROOT', default='')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, PUBLIC_ROOT, 'media')

STATIC_URL = 'static/'

if DEBUG:
	STATICFILES_DIRS = [
		BASE_DIR / 'static'
	]
else:
	STATIC_ROOT = os.path.join(BASE_DIR, PUBLIC_ROOT, 'static')

FILES_UPLOAD_FOLDER = 'uploads/'

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
MAX_UPLOAD_FILES_SIZE = 20 * 5 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o775

if os.path.exists(os.path.join(MEDIA_ROOT, 'tmp')):
	FILE_UPLOAD_TEMP_DIR = os.path.join(MEDIA_ROOT, 'tmp')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# It uses in exhibition.views.projects_list as parameter for queryset
PORTFOLIO_COUNT_PER_PAGE = 20
# It uses in blog.views.article_list as parameter for queryset
ARTICLES_COUNT_PER_PAGE = 10
