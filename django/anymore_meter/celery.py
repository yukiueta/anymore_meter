# anymore_meter/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anymore_meter.settings.local')

app = Celery('anymore_meter')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)