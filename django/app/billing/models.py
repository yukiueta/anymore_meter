from django.db import models


class BillingCalendar(models.Model):
    """検針日カレンダー"""
    ZONE_CHOICES = [
        (0, '未設定'),
        (1, '北海道電力管轄'),
        (2, '東北電力管轄'),
        (3, '東京電力管轄'),
        (4, '中部電力管轄'),
        (5, '北陸電力管轄'),
        (6, '関西電力管轄'),
        (7, '中国電力管轄'),
        (8, '四国電力管轄'),
        (9, '九州電力管轄'),
        (10, '沖縄電力管轄'),
    ]

    zone = models.IntegerField(choices=ZONE_CHOICES, verbose_name='電力管轄')
    fiscal_year = models.IntegerField(verbose_name='年度')  # 2025
    base_billing_day = models.CharField(max_length=2, verbose_name='基準検針日')  # 01-26
    month = models.IntegerField(verbose_name='月')  # 1-12
    actual_billing_date = models.DateField(verbose_name='実検針日')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_calendars'
        verbose_name = '検針日カレンダー'
        verbose_name_plural = '検針日カレンダー'
        unique_together = ['zone', 'fiscal_year', 'base_billing_day', 'month']
        indexes = [
            models.Index(fields=['zone', 'fiscal_year', 'base_billing_day']),
            models.Index(fields=['actual_billing_date']),
        ]

    def __str__(self):
        return f'{self.get_zone_display()} {self.fiscal_year}年度 基準{self.base_billing_day} {self.month}月'

    @classmethod
    def get_zone_choices(cls):
        return cls.ZONE_CHOICES


class BillingSummary(models.Model):
    """検針期間ごとの請求用サマリ"""
    
    DEEMED_METHOD_CHOICES = [
        ('none', 'なし'),
        ('daily', '6kWh/日'),
        ('monthly', '180kWh/月'),
    ]
    
    FETCH_STATUS_CHOICES = [
        ('pending', '未処理'),
        ('processing', '処理中'),
        ('completed', '処理完了'),
        ('error', 'エラー'),
    ]
    
    class Meta:
        verbose_name = '請求サマリ'
        verbose_name_plural = '請求サマリ'
        ordering = ['-period_end', 'meter_id']
        unique_together = ['meter', 'period_start', 'period_end']
    
    # 基本情報
    meter = models.ForeignKey('meters.Meter', on_delete=models.CASCADE, related_name='billing_summaries')
    project_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name='案件ID')
    project_name = models.CharField(max_length=500, blank=True, default='', verbose_name='案件名')
    zone = models.IntegerField(default=0, db_index=True, verbose_name='電力管轄')
    base_billing_day = models.CharField(max_length=2, blank=True, default='', verbose_name='基準検針日')
    
    # 検針期間
    period_start = models.DateField(db_index=True, verbose_name='検針期間開始')
    period_end = models.DateField(db_index=True, verbose_name='検針期間終了')
    
    # 実測累計値（nullなら欠損）
    prev_actual_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='前回実測累計値')
    curr_actual_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='今回実測累計値')
    
    # 期間中最新データ（今回欠損時に使用）
    mid_actual_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='期間中最新累計値')
    mid_actual_date = models.DateField(null=True, blank=True, verbose_name='期間中最新データ日')
    
    # 計算に使った値
    prev_used_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='前回使用値')
    curr_used_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='今回使用値')
    
    # 使用量
    actual_kwh = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='実測kWh')
    deemed_kwh = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='みなしkWh')
    total_kwh = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='合計kWh')
    
    # みなし方法
    deemed_method = models.CharField(max_length=10, choices=DEEMED_METHOD_CHOICES, default='none', verbose_name='みなし方法')
    
    # フラグ・備考
    is_first_billing = models.BooleanField(default=False, verbose_name='初回請求')
    note = models.TextField(blank=True, default='', verbose_name='備考')
    
    # Anymore連携ステータス
    fetch_status = models.CharField(max_length=20, choices=FETCH_STATUS_CHOICES, default='pending', db_index=True, verbose_name='取得ステータス')
    fetch_started_at = models.DateTimeField(null=True, blank=True, verbose_name='取得開始日時')
    fetch_completed_at = models.DateTimeField(null=True, blank=True, verbose_name='取得完了日時')
    fetch_error_message = models.TextField(blank=True, default='', verbose_name='エラーメッセージ')
    
    # メタ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.meter_id} {self.period_start}〜{self.period_end}"