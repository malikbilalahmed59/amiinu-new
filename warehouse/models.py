from django.db import models
from django.conf import settings

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
    shipment_method = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
