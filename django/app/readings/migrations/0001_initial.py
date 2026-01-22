# 0001

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('meters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year_month', models.CharField(max_length=7, verbose_name='年月')),
                ('total_import_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True, verbose_name='買電量合計')),
                ('total_export_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True, verbose_name='売電量合計')),
                ('total_pv_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True, verbose_name='発電量合計')),
                ('calculated_at', models.DateTimeField(auto_now=True, verbose_name='集計日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_summaries', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': '月次集計',
                'verbose_name_plural': '月次集計',
                'db_table': 'monthly_summaries',
                'unique_together': {('meter', 'year_month')},
            },
        ),
        migrations.CreateModel(
            name='MeterReading',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recorded_at', models.DateTimeField(verbose_name='計測日時')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='受信日時')),
                ('import_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='買電量')),
                ('export_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='売電量')),
                ('pv_energy_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='発電量')),
                ('pyranometer', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='日射量')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': '30分データ',
                'verbose_name_plural': '30分データ',
                'db_table': 'meter_readings',
                'indexes': [models.Index(fields=['meter', 'recorded_at'], name='meter_readi_meter_i_0bd391_idx'), models.Index(fields=['recorded_at'], name='meter_readi_recorde_c70b2a_idx')],
            },
        ),
        migrations.CreateModel(
            name='DailySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='日付')),
                ('total_import_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='買電量合計')),
                ('total_export_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='売電量合計')),
                ('total_pv_kwh', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='発電量合計')),
                ('record_count', models.IntegerField(default=0, verbose_name='レコード数')),
                ('calculated_at', models.DateTimeField(auto_now=True, verbose_name='集計日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_summaries', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': '日次集計',
                'verbose_name_plural': '日次集計',
                'db_table': 'daily_summaries',
                'unique_together': {('meter', 'date')},
            },
        ),
    ]
