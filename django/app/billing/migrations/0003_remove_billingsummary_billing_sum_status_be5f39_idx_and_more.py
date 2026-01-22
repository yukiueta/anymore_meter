# django/app/billing/migrations/0003_remove_billingsummary_billing_sum_status_be5f39_idx_and_more.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_billingsummary'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='billingsummary',
            name='billing_sum_status_be5f39_idx',
        ),
        migrations.RemoveField(
            model_name='billingsummary',
            name='status',
        ),
        migrations.AddIndex(
            model_name='billingsummary',
            index=models.Index(fields=['zone', 'period_end'], name='billing_sum_zone_ef88f0_idx'),
        ),
    ]
