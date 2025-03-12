import uuid
from datetime import datetime

from django.db import models
from django.conf import settings
from django.utils import timezone
class Warehouse(models.Model):
    country = models.CharField(max_length=100)
    address = models.JSONField(help_text="Address as {'label': str, 'value': str}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.country


class InboundShipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inbound_shipments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inbound_shipments')
    tracking_number = models.CharField(max_length=255, unique=True)
    shipment_number = models.CharField(max_length=255, unique=True, blank=True)  # Added this field
    shipment_method = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Status timestamp fields
    pending_at = models.DateTimeField(auto_now_add=True)  # Set when created (default status is pending)
    in_transit_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.shipment_number:
            self.shipment_number = f"IN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Handle status timestamp fields
        if self.pk:
            old_instance = InboundShipment.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                now = timezone.now()

                if self.status == 'pending':
                    self.pending_at = now
                elif self.status == 'in_transit':
                    self.in_transit_at = now
                elif self.status == 'received':
                    self.received_at = now
                elif self.status == 'completed':
                    self.completed_at = now
                elif self.status == 'cancelled':
                    self.cancelled_at = now

        super().save(*args, **kwargs)
class Product(models.Model):
    inbound_shipments = models.ForeignKey(InboundShipment, related_name='products', on_delete=models.CASCADE)  # ✅ FIXED FIELD NAME
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    weight = models.FloatField(help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, help_text="Dimensions as 'L*W*H'")

    def __str__(self):
        return self.name

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True,blank=True, related_name='variations')
    type = models.CharField(max_length=100, help_text="Variation type (e.g., color, size)")

    def __str__(self):
        return f"{self.product.name} - {self.type}"

class VariationOption(models.Model):
    variation = models.ForeignKey(Variation,null=True,blank=True, on_delete=models.CASCADE, related_name='options')  # ✅ RELATES TO VARIATION
    name = models.CharField(max_length=100,null=True,blank=True, help_text="Option name (e.g., Red, Blue, Small)")
    quantity = models.PositiveIntegerField(default=0,null=True,blank=True)

    def __str__(self):
        return f"{self.variation.product.name} - {self.variation.type}: {self.name} ({self.quantity})"


class OutboundShipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='outbound_shipments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='outbound_shipments')
    customer_name = models.CharField(max_length=255)
    customer_address = models.JSONField(help_text="Address as {'label': str, 'value': str}")
    shipment_number = models.CharField(max_length=255, unique=True, blank=True)  # Added this field
    tracking_number = models.CharField(max_length=255, unique=True)
    shipment_method = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Status timestamp fields
    pending_at = models.DateTimeField(auto_now_add=True)  # Set when created (default status is pending)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        if not self.shipment_number:
            self.shipment_number = f"OUT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        # Handle status timestamp fields
        if self.pk:
            old_instance = OutboundShipment.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                now = timezone.now()

                if self.status == 'pending':
                    self.pending_at = now
                elif self.status == 'shipped':
                    self.shipped_at = now
                elif self.status == 'delivered':
                    self.delivered_at = now
                elif self.status == 'cancelled':
                    self.cancelled_at = now

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment  to {self.customer_name}"


# ✅ Outbound Shipment Product Selection
class OutboundShipmentItem(models.Model):
    outbound_shipment = models.ForeignKey(OutboundShipment, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='outbound_items')
    variation_option = models.ForeignKey(VariationOption, on_delete=models.CASCADE, related_name='outbound_items', null=True, blank=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} ({self.variation_option.name if self.variation_option else 'No Variation'}) - {self.quantity} pcs"