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
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mygyaanhive@gmail.com'
EMAIL_HOST_PASSWORD = 'gyaanhive123'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'GyaanHive <mygyaanhive@gmail.com>'

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

    # applications
    'profiles',
    'accounts',
    'provider',
    'student',
    'course',
    'payments',

    # django packages
    'snowpenguin.django.recaptcha2',
    'paypal.standard.ipn',
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
]

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
