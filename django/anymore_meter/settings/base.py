# django/anymore_meter/settings/base.py
"""
Django settings for anymore_meter project.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config
from celery.schedules import crontab
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = config('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "local.anymore-meter.co.jp", '*', 'testserver']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'storages',
    'simple_history',
    'djoser',
    'django_celery_beat',
    'django_rest_passwordreset',
    'app.meters',
    'app.readings',
    'app.billing',
    'app.keys',
    'app.alerts',
    'app.user',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'anymore_meter.urls'

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'anymore_meter',
        'USER': 'root',
        'HOST': '',
        'PORT': '',
        'PASSWORD': '11921111',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

AUTH_USER_MODEL = 'user.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True

from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers)

CORS_EXPOSE_HEADERS = [
    'X-Filename',
    'Content-Disposition',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60*24)
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.ap-northeast-1.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'no-reply@anymore-meter.co.jp'

FRONT_URL = 'http://localhost:8080/'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Asia/Tokyo'
CELERY_ENABLE_UTC = False
CELERY_RESULT_BACKEND_MAX_RETRIES = 10
CELERY_TASK_RESULT_EXPIRES = 3600

CELERY_BEAT_SCHEDULE = {
    'aggregate-daily-readings': {
        'task': 'app.readings.tasks.aggregate_daily',
        'schedule': crontab(hour=1, minute=0),
    },
    'aggregate-monthly-readings': {
        'task': 'app.readings.tasks.aggregate_monthly',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),
    },
    'check-meter-alerts': {
        'task': 'app.alerts.tasks.check_communication_alerts',
        'schedule': crontab(minute='*/30'),
    },
    # 請求集計（毎日AM6:00に実行）
    'generate-billing-summary': {
        'task': 'app.billing.tasks.generate_billing_summary',
        'schedule': crontab(hour=6, minute=0),
    },
    # processingタイムアウト処理（毎時0分に実行）
    'reset-stale-processing': {
        'task': 'app.billing.tasks.reset_stale_processing',
        'schedule': crontab(minute=0),
    },
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'app': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# 施工管理API連携
SEKOU_API_URL = config('SEKOU_API_URL', default='')
SEKOU_API_KEY = config('SEKOU_API_KEY', default='')

# Anymore連携用（Anymore → Meter の認証）
ANYMORE_API_KEY = config('ANYMORE_API_KEY', default='')

# AWS IoT Core
AWS_IOT_ENDPOINT = config('AWS_IOT_ENDPOINT', default='a3euups5uuz661-ats.iot.ap-northeast-1.amazonaws.com')
AWS_IOT_REGION = config('AWS_IOT_REGION', default='ap-northeast-1')
LAMBDA_API_KEY = config('LAMBDA_API_KEY', default='')