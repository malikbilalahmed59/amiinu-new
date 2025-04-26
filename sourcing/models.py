from django.db import models
from django.conf import settings

import string
import random
from django.db import models
from django.conf import settings

def generate_reference_number():
    # Don't check for uniqueness during migrations
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


import random
import string
from django.conf import settings
from django.db import models


class SourcingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('review', 'Under Review'),
        ('quotation_sent', 'Quotation Sent'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sourcing_requests')
    name = models.CharField(max_length=255)
    description = models.TextField()
    quantity_needed = models.PositiveIntegerField()
    target_price = models.PositiveIntegerField()
    images = models.ImageField(upload_to='sourcing_requests/')
    whatsapp_number = models.CharField(max_length=20)
    address = models.JSONField(help_text="Address as {'label': str, 'value': str}")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reference_number = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.user.username} - {self.reference_number}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Get first 3 characters of username (or first 3 chars if username is shorter)
            user_prefix = self.user.username[:3].upper()

            while True:
                # Generate a random string
                random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
                # Combine user prefix with random string
                ref_number = f"{user_prefix}-{random_string}"

                # Check if this reference number already exists
                if not SourcingRequest.objects.filter(reference_number=ref_number).exists():
                    self.reference_number = ref_number
                    break

        super().save(*args, **kwargs)


class Quotation(models.Model):
    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='quotation')
    air_shipment_cost = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    truck_shipment_cost = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    note=models.TextField(null=True,blank=True)


    sent_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)  # Timestamp for when the quotation was sent
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)  # Payment amount
    payment_status = models.BooleanField(default=False)  # Payment status (Paid/Not Paid)
    payment_date = models.DateTimeField(blank=True, null=True)  # Payment date


    def __str__(self):
        return f"Quotation for {self.sourcing_request.name} - {self.sourcing_request.user.username}"



class Shipping(models.Model):
    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='shipping')
    tracking_number = models.CharField(max_length=255, blank=True, null=True)  # Tracking number
    shipped_date = models.DateTimeField(blank=True, null=True)  # Date of shipment
    estimated_delivery_date = models.DateTimeField(blank=True, null=True)  # Estimated delivery date

    def __str__(self):
        return f"Shipping for {self.sourcing_request.name} - {self.sourcing_request.user.username}"
