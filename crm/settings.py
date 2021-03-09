"""
Django settings for crm project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os, sys
# django-environ
# https://django-environ.readthedocs.io/en/latest/
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load and read .env file
# OS environment variables take precedence over variables from .env
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', False)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', list, [])


# Application definition

INSTALLED_APPS = [
    'django_static_jquery_ui',
    'django_tabbed_changeform_admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites', #added for django-allauth
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
    'smart_selects',
    'watson',
    'exhibition',
    'rating',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.instagram',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.odnoklassniki',
    'allauth.socialaccount.providers.vk',
    'allauth.socialaccount.providers.google',
    #'allauth.socialaccount.providers.apple',
    #'allauth.socialaccount.providers.mailru',
    #'allauth.socialaccount.providers.yandex',
]

MIDDLEWARE = [
    'django.middleware.cache.CacheMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'django.middleware.cache.FetchFromCacheMiddleware',
    # watson search
    #'django.middleware.transaction.TransactionMiddleware',
    'watson.middleware.SearchContextMiddleware',
]

ROOT_URLCONF = 'crm.urls'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ os.path.join(BASE_DIR, 'templates') ],
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


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': env.db()
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,
        }
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

CACHES = {
    'default': env.cache('MEMCACHE_URL'), # {'BACKEND': 'django.core.cache.backends.dummy.DummyCache',}
}


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'odnoklassniki': {
        'APP': {
            'client_id': '512000847912',
            'secret': '79F74C7253623973B5E39731',
        },
        'SCOPE': [
            'GET_EMAIL',
        ],
    },
    'google': {
        'APP': {
            'client_id': '46937687995-80ef80l5bbvug8m23f5v56h8gkeah227.apps.googleusercontent.com',
            'secret': 'u8pnwhrv_s-6XAnsajGz_VJE',
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'facebook': {
        'APP': {
            'client_id': '2910399535951628',
            'secret': 'c10c8aaf1eb05dba81eeb8c9070e0a88',
        },
        #'METHOD': 'js_sdk', # default is oauth2 method
        #'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'name',
        ],
        'EXCHANGE_TOKEN': True,
        'LOCALE_FUNC': lambda request: 'ru_RU',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v9.0',
    },
    'vk': {
        'APP': {
            'client_id': '7725491',
            'secret': 'tdv9taPqYAJk7wM3W62V',
            'key': '24518b7324518b7324518b73ff24246ac02245124518b7344511499a33dec7893902549'
        }
    }

}

SITE_ID=1
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 14
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
#ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_MAX_EMAIL_ADDRESSES = 2
SOCIALACCOUNT_QUERY_EMAIL=True
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
EMAIL_RICIPIENTS = env('EMAIL_RICIPIENTS', list, [])
EMAIL_HOST_USER = EMAIL_CONFIG['EMAIL_HOST_USER']
DEFAULT_FROM_EMAIL = EMAIL_CONFIG['EMAIL_HOST_USER']
vars().update(EMAIL_CONFIG)

ADMINS = [('Starck', EMAIL_RICIPIENTS)]


FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
 ]


FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400
FILE_UPLOAD_PERMISSIONS = 0o775

# It uses in exhibition.views.projects_list as parameter for queryset
PORTFOLIO_COUNT_PER_PAGE = 3

# sorl-thumbnail settings

THUMBNAIL_QUALITY = 85
THUMBNAIL_UPSCALE = False
THUMBNAIL_FILTER_WIDTH = 600
#Resolution multiplicators, e.g. value 2 means for every thumbnail of regular size x*y, additional thumbnail of 2x*2y size is created.
THUMBNAIL_ALTERNATIVE_RESOLUTIONS = [2,2]
#THUMBNAIL_PROGRESSIVE = False
ADMIN_THUMBNAIL_SIZE = [100, 100]

DJANGORESIZED_DEFAULT_SIZE = [1500, 1024]
DJANGORESIZED_DEFAULT_QUALITY = 80
DJANGORESIZED_DEFAULT_KEEP_META = False

CRISPY_TEMPLATE_PACK = 'bootstrap4'


CKEDITOR_UPLOAD_PATH = 'attachments/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
AWS_QUERYSTRING_AUTH = False
CKEDITOR_CONFIGS = {
    'default': {
        #'skin': 'moono',
        'toolbar': [
            {'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize']},
            {'name': 'basicstyles', 'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
            {'name': 'paragraph', 'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', '-',
                'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl',]},
            {'name': 'tools', 'items': ['Image', 'Link', 'Maximize', 'ShowBlocks','Undo', 'Redo',]},
        ],
        'font_names': 'Corbel;Calibri;Arial;Tahoma;Sans serif;Helvetica;Symbol',
        'width': '100%',
        'height': 400,
        'tabSpaces': 4,
        'removePlugins': 'flash,iframe',
        #'toolbarCanCollapse': True,
    },
}

#X_FRAME_OPTIONS = 'SAMEORIGIN'


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
PUBLIC_ROOT = env('PUBLIC_ROOT', default='')

STATIC_URL = '/static/'


if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, PUBLIC_ROOT + 'static/')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, PUBLIC_ROOT + 'assets/'),
    ]
else:
    #STATIC_ROOT = ''
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, PUBLIC_ROOT + 'static/'),
    ]

# Base url to serve media files
MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, PUBLIC_ROOT + 'media/')

