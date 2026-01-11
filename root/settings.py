import os
from datetime import timedelta
from os.path import join
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from redis import Redis

from core.config import RedisConfig, EmailConfig, SecretConfig

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = SecretConfig.SECRET_KEY

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'unfold',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # my app
    'authentication',
    'app',
    # drf
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    # jwt
    'rest_framework_simplejwt',
]

ROOT_URLCONF = 'root.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'root.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _('English')),
    ('uz', _('Uzbek')),
    ('en', _('Russian')),
]

TIME_ZONE = 'Asia/Tashkent'

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'authentication.middleware.UserLanguageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'core.utils.RequestLoggingMiddleware'
]

STATIC_URL = 'static/'
STATIC_ROOT = join(BASE_DIR / 'static')

MEDIA_URL = 'media/'
MEDIA_ROOT = join(BASE_DIR, 'media')

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        "authentication.permissions.IsActiveUser",
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'PostStream',
    'DESCRIPTION': 'PostStream',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

SIMPLE_JWT = {
    "UPDATE_LAST_LOGIN": True,
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

AUTH_USER_MODEL = 'authentication.User'

redis = Redis.from_url(RedisConfig.CELERY_BROKER_URL, decode_responses=True)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = EmailConfig.EMAIL_USER
EMAIL_HOST_PASSWORD = EmailConfig.EMAIL_PASSWORD

CELERY_TASK_ALWAYS_EAGER = True

CELERY_BROKER_URL = RedisConfig.CELERY_BROKER_URL

CELERY_RESULT_BACKEND = RedisConfig.CELERY_BROKER_URL

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_TIMEZONE = 'Asia/Tashkent'

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} | {name} | {message}",
            "style": "{",
        },
        "request": {
            "format": "[{levelname}] {asctime} | {client_ip} | {method} {path} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file_debug": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "debug.log"),
            "formatter": "verbose",
        },
        "file_requests": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "requests.log"),
            "formatter": "request",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_debug"],
            "level": "DEBUG",
            "propagate": True,
        },
        "requests_logger": {
            "handlers": ["file_requests"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
