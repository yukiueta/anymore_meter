"""
ASGI config for anymore_meter project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anymore_meter.settings')

application = get_asgi_application()