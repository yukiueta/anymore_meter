from django.db import models
from app.meters.models import Meter


class MeterReading(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='readings', verbose_name='メーター')
    recorded_at = models.DateTimeField(verbose_name='計測日時')
    received_at = models.DateTimeField(auto_now_add=True, verbose_name='受信日時')
    import_kwh = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='買電量')
    export_kwh = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='売電量')
    pv_energy_kwh = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='発電量')
    pyranometer = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='日射量')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meter_readings'
        verbose_name = '30分データ'
        verbose_name_plural = '30分データ'
        indexes = [
            models.Index(fields=['meter', 'recorded_at']),
            models.Index(fields=['recorded_at']),
        ]

    def __str__(self):
        return f'{self.meter.meter_id} - {self.recorded_at}'


class DailySummary(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='daily_summaries', verbose_name='メーター')
    date = models.DateField(verbose_name='日付')
    total_import_kwh = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='買電量合計')
    total_export_kwh = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='売電量合計')
    total_pv_kwh = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='発電量合計')
    record_count = models.IntegerField(default=0, verbose_name='レコード数')
    calculated_at = models.DateTimeField(auto_now=True, verbose_name='集計日時')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_summaries'
        verbose_name = '日次集計'
        verbose_name_plural = '日次集計'
        unique_together = ['meter', 'date']

    def __str__(self):
        return f'{self.meter.meter_id} - {self.date}'


class MonthlySummary(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='monthly_summaries', verbose_name='メーター')
    year_month = models.CharField(max_length=7, verbose_name='年月')  # 2026-01
    total_import_kwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, verbose_name='買電量合計')
    total_export_kwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, verbose_name='売電量合計')
    total_pv_kwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, verbose_name='発電量合計')
    calculated_at = models.DateTimeField(auto_now=True, verbose_name='集計日時')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_summaries'
        verbose_name = '月次集計'
        verbose_name_plural = '月次集計'
        unique_together = ['meter', 'year_month']

    def __str__(self):
        return f'{self.meter.meter_id} - {self.year_month}'