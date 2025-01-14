from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('normal', 'Normal User'),
        ('warehouse', 'Warehouse Management'),
        ('shipment', 'Shipment Management'),
        ('supplier', 'Supplier Management'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='normal'
    )
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.username} ({self.role})"

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
