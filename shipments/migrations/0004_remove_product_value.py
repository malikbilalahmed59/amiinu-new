# Generated by Django 5.1.4 on 2025-02-02 20:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0003_product_value'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='value',
        ),
    ]
