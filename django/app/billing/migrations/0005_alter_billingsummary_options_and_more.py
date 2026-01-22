# django/app/billing/migrations/0005_alter_billingsummary_options_and_more.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meters', '0004_historicalmeterassignment_base_billing_day_and_more'),
        ('billing', '0004_remove_billingsummary_data_missing_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='billingsummary',
            options={'ordering': ['-period_end', 'meter_id'], 'verbose_name': '請求サマリ', 'verbose_name_plural': '請求サマリ'},
        ),
        migrations.RemoveIndex(
            model_name='billingsummary',
            name='billing_sum_project_1f10a0_idx',
        ),
        migrations.RemoveIndex(
            model_name='billingsummary',
            name='billing_sum_period__f8c7b7_idx',
        ),
        migrations.RemoveIndex(
            model_name='billingsummary',
            name='billing_sum_zone_ef88f0_idx',
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='fetch_completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='取得完了日時'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='fetch_error_message',
            field=models.TextField(blank=True, default='', verbose_name='エラーメッセージ'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='fetch_started_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='取得開始日時'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='fetch_status',
            field=models.CharField(choices=[('pending', '未処理'), ('processing', '処理中'), ('completed', '処理完了'), ('error', 'エラー')], db_index=True, default='pending', max_length=20, verbose_name='取得ステータス'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='actual_kwh',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='実測kWh'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='base_billing_day',
            field=models.CharField(blank=True, default='', max_length=2, verbose_name='基準検針日'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='curr_used_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='今回使用値'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='deemed_kwh',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='みなしkWh'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='is_first_billing',
            field=models.BooleanField(default=False, verbose_name='初回請求'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='meter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_summaries', to='meters.meter'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='mid_actual_date',
            field=models.DateField(blank=True, null=True, verbose_name='期間中最新データ日'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='period_end',
            field=models.DateField(db_index=True, verbose_name='検針期間終了'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='period_start',
            field=models.DateField(db_index=True, verbose_name='検針期間開始'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='prev_used_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='前回使用値'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='project_id',
            field=models.IntegerField(blank=True, db_index=True, null=True, verbose_name='案件ID'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='project_name',
            field=models.CharField(blank=True, default='', max_length=500, verbose_name='案件名'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='total_kwh',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='合計kWh'),
        ),
        migrations.AlterField(
            model_name='billingsummary',
            name='zone',
            field=models.IntegerField(db_index=True, default=0, verbose_name='電力管轄'),
        ),
        migrations.AlterModelTable(
            name='billingsummary',
            table=None,
        ),
    ]
