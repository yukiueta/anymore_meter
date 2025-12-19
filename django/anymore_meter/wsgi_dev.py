# /anymore_meter/wsgi_dev.py
"""
WSGI config for anymore_meter project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anymore_meter.settings.dev')

application = get_wsgi_application()