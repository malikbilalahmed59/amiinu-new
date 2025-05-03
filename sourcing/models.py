from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import string
import random


def generate_reference_number():
    # Don't check for uniqueness during migrations
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


class SourcingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('review', 'Under Review'),
        ('quotation_sent', 'Quotation Sent'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('quotation_rejected', 'Quotation Rejected')
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

    def delete(self, *args, **kwargs):
        # Ensure related quotation and shipping records are deleted first
        # This helps prevent the issue where deletion leaves orphaned records
        if hasattr(self, 'quotation'):
            self.quotation.delete()
        if hasattr(self, 'shipping'):
            self.shipping.delete()
        super().delete(*args, **kwargs)


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='quotation')
    air_shipment_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sea_shipment_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    truck_shipment_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    note = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(null=True, blank=True)

    sent_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Quotation for {self.sourcing_request.name} - {self.sourcing_request.user.username}"


class Shipping(models.Model):
    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='shipping')
    tracking_number = models.CharField(max_length=255, blank=True, null=True)
    shipped_date = models.DateTimeField(blank=True, null=True)
    estimated_delivery_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Shipping for {self.sourcing_request.name} - {self.sourcing_request.user.username}"


@receiver(post_save, sender=Quotation)
def update_sourcing_request_status(sender, instance, **kwargs):
    """
    Update SourcingRequest status when Quotation status changes
    """
    sourcing_request = instance.sourcing_request

    if instance.status == 'rejected':
        sourcing_request.status = 'quotation_rejected'
        sourcing_request.save()
    elif instance.status == 'accepted':
        sourcing_request.status = 'quotation_sent'
        sourcing_request.save()