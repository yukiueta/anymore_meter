# 0004

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('readings', '0003_delete_billingsummary'),
    ]

    operations = [
        migrations.RenameField(
            model_name='meterreading',
            old_name='grid_export_kwh',
            new_name='route_b_export_kwh',
        ),
        migrations.RenameField(
            model_name='meterreading',
            old_name='grid_import_kwh',
            new_name='route_b_import_kwh',
        ),
        migrations.RemoveField(
            model_name='dailysummary',
            name='grid_export_kwh',
        ),
        migrations.RemoveField(
            model_name='meterevent',
            name='pv_import_kwh',
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='pv_export_kwh',
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='pv_import_kwh',
        ),
        migrations.RemoveField(
            model_name='meterreading',
            name='reading_kwh',
        ),
        migrations.RemoveField(
            model_name='monthlysummary',
            name='grid_export_kwh',
        ),
        migrations.AddField(
            model_name='meterevent',
            name='import_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='発電量(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='export_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='逆潮流累計(kWh)'),
        ),
        migrations.AddField(
            model_name='meterreading',
            name='import_kwh',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='発電量累計(kWh)'),
        ),
    ]
