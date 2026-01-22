# django/app/readings/migrations/0001_initial.py

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
                ('generation_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='発電量(kWh)')),
                ('export_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='売電量(kWh)')),
                ('self_consumption_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='自家消費量(kWh)')),
                ('grid_import_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='買電量(kWh)')),
                ('calculated_at', models.DateTimeField(auto_now=True, verbose_name='集計日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_summaries', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': '月次集計',
                'verbose_name_plural': '月次集計',
                'db_table': 'monthly_summaries',
            },
        ),
        migrations.CreateModel(
            name='MeterReading',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(verbose_name='計測日時')),
                ('reading_type', models.CharField(choices=[('instant', '瞬時値'), ('interval', '30分値')], default='interval', max_length=10, verbose_name='種別')),
                ('import_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='発電量累計(kWh)')),
                ('export_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='逆潮流累計(kWh)')),
                ('route_b_import_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='買電累計(kWh)')),
                ('route_b_export_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='売電累計(kWh)')),
                ('raw_data', models.TextField(blank=True, default='', verbose_name='生データ(HEX)')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='受信日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': '30分データ',
                'verbose_name_plural': '30分データ',
                'db_table': 'meter_readings',
            },
        ),
        migrations.CreateModel(
            name='MeterEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(verbose_name='発生日時')),
                ('record_no', models.IntegerField(verbose_name='レコード番号')),
                ('event_code', models.CharField(max_length=10, verbose_name='イベントコード')),
                ('event_description', models.CharField(blank=True, default='', max_length=100, verbose_name='イベント説明')),
                ('import_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='発電量(kWh)')),
                ('raw_data', models.TextField(blank=True, default='', verbose_name='生データ(HEX)')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='受信日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': 'イベントログ',
                'verbose_name_plural': 'イベントログ',
                'db_table': 'meter_events',
            },
        ),
        migrations.CreateModel(
            name='DailySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='日付')),
                ('generation_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='発電量(kWh)')),
                ('export_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='売電量(kWh)')),
                ('self_consumption_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='自家消費量(kWh)')),
                ('grid_import_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='買電量(kWh)')),
                ('record_count', models.IntegerField(default=0, verbose_name='レコード数')),
                ('calculated_at', models.DateTimeField(auto_now=True, verbose_name='集計日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_summaries', to='meters.meter', verbose_name='メーター')),
            ],
            options={
                'verbose_name': '日次集計',
                'verbose_name_plural': '日次集計',
                'db_table': 'daily_summaries',
            },
        ),
    ]