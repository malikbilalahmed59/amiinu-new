# Generated by Django 5.1.4 on 2025-03-07 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0006_shipment_estimated_delivery_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='value',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
