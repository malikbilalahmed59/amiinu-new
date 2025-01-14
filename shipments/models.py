from django.db import models
from django.contrib.auth import get_user_model

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
]

CONTAINER_TYPES = [
    ('20FR', "20' FLAT RACK CNTR(S)"),
    ('20OT', "20' OPEN TOP CNTR(S)"),
    ('20PL', "20' PLATFORM(S)"),
    ('20RE', "20' REEFER(S)"),
    ('40HR', "40' HIGH CUBE REEFER(S)"),
    ('40FR', "40' FLAT RACK CNTR(S)"),
    ('40RE', "40' REEFER(S)"),
    ('40OT', "40' OPEN TOP CNTR(S)"),
    ('40PL', "40' PLATFORM(S)"),
    ('40ST', "40' STANDARD CNTR(S)"),
    ('40HC', "40' HIGH CUBE CNTR(S)"),
    ('20ST', "20' STANDARD CNTR(S)"),
]

PACKAGE_TYPES = [
    ('boxes', 'Boxes'),
    ('crates', 'Crates'),
    ('pallets', 'Pallets'),
    ('wooden_box', 'Wooden Box'),]

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
    international_shipping_type = models.CharField(max_length=20, choices=INTERNATIONAL_SHIPPING_TYPES, null=True, blank=True)
    incoterm = models.CharField(max_length=10, choices=INCOTERMS)
    special_instructions = models.TextField(null=True, blank=True)
    insure_shipment = models.BooleanField(default=False)
    insurance_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    pickup_date = models.DateField()
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.EmailField()
    recipient_phone = models.CharField(max_length=20)
    receiver_name = models.CharField(max_length=255)
    receiver_email = models.EmailField()
    receiver_phone = models.CharField(max_length=20)
    receiver_vat_no = models.CharField(max_length=50, null=True, blank=True, help_text="Receiver's VAT number")
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment {self.id} ({self.shipment_type})"

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
    description = models.TextField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    weight_per_unit = models.FloatField(help_text="Weight per unit in kg")
    hs_code = models.CharField(max_length=10, help_text="Harmonized System Code for customs classification")

    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.name} (Qty: {self.quantity}) in Container {self.container.id}"

