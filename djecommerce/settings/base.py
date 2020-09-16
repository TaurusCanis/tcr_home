import os
import django_heroku

ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

DEBUG = True
# DEBUG = os.environ.get('DJANGO_DEBUG', '') != 'False'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SECRET_KEY = '-05sgp9!deq=q1nltm@^^2cc+v29i(tyybv3v2t77qi66czazj'
# SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '-05sgp9!deq=q1nltm@^^2cc+v29i(tyybv3v2t77qi66czazj')
# SECRET_KEY = os.environ.get('SECRET_KEY', '')
ALLOWED_HOSTS = ['tauruscanisrex.com', 'tauruscanisrex.herokuapp.com', '127.0.0.1']

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

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static_in_env')]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root')


DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": os.path.join(BASE_DIR, 'db.sqlite3')
    # }
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'd7qibaflpi4phs',
        'USER': 'dlrqebnhfvncdc',
        'PASSWORD': 'fd351b73658f2fc4cd9ef678417f77f772f0954f78b061f303dc886fb4cf6019',
        'HOST': 'ec2-54-175-77-250.compute-1.amazonaws.com',
        'PORT': '5432',
    }
}

if ENVIRONMENT == 'production':
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')
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

STRIPE_PUBLIC_KEY = 'pk_test_4tNiwpsFHEX7N7hon7bpW4kE00saVfxboZ'
STRIPE_SECRET_KEY = 'sk_test_sYyZfPMDiefqOPb1I6yZvHzM00GXAujNFH'

BRAINTREE_MERCHANT_ID = 'ypwk6jkdkhn6c3jx'
BRAINTREE_PUBLIC_KEY = 'mrzs5jtfmvmkzkjv'
BRAINTREE_PRIVATE_KEY = 'f49af70c2659139cf6cdf926b8fc253d'

PRINTFUL_KEY = '6bhck2wu-onuj-xp2n:ltb0-wsfqq6pskkwe'

EMAIL_HOST = "mail.privateemail.com"
EMAIL_PORT = "465"
EMAIL_HOST_USER = "admin@tauruscanisrex.com"
EMAIL_HOST_PASSWORD = "SenorCerdo2013!"
EMAIL_USE_SSL = True

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

django_heroku.settings(locals())
