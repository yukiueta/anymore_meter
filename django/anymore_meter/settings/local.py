from .base import *


DEBUG = True

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "https://local.anymore-meter.co.jp",
    "http://localhost:8082",  # マイページ追加
    "http://127.0.0.1:8082",  # マイページ追加
]

WSGI_APPLICATION = 'anymore_meter.wsgi_local.application'

import pymysql
pymysql.version_info = (1, 4, 6, 'final', 0)
pymysql.install_as_MySQLdb()

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

API_URL = 'http://127.0.0.1:8002/'
FRONT_URL = 'http://localhost:8080/'