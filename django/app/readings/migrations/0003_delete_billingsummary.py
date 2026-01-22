# 0003

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('readings', '0002_billingsummary_meterevent_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BillingSummary',
        ),
    ]
