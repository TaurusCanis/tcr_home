import os
import django_heroku

ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

DEBUG = False
# DEBUG = os.environ.get('DJANGO_DEBUG', '') != 'False'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get('SECRET_KEY', )
BRAINTREE_PRODUCTION_MERCHANT_ID = os.environ.get('BRAINTREE_PRODUCTION_MERCHANT_ID', )
BRAINTREE_PRODUCTION_PUBLIC_KEY = os.environ.get('BRAINTREE_PRODUCTION_PUBLIC_KEY', )
BRAINTREE_PRODUCTION_PRIVATE_KEY = os.environ.get('BRAINTREE_PRODUCTION_PRIVATE_KEY', )

PRINTFUL_KEY = os.environ.get('PRINTFUL_KEY', )

ALLOWED_HOSTS = ['tauruscanisrex.com', 'tauruscanisrex.herokuapp.com', '127.0.0.1']
DEBUG_PROPAGATE_EXCEPTIONS = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'django_countries',
    'localflavor',
    'django_inlinecss',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'djecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
#                        'pathname=%(pathname)s lineno=%(lineno)s ' +
#                        'funcname=%(funcName)s %(message)s'),
#             'datefmt': '%Y-%m-%d %H:%M:%S'
#         },
#         'simple': {
#             'format': '%(levelname)s %(message)s'
#         }
#     },
#     'handlers': {
#         'null': {
#             'level': 'DEBUG',
#             'class': 'logging.NullHandler',
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose'
#         }
#     },
#     'loggers': {
#         'testlogger': {
#             'handlers': ['console'],
#             'level': 'INFO',
#         }
#     }
# }

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": os.path.join(BASE_DIR, 'db.sqlite3')
    # }
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', ),
        'NAME': os.environ.get('DB_NAME', )
        'USER': os.environ.get('DB_USER', ),
        'PASSWORD': os.environ.get('DB_PASSWORD', ),
        'HOST': os.environ.get('DB_HOST', ),
        'PORT': os.environ.get('DB_PORT', ),
    }
}

if ENVIRONMENT == 'production':
    DEBUG = False
    # SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#Auth

AUTHENTICATION_BACKENDS = (

    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',

)

SITE_ID = 1
LOGIN_REDIRECT_URL = "/"

CRISPY_TEMPLATE_PACK = "bootstrap4"

EMAIL_HOST = os.environ.get('EMAIL_HOST', )
EMAIL_PORT = os.environ.get('EMAIL_PORT', )
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', )
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', )
EMAIL_USE_SSL = True



STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static_in_env')]
VENV_PATH = os.path.dirname(BASE_DIR)
STATIC_ROOT = os.path.join(VENV_PATH, 'static_root')
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(VENV_PATH, "media")

# The URL to use when referring to static files (where they will be served from)
# STATIC_URL = '/static/'

# The absolute path to the directory where collectstatic will collect static files for deployment.
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Extra places for collectstatic to find static files.
# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, 'static'),
# )

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

django_heroku.settings(locals())
