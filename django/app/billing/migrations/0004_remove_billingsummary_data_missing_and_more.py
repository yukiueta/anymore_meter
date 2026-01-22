# django/app/billing/migrations/0004_remove_billingsummary_data_missing_and_more.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_remove_billingsummary_billing_sum_status_be5f39_idx_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billingsummary',
            name='data_missing',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='generation_kwh',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='import_end',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='import_start',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='route_b_export_end',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='route_b_export_start',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='self_consumption_kwh',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='sold_kwh',
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='actual_kwh',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='実測分(kWh)'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='curr_actual_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='今回実測累計値'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='curr_used_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='計算用今回値'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='deemed_kwh',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='みなし分(kWh)'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='deemed_method',
            field=models.CharField(choices=[('none', 'なし'), ('daily', '6kWh/日'), ('monthly', '180kWh/月')], default='none', max_length=10, verbose_name='みなし方法'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='is_first_billing',
            field=models.BooleanField(default=False, verbose_name='初回検針'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='mid_actual_date',
            field=models.DateField(blank=True, null=True, verbose_name='期間中最新データ日付'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='mid_actual_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='期間中最新累計値'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='prev_actual_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='前回実測累計値'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='prev_used_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='計算用前回値'),
        ),
        migrations.AddField(
            model_name='billingsummary',
            name='total_kwh',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='合計(kWh)'),
        ),
    ]
