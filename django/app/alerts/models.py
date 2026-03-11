from django.db import models
from app.meters.models import Meter


class Alert(models.Model):
    STATUS_CHOICES = [
        ('open', '発生中'),
        ('resolved', '解決済'),
    ]

    TYPE_CHOICES = [
        ('communication', '通信途絶'),
        ('anomaly', '異常値'),
    ]

    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='alerts', verbose_name='メーター')
    alert_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='種別')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name='ステータス')
    message = models.TextField(verbose_name='メッセージ')
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name='検知日時')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='解決日時')
    note = models.TextField(blank=True, default='', verbose_name='メモ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'
        verbose_name = 'アラート'
        verbose_name_plural = 'アラート'

    def __str__(self):
        return f'{self.meter.meter_id} - {self.alert_type} - {self.status}'