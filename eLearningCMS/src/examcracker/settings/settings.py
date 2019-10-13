from .base import *             # NOQA
import sys
import logging.config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATES[0]['OPTIONS'].update({'debug': True})

# Turn off debug while imported by Celery with a workaround
# See http://stackoverflow.com/a/4806384
if "celery" in sys.argv[0]:
    DEBUG = False

STATIC_ROOT = "/home/3Idiots/eLearningCMS/eLearningCMS/src/static"

# Less strict password authentication and validation
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]
AUTH_PASSWORD_VALIDATORS = []

# Channels
ASGI_APPLICATION = 'examcracker.routing.application'

# Django Debug Toolbar
INSTALLED_APPS += (
    'debug_toolbar',)

# Additional middleware introduced by debug toolbar
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Show emails to console in DEBUG mode
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mygyaanhive@yahoo.com'
EMAIL_HOST_PASSWORD = 'examcracker2019'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'GyaanHive <mygyaanhive@yahoo.com>'

# Show thumbnail generation errors
THUMBNAIL_DEBUG = True

# Allow internal IPs for debugging
INTERNAL_IPS = [
    '127.0.0.1',
    '0.0.0.1',
]

ALLOWED_HOSTS = ['www.gyaanhive.com','www.kunal.gyaanhive.com']

if DEBUG is False:
    RECAPTCHA_PUBLIC_KEY = '6Ldum20UAAAAAEWoxXETng8qOScbkAdVLTJ7YN7_'
    RECAPTCHA_PRIVATE_KEY = '6Ldum20UAAAAAHp3pr7r1OWmbRdL7qwKOm2jPvK2'

# Log everything to the logs directory at the top
LOGFILE_ROOT = BASE_DIR.parent / 'logs'

# Reset logging
# (see http://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/)

LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'django_log_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': str(LOGFILE_ROOT / 'django.log'),
            'formatter': 'verbose'
        },
        'proj_log_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': str(LOGFILE_ROOT / 'project.log'),
            'formatter': 'verbose'
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['django_log_file'],
            'propagate': True,
            'level': 'ERROR',
        },
        'project': {
            'handlers': ['proj_log_file'],
            'level': 'ERROR',
        },
    }
}

logging.config.dictConfig(LOGGING)
