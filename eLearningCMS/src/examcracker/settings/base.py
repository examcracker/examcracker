"""
Django settings for examcracker project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from django.urls import reverse_lazy
from pathlib import Path
import os
import sys

# Build paths inside the project like this: BASE_DIR / "directory"
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATICFILES_DIRS = [str(BASE_DIR / 'static'), ]
MEDIA_ROOT = str(BASE_DIR / 'media')
MEDIA_URL = "/media/"
BINARY_ROOT = str(BASE_DIR / 'bin' / sys.platform)

os.environ["PATH"] = os.environ["PATH"] + ";" + BINARY_ROOT

# Use Django templates using the new Django 1.8 TEMPLATES settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            str(BASE_DIR / 'templates'),
            # insert more TEMPLATE_DIRS here
            str(BASE_DIR / 'student' / 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Use 12factor inspired environment variables or from a file
import environ
env = environ.Env()

# Create a local.env file in the settings directory
# But ideally this env file should be outside the git repo
env_file = Path(__file__).resolve().parent / 'local.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = []

# Captcha settings
RECAPTCHA_PUBLIC_KEY = '6LeooVkUAAAAANcm2d0EvhOzz_uv8yhdxDbuxz9B'
RECAPTCHA_PRIVATE_KEY = '6LeooVkUAAAAAPvOY22Dp8RkyIXM2d0P4opaLdcA'

# Email settings
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'mygyaanhive@gmail.com'
#EMAIL_HOST_PASSWORD = 'gyaanhive123'
#EMAIL_USE_TLS = True
#DEFAULT_FROM_EMAIL = 'GyaanHive <mygyaanhive@gmail.com>'

EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mygyaanhive@yahoo.com'
EMAIL_HOST_PASSWORD = 'examcracker2018'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'GyaanHive <mygyaanhive@yahoo.com>'

# Pusher settings
PUSHER_APP_ID = "656749"
PUSHER_KEY = "3ff394e3371be28d8abd"
PUSHER_SECRET = "35f5a7cde33cd756c30d"
PUSHER_CLUSTER = "ap2"

# Vimeo settings
VIMEO_CLIENT_ID = '0dabe4d1dc86c61dabf843461f3d57029a6e9b9c'
VIMEO_CLIENT_SECRET = 'RlQwRiXMayDSLIZbLZYRjlMjM1k45FS55PnW1WihX7emqzdWARm8CVf3RkwXYErJ1NcVWmnkZ6O2B9nvwOCuh/ORczcnsfl5XD0Mr3vMVxzarQwwm1DH4cVLFRXJ0qbB'
VIMEO_ACCESS_TOKEN = '69aaa4c6d5f05991df55ddf3d3955240'

# Web socket details
ASGI_APPLICATION = 'examcracker.routing.application'

# JW settings
JWPLAYER_API_KEY = '03IfLqqB'
JWPLAYER_API_SECRET = 'AK6y0bBoyEOHASfYwE5xUnWw'

JWPLAYER_DEV_ACC_API_KEY = 'avfMTzPK'
JWPLAYER_DEV_ACC_API_SECRET='k7HIvXAueCNF0G7I8A88Ecor'

# Digital ocean keys
DIGITAL_OCEAN_SPACE_KEY = 'V2ERLGS6TEFEJMD7OVYE'
DIGITAL_OCEAN_SPACE_KEY_SECRET = '+Q+Yn9dRjlAgussQ0KDXXPCr0q7d9jCDgq6LJMaZlPw'

PROVIDER_APPROVAL_NEEDED = True
COURSE_ENROLLING_ALLOWED = False

DRM_KEY_ID = "a7e61c373e219033c21091fa607bf3b8"
DRM_KEY = "76a6c65c5ea762046bd749a2e632ccbb"

# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'authtools',
    'crispy_forms',
    'easy_thumbnails',

    # django packages
    'snowpenguin.django.recaptcha2',
    'paypal.standard.ipn',
    'django_user_agents',

    # applications
    'profiles',
    'accounts',
    'provider',
    'student',
    'course',
    'payments',
    'access',
    'notification',
    'cdn',
    'schedule',

    # django rest api packages
    'rest_framework',
)

PAYPAL_RECEIVER_EMAIL = 'eexamcracker@gmail.com'
PAYPAL_TEST = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # other middlewares...
    'django_user_agents.middleware.UserAgentMiddleware',
]

# Cache backend is optional, but recommended to speed up user agent parsing

ROOT_URLCONF = 'examcracker.urls'

WSGI_APPLICATION = 'examcracker.wsgi.application'

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
  'default': env.db(),
}

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'postgres',                      
#        'USER': 'postgres',
#        'PASSWORD': 'postgres',
#        'HOST': 'localhost',
#        'PORT': '5432',
#    }
# }

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'

ALLOWED_HOSTS = []

# Crispy Form Theme - Bootstrap 3
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# For Bootstrap 3, change error alert to 'danger'
from django.contrib import messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

# Authentication Settings
AUTH_USER_MODEL = 'authtools.User'
LOGIN_REDIRECT_URL = reverse_lazy("home")
LOGIN_URL = reverse_lazy("accounts:login")

THUMBNAIL_EXTENSION = 'png'     # Or any extn for your thumbnails

# Cookie Settings
USER_AUTH_COOKIE_UPDATE_IN_DAYS = 3
USER_AUTH_COOKIE_AGE = 3*24*60*60
USER_AUTH_COOKIE = 'GHUSERAUTH'
USER_AUTH_COOKIE_DEFAULT_VALUE = 'unenrolleduser'
NUMBER_ALLOWED_DEVICES = 2
NUMBER_OF_COOKIE_MISS = 3


# Media server settings

MEDIA_SERVER_IP = '139.59.32.199'
MEDIA_SERVER_HTTP_PORT = '8080'
MEDIA_SERVER_HTTPS_PORT = '443'
MEDIA_SERVER_APP = 'gyaanhive'
MEDIA_SERVER_SUB_DOMAIN = 'www.live.gyaanhive.com'

