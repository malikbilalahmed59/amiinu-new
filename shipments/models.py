# Updated models.py for shipment app

from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime
from suggestions.models import ShippingRoute, Country  # Import from suggestions app

User = get_user_model()

SHIPMENT_TYPES = [
    ('domestic', 'Domestic'),
    ('international', 'International'),
]

INTERNATIONAL_SHIPPING_TYPES = [
    ('economy_air', 'Economy Air'),
    ('express_air', 'Express Air'),
    ('fcl_sea', 'FCL (Full Container Load) Sea'),
    ('lcl_sea', 'LCL (Less than Container Load) Sea'),
    ('connect_plus', 'Connect Plus')
]

CONTAINER_TYPES = [
    ('20ST', "20' DRY STANDARD"),
    ('40ST', "40' DRY STANDARD"),
]

PACKAGE_TYPES = [
    ('boxes', 'Boxes'),
    ('crates', 'Crates'),
    ('pallets', 'Pallets'),
    ('wooden_box', 'Wooden Box'),
]

INCOTERMS = [
    ('FOB', 'FOB - Free On Board'),
    ('CPT', 'CPT - Carriage Paid To'),
    ('CIF', 'CIF - Cost, Insurance and Freight'),
    ('DAP', 'DAP - Delivered At Place'),
    ('DDP', 'DDP - Delivered Duty Paid'),
]


class Shipment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipments')
    shipment_type = models.CharField(max_length=20, choices=SHIPMENT_TYPES)
    international_shipping_type = models.CharField(max_length=20, choices=INTERNATIONAL_SHIPPING_TYPES, null=True,
                                                   blank=True)
    incoterm = models.CharField(max_length=10, choices=INCOTERMS)
    special_instructions = models.TextField(null=True, blank=True)
    insure_shipment = models.BooleanField(default=False)
    insurance_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pickup_address = models.JSONField(help_text="Stores the pickup address as {'label': str, 'value': str}")
    delivery_address = models.JSONField(help_text="Stores the delivery address as {'label': str, 'value': str}")
    pickup_date = models.DateField()
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.EmailField()
    recipient_phone = models.CharField(max_length=20)
    sender_tax_vat = models.CharField(max_length=50, blank=True, null=True)
    sender_email = models.EmailField()
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')],
                                      default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_dangerous_goods = models.BooleanField(default=False,
                                             help_text="Indicates if the shipment contains dangerous goods like batteries")
    is_one_percent_insured = models.BooleanField(default=False,
                                                 help_text="If true, 1% of order value is used as insurance")
    shipment_number = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('in_transit', 'In Transit'),
                                                      ('delivered', 'Delivered')], default='pending')
    estimated_delivery_date = models.DateTimeField(null=True, blank=True)
    tracking_company = models.CharField(max_length=100, null=True, blank=True)
    tracking_number = models.CharField(max_length=50, null=True, blank=True)
    total_weight = models.FloatField(default=0.0, null=True, blank=True,
                                     help_text="Sum of all container weights * quantity in kg")

    # New fields for profit tracking
    shipping_route = models.ForeignKey(
        'suggestions.ShippingRoute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments',
        help_text="The shipping route used for this shipment"
    )
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base cost from the shipping route"
    )
    profit_margin_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Profit margin percentage applied"
    )
    profit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual profit amount (delivery_price - base_cost)"
    )
    origin_country = models.ForeignKey(
        'suggestions.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='origin_shipments',
        help_text="Origin country for easier filtering"
    )
    destination_country = models.ForeignKey(
        'suggestions.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='destination_shipments',
        help_text="Destination country for easier filtering"
    )

    def save(self, *args, **kwargs):
        if not self.shipment_number:
            self.shipment_number = f"SHIP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Calculate profit if we have the necessary data
        if self.base_cost and self.delivery_price:
            self.profit_amount = self.delivery_price - self.base_cost

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment {self.shipment_number} ({self.shipment_type})"

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['origin_country', 'created_at']),
            models.Index(fields=['payment_status', 'created_at']),
            models.Index(fields=['status']),
        ]


class Container(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='containers')
    container_type = models.CharField(max_length=10, choices=CONTAINER_TYPES, null=True, blank=True)
    package_type = models.CharField(max_length=10, choices=PACKAGE_TYPES, null=True, blank=True)
    length = models.FloatField(help_text="Length in cm")
    width = models.FloatField(help_text="Width in cm")
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Container {self.id} for Shipment {self.shipment.id}"


class Product(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    hs_code = models.CharField(max_length=10, help_text="Harmonized System Code for customs classification")
    product_value = models.FloatField(null=True, blank=True)
    product_quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} (HS: {self.hs_code})"