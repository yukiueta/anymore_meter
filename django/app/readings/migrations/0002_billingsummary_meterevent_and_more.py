#django/app/readings/migrations/0002_billingsummary_meterevent_and_more.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meters', '0003_historicalmeter_b_route_enabled_and_more'),
        ('readings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeterEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(verbose_name='発生日時')),
                ('record_no', models.IntegerField(verbose_name='レコード番号')),
                ('event_code', models.CharField(max_length=10, verbose_name='イベントコード')),
                ('event_description', models.CharField(blank=True, default='', max_length=100, verbose_name='イベント説明')),
                ('pv_import_kwh', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='PV順潮流(kWh)')),
                ('raw_data', models.TextField(blank=True, default='', verbose_name='生データ(HEX)')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='受信日時')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'イベントログ',
                'verbose_name_plural': 'イベントログ',
                'db_table': 'meter_events',
            },
        ),
        migrations.RemoveIndex(
            model_name='meterreading',
            name='meter_readi_meter_i_0bd391_idx',
        ),
        migrations.RemoveIndex(
            model_name='meterreading',
            name='meter_readi_recorde_c70b2a_idx',
        ),
        migrations.RenameField(
            model_name='meterreading',
            old_name='recorded_at',
            new_name='timestamp',
        ),
        migrations.RemoveField(
            model_name='dailysummary',
            name='total_export_kwh',
        ),
        migrations.RemoveField(
            model_name='dailysummary',
            name='total_import_kwh',
        ),
        migrations.RemoveField(
            model_name='dailysummary',
            name='total_pv_kwh',
        ),
        migrations.RemoveField(
            model_name='monthlysummary',
            name='total_export_kwh',
        ),
        migrations.RemoveField(
            model_name='monthlysummary',
            name='total_import_kwh',
        ),
        migrations.RemoveField(
            model_name='monthlysummary',
            name='total_pv_kwh',
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='売電量(kWh)'),
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='generation_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='発電量(kWh)'),
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='grid_export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='売電量_Bルート(kWh)'),
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='grid_import_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='買電量(kWh)'),
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='self_consumption_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='自家消費量(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='grid_export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='売電累計(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='grid_import_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='買電累計(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='pv_export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='PV逆潮流累計(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='pv_import_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='PV順潮流累計(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='raw_data',
            field=models.TextField(blank=True, default='', verbose_name='生データ(HEX)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='reading_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='総発電量累計(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='reading_type',
            field=models.CharField(choices=[('instant', '瞬時値'), ('interval', '30分値')], default='interval', max_length=10, verbose_name='種別'),
        ),
        migrations.AddField(
            model_name='monthlysummary',
            name='export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='売電量(kWh)'),
        ),
        migrations.AddField(
            model_name='monthlysummary',
            name='generation_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='発電量(kWh)'),
        ),
        migrations.AddField(
            model_name='monthlysummary',
            name='grid_export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='売電量_Bルート(kWh)'),
        ),
        migrations.AddField(
            model_name='monthlysummary',
            name='grid_import_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='買電量(kWh)'),
        ),
        migrations.AddField(
            model_name='monthlysummary',
            name='self_consumption_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='自家消費量(kWh)'),
        ),
        migrations.AddIndex(
            model_name='dailysummary',
            index=models.Index(fields=['meter', 'date'], name='daily_summa_meter_i_fa8edd_idx'),
        ),
        migrations.AddIndex(
            model_name='meterreading',
            index=models.Index(fields=['meter', 'timestamp'], name='meter_readi_meter_i_fc9657_idx'),
        ),
        migrations.AddIndex(
            model_name='meterreading',
            index=models.Index(fields=['timestamp'], name='meter_readi_timesta_121b28_idx'),
        ),
        migrations.AddIndex(
            model_name='monthlysummary',
            index=models.Index(fields=['meter', 'year_month'], name='monthly_sum_meter_i_c91d36_idx'),
        ),
        migrations.AddField(
            model_name='meterevent',
            name='meter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='meters.meter', verbose_name='メーター'),
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='export_kwh',
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='import_kwh',
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='pv_energy_kwh',
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='pyranometer',
        ),
        migrations.AddIndex(
            model_name='meterevent',
            index=models.Index(fields=['meter', 'timestamp'], name='meter_event_meter_i_e44377_idx'),
        ),
        migrations.AddIndex(
            model_name='meterevent',
            index=models.Index(fields=['event_code'], name='meter_event_event_c_191cd4_idx'),
        ),
    ]