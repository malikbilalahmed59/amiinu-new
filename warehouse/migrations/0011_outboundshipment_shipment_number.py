# Generated by Django 5.1.4 on 2025-03-12 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0010_inboundshipment_shipment_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='outboundshipment',
            name='shipment_number',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]
