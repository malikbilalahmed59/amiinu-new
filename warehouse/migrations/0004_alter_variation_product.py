# Generated by Django 5.1.4 on 2025-02-18 23:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0003_alter_product_inbound_shipments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='warehouse.product'),
        ),
    ]
