# django/app/readings/models.py
from django.db import models
from app.meters.models import Meter


class MeterReading(models.Model):
    """30分値データ（メーターからの生データ）"""
    READING_TYPE_CHOICES = [
        ('instant', '瞬時値'),
        ('interval', '30分値'),
    ]

    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='readings', verbose_name='メーター')
    timestamp = models.DateTimeField(verbose_name='計測日時')
    reading_type = models.CharField(max_length=10, choices=READING_TYPE_CHOICES, default='interval', verbose_name='種別')
    
    # PV発電（パワコンから）- 累計値
    import_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='発電量累計(kWh)')
    export_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='逆潮流累計(kWh)')
    
    # Bルート（電力スマメから）- 累計値
    route_b_import_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='買電累計(kWh)')
    route_b_export_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='売電累計(kWh)')
    
    # メタ情報
    raw_data = models.TextField(blank=True, default='', verbose_name='生データ(HEX)')
    received_at = models.DateTimeField(auto_now_add=True, verbose_name='受信日時')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meter_readings'
        verbose_name = '30分データ'
        verbose_name_plural = '30分データ'
        unique_together = ['meter', 'timestamp', 'reading_type']
        indexes = [
            models.Index(fields=['meter', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f'{self.meter.meter_id} - {self.timestamp}'


class MeterEvent(models.Model):
    """メーターイベントログ"""
    EVENT_CODE_CHOICES = [
        ('W1', 'Wi-SUN通信回復'),
        ('L1', 'LTE通信回復'),
        ('D1', 'リレースイッチ開閉'),
        ('A0', '停電(1週間/3週間)'),
        ('A2', '停電(1週間/3週間)'),
        ('RTC', 'RTC異常'),
        ('ERR', 'モジュールエラー'),
    ]

    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='events', verbose_name='メーター')
    timestamp = models.DateTimeField(verbose_name='発生日時')
    record_no = models.IntegerField(verbose_name='レコード番号')
    event_code = models.CharField(max_length=10, verbose_name='イベントコード')
    event_description = models.CharField(max_length=100, blank=True, default='', verbose_name='イベント説明')
    
    # イベント発生時の値
    import_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='発電量(kWh)')
    
    raw_data = models.TextField(blank=True, default='', verbose_name='生データ(HEX)')
    received_at = models.DateTimeField(auto_now_add=True, verbose_name='受信日時')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meter_events'
        verbose_name = 'イベントログ'
        verbose_name_plural = 'イベントログ'
        indexes = [
            models.Index(fields=['meter', 'timestamp']),
            models.Index(fields=['event_code']),
        ]

    def __str__(self):
        return f'{self.meter.meter_id} - {self.event_code} - {self.timestamp}'


class DailySummary(models.Model):
    """日次集計"""
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='daily_summaries', verbose_name='メーター')
    date = models.DateField(verbose_name='日付')
    
    # 発電量（当日の増分）
    generation_kwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='発電量(kWh)')
    export_kwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='売電量(kWh)')
    self_consumption_kwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='自家消費量(kWh)')
    
    # Bルート（当日の増分）
    grid_import_kwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='買電量(kWh)')
    
    # メタ情報
    record_count = models.IntegerField(default=0, verbose_name='レコード数')
    calculated_at = models.DateTimeField(auto_now=True, verbose_name='集計日時')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_summaries'
        verbose_name = '日次集計'
        verbose_name_plural = '日次集計'
        unique_together = ['meter', 'date']
        indexes = [
            models.Index(fields=['meter', 'date']),
        ]

    def __str__(self):
        return f'{self.meter.meter_id} - {self.date}'


class MonthlySummary(models.Model):
    """月次集計"""
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='monthly_summaries', verbose_name='メーター')
    year_month = models.CharField(max_length=7, verbose_name='年月')  # 2026-01
    
    # 発電量（当月の増分）
    generation_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='発電量(kWh)')
    export_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='売電量(kWh)')
    self_consumption_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='自家消費量(kWh)')
    
    # Bルート（当月の増分）
    grid_import_kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='買電量(kWh)')
    
    calculated_at = models.DateTimeField(auto_now=True, verbose_name='集計日時')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_summaries'
        verbose_name = '月次集計'
        verbose_name_plural = '月次集計'
        unique_together = ['meter', 'year_month']
        indexes = [
            models.Index(fields=['meter', 'year_month']),
        ]

    def __str__(self):
        return f'{self.meter.meter_id} - {self.year_month}'