# django/app/meters/models.py
from django.db import models
from simple_history.models import HistoricalRecords
from app.billing.models import BillingCalendar


class Meter(models.Model):
    STATUS_CHOICES = [
        ('inactive', '未稼働'),
        ('pending', '登録待ち'),
        ('active', '稼働中'),
        ('error', 'エラー'),
    ]

    meter_id = models.CharField(max_length=20, unique=True, verbose_name='メーターID')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive', verbose_name='ステータス')
    
    # Bルート設定
    b_route_enabled = models.BooleanField(default=True, verbose_name='Bルート有効')
    b_route_id = models.CharField(max_length=32, blank=True, default='', verbose_name='BルートID')
    b_route_password = models.CharField(max_length=12, blank=True, default='', verbose_name='Bルートパスワード')
    
    # 日時
    installed_at = models.DateField(null=True, blank=True, verbose_name='設置日')
    registered_at = models.DateTimeField(null=True, blank=True, verbose_name='初回登録日時')
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

    @property
    def current_assignment(self):
        return self.assignments.filter(end_date__isnull=True).first()

    @property
    def current_project_id(self):
        assignment = self.current_assignment
        return assignment.project_id if assignment else None

    @property
    def setup_status(self):
        """セットアップ状態を返す"""
        assignment = self.current_assignment
        if not assignment:
            return 'unlinked'
        if not assignment.zone:
            return 'zone_missing'
        if not assignment.base_billing_day:
            return 'billing_day_missing'
        return 'complete'


class MeterAssignment(models.Model):
    """メーターと案件の紐付け（履歴管理）"""
    ZONE_CHOICES = BillingCalendar.ZONE_CHOICES

    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='assignments', verbose_name='メーター')
    project_id = models.IntegerField(verbose_name='案件ID')
    project_name = models.CharField(max_length=200, blank=True, default='', verbose_name='案件名')
    zone = models.IntegerField(choices=ZONE_CHOICES, null=True, blank=True, verbose_name='電力管轄')
    base_billing_day = models.CharField(max_length=2, blank=True, default='', verbose_name='基準検針日')
    
    start_date = models.DateField(verbose_name='開始日')
    end_date = models.DateField(null=True, blank=True, verbose_name='終了日')
    synced_at = models.DateTimeField(null=True, blank=True, verbose_name='最終同期日時')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'meter_assignments'
        verbose_name = 'メーター紐付け'
        verbose_name_plural = 'メーター紐付け'
        indexes = [
            models.Index(fields=['meter', 'end_date']),
            models.Index(fields=['project_id']),
            models.Index(fields=['zone', 'base_billing_day']),
        ]

    def __str__(self):
        return f'{self.meter.meter_id} - {self.project_name or self.project_id}'

    @property
    def zone_display(self):
        return dict(self.ZONE_CHOICES).get(self.zone, '')