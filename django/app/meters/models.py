from django.db import models
from simple_history.models import HistoricalRecords


class Meter(models.Model):
    STATUS_CHOICES = [
        ('registered', '登録済み'),
        ('active', '稼働中'),
        ('inactive', '停止中'),
        ('offline', 'オフライン'),
    ]

    meter_id = models.CharField(max_length=20, unique=True, verbose_name='メーターID')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name='ステータス')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='登録日時')
    last_received_at = models.DateTimeField(null=True, blank=True, verbose_name='最終受信日時')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'meters'
        verbose_name = 'メーター'
        verbose_name_plural = 'メーター'

    def __str__(self):
        return self.meter_id


class MeterAssignment(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='assignments', verbose_name='メーター')
    project_id = models.IntegerField(verbose_name='案件ID')  # Anymore側のproject.id
    start_date = models.DateField(verbose_name='開始日')
    end_date = models.DateField(null=True, blank=True, verbose_name='終了日')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'meter_assignments'
        verbose_name = 'メーター紐付け'
        verbose_name_plural = 'メーター紐付け'

    def __str__(self):
        return f'{self.meter.meter_id} - Project {self.project_id}'