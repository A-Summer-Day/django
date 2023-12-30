"""
Django settings for axess_client_portal project.

Generated by 'django-admin startproject' using Django 3.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
from os import getenv
from django.urls.base import reverse_lazy
from dotenv import load_dotenv
from django.contrib.messages import constants as messages
from boto3.session import Session


load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-uf&=1p&4pzs^@qc=ot^*91khgu^=ywue8dwwq(d$%u2v+%wpat'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv('DEBUG', True)

ALLOWED_HOSTS = [
    getenv('APP_HOST', '127.0.0.1'),
    'api.axesslaw.com',
    '172.31.11.73'
    #'*',
]


# Application definition

INSTALLED_APPS = [
    'client_portal',
    'users',
    'api',
    'storages',
    'crispy_forms',
    'bootstrap4',
    'simple_salesforce',
    'mathfilters',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_api_key',
    'django_filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  
    ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'axess_client_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
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

WSGI_APPLICATION = 'axess_client_portal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': getenv('POSTGRES_USERNAME'),
        'PASSWORD': getenv('POSTGRES_PASSWORD'),
        'HOST': getenv('POSTGRES_HOST'),
        'PORT': getenv('POSTGRES_PORT')
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Toronto'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = BASE_DIR / 'uploads'
MEDIA_URL = '/files/'

AWS_STORAGE_BUCKET_NAME = 'axess-client-portal'
AWS_S3_REGION_NAME = 'us-east-2'
AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')

AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

STATICFILES_FOLDER = 'static'
MEDIAFILES_FOLDER = 'media'

STATICFILES_STORAGE = 'custom_storages.StaticFileStorage'
DEFAULT_FILE_STORAGE = 'custom_storages.MediaFileStorage'

LOGIN_REDIRECT_URL = reverse_lazy('client_portal:dashboard')
LOGOUT_REDIRECT_URL = reverse_lazy('login')
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

AUTH_USER_MODEL = 'users.User'

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'aws': {
            'format': '%(asctime)s [%(levelname)-8s] %(message)s [%(pathname)s:%(lineno)d]',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'watchtower': {
            'level': 'INFO',
            'class': 'watchtower.CloudWatchLogHandler',
            'boto3_session': Session(
                aws_access_key_id= getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key= getenv('AWS_SECRET_ACCESS_KEY'),
                region_name= 'ca-central-1'
            ),
            'log_group': 'AxessClientPortalLogs',\
            'stream_name': f'logs',
            'formatter': 'aws',
        },
        'console': {'class': 'logging.StreamHandler', 'formatter': 'aws',},
    },
    'loggers': {
        'watchtower': {'level': 'INFO', 'handlers': ['watchtower'], 'propogate': False,}
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey' 
EMAIL_HOST_PASSWORD = getenv('SENDGRID_API_KEY')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'autoemail@axesslaw.com'