from django.db import models
from simple_history.models import HistoricalRecords
from app.meters.models import Meter


class MeterKey(models.Model):
    meter = models.OneToOneField(Meter, on_delete=models.CASCADE, related_name='key', verbose_name='メーター')
    master_key = models.CharField(max_length=64, verbose_name='マスターキー')
    data_key = models.CharField(max_length=64, verbose_name='データキー')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'meter_keys'
        verbose_name = 'メーターキー'
        verbose_name_plural = 'メーターキー'

    def __str__(self):
        return f'{self.meter.meter_id} keys'