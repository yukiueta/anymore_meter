# django/app/billing/migrations/0002_billingsummary.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('meters', '0004_historicalmeterassignment_base_billing_day_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingCalendar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zone', models.IntegerField(choices=[(0, '未設定'), (1, '北海道電力管轄'), (2, '東北電力管轄'), (3, '東京電力管轄'), (4, '中部電力管轄'), (5, '北陸電力管轄'), (6, '関西電力管轄'), (7, '中国電力管轄'), (8, '四国電力管轄'), (9, '九州電力管轄'), (10, '沖縄電力管轄')], verbose_name='電力管轄')),
                ('fiscal_year', models.IntegerField(verbose_name='年度')),
                ('base_billing_day', models.CharField(max_length=2, verbose_name='基準検針日')),
                ('month', models.IntegerField(verbose_name='月')),
                ('actual_billing_date', models.DateField(verbose_name='実検針日')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '検針日カレンダー',
                'verbose_name_plural': '検針日カレンダー',
                'db_table': 'billing_calendars',
            },
        ),
        migrations.CreateModel(
            name='BillingSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.IntegerField(blank=True, null=True, verbose_name='案件ID')),
                ('project_name', models.CharField(blank=True, default='', max_length=500, verbose_name='案件名')),
                ('zone', models.IntegerField(default=0, verbose_name='電力管轄')),
                ('base_billing_day', models.CharField(blank=True, default='', max_length=2, verbose_name='基準検針日')),
                ('period_start', models.DateField(verbose_name='検針期間開始')),
                ('period_end', models.DateField(verbose_name='検針期間終了')),
                ('actual_kwh', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='実測kWh')),
                ('deemed_kwh', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='みなしkWh')),
                ('total_kwh', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='合計kWh')),
                ('deemed_method', models.CharField(choices=[('none', 'なし'), ('daily', '6kWh/日'), ('monthly', '180kWh/月')], default='none', max_length=10, verbose_name='みなし方法')),
                ('is_first_billing', models.BooleanField(default=False, verbose_name='初回請求')),
                ('prev_actual_value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='前回実測累計値')),
                ('curr_actual_value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='今回実測累計値')),
                ('mid_actual_value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='期間中最新累計値')),
                ('mid_actual_date', models.DateField(blank=True, null=True, verbose_name='期間中最新データ日')),
                ('prev_used_value', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='前回使用値')),
                ('curr_used_value', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='今回使用値')),
                ('fetch_status', models.CharField(choices=[('pending', '未処理'), ('processing', '処理中'), ('completed', '処理完了'), ('error', 'エラー')], default='pending', max_length=20, verbose_name='取得ステータス')),
                ('fetch_started_at', models.DateTimeField(blank=True, null=True, verbose_name='取得開始日時')),
                ('fetch_completed_at', models.DateTimeField(blank=True, null=True, verbose_name='取得完了日時')),
                ('fetch_error_message', models.TextField(blank=True, default='', verbose_name='エラーメッセージ')),
                ('note', models.TextField(blank=True, default='', verbose_name='備考')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_summaries', to='meters.meter')),
            ],
            options={
                'verbose_name': '請求サマリ',
                'verbose_name_plural': '請求サマリ',
                'ordering': ['-period_end', 'meter_id'],
            },
        ),
    ]