from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    APP_CHOICES = [
        ('sourcing', 'Sourcing'),
        ('shipment', 'Shipment'),
        ('warehouse', 'Warehouse'),
    ]

    NOTIFICATION_TYPES = [
        # Sourcing notifications
        ('sourcing_status', 'Sourcing Status Update'),
        ('quotation_created', 'Quotation Created'),
        ('quotation_updated', 'Quotation Updated'),
        ('sourcing_shipping_status', 'Sourcing Shipping Status Update'),

        # Shipment notifications
        ('shipment_created', 'Shipment Created'),
        ('shipment_status', 'Shipment Status Update'),
        ('shipment_tracking', 'Tracking Number Added'),
        ('shipment_payment', 'Shipment Payment Status'),

        # Warehouse notifications
        ('inbound_status', 'Inbound Shipment Status'),
        ('inbound_created', 'Inbound Shipment Created'),
        ('outbound_created', 'Outbound Shipment Created'),
        ('outbound_status', 'Outbound Shipment Status'),
        ('inventory_update', 'Inventory Update'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    app_name = models.CharField(max_length=20, choices=APP_CHOICES)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()

    # Generic relation for linking to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional metadata
    reference_number = models.CharField(max_length=50, null=True, blank=True)
    reference_url = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['app_name', 'user']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.app_name} - {self.title}"