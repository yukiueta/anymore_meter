# django/app/billing/migrations/0003_remove_billingsummary_billing_sum_status_be5f39_idx_and_more.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_billingsummary'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billingsummary',
            name='status',
        ),
    ]