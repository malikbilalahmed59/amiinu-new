# Generated by Django 5.1.4 on 2025-03-09 20:07

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0007_outboundshipment_outboundshipmentitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='inboundshipment',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='inboundshipment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='inboundshipment',
            name='in_transit_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='inboundshipment',
            name='pending_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='outboundshipment',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='outboundshipment',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='outboundshipment',
            name='pending_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='outboundshipment',
            name='shipped_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
