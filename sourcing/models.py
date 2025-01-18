from django.db import models
from django.conf import settings

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
    images = models.ImageField(upload_to='sourcing_requests/', blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20)
    address = models.TextField()  
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Quotation(models.Model):
    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='quotation')
    quotation_price = models.DecimalField(max_digits=10, decimal_places=2)  # Quoted price for the request
    sent_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the quotation was sent

    def __str__(self):
        return f"Quotation for {self.sourcing_request.name} - {self.sourcing_request.user.username}"

class Payment(models.Model):
    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='payment')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Payment amount
    payment_status = models.BooleanField(default=False)  # Payment status (Paid/Not Paid)
    payment_date = models.DateTimeField(blank=True, null=True)  # Payment date

    def __str__(self):
        return f"Payment for {self.sourcing_request.name} - {self.sourcing_request.user.username}"

class Shipping(models.Model):
    sourcing_request = models.OneToOneField(SourcingRequest, on_delete=models.CASCADE, related_name='shipping')
    tracking_number = models.CharField(max_length=255, blank=True, null=True)  # Tracking number
    shipped_date = models.DateTimeField(blank=True, null=True)  # Date of shipment
    estimated_delivery_date = models.DateTimeField(blank=True, null=True)  # Estimated delivery date
    live_tracking_url = models.URLField(blank=True, null=True)  # URL for live tracking

    def __str__(self):
        return f"Shipping for {self.sourcing_request.name} - {self.sourcing_request.user.username}"
