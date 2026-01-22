# django/app/keys/models.py
from django.db import models
from simple_history.models import HistoricalRecords
from app.meters.models import Meter


class MeterKey(models.Model):
    """メーター暗号鍵管理"""
    meter = models.OneToOneField(Meter, on_delete=models.CASCADE, related_name='key', verbose_name='メーター')
    
    # 暗号鍵（16バイト = 32文字HEX）
    master_key = models.CharField(max_length=64, verbose_name='マスターキー')
    data_key = models.CharField(max_length=64, verbose_name='データキー')
    
    # 鍵管理
    key_version = models.IntegerField(default=1, verbose_name='鍵バージョン')
    registered_at = models.DateTimeField(null=True, blank=True, verbose_name='初回鍵交換日時')
    last_key_exchange = models.DateTimeField(null=True, blank=True, verbose_name='最終鍵交換日時')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'meter_keys'
        verbose_name = 'メーターキー'
        verbose_name_plural = 'メーターキー'

    def __str__(self):
        return f'{self.meter.meter_id} keys (v{self.key_version})'

    @property
    def is_registered(self):
        """初回鍵交換が完了しているか"""
        return self.registered_at is not None