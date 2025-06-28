from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class ShippingService(models.Model):
    SHIPPING_TYPES = [
        ('economy_air', 'Economy Air'),
        ('express_air', 'Express Air'),
        ('fcl_sea', 'FCL (Full Container Load) Sea'),
        ('lcl_sea', 'LCL (Less than Container Load) Sea'),
        ('connect_plus', 'Connect Plus'),
    ]

    service_type = models.CharField(max_length=20, choices=SHIPPING_TYPES)

    class Meta:
        unique_together = ['service_type']

    def __str__(self):
        return f"({self.get_service_type_display()})"


class ShippingRoute(models.Model):


    shipping_from = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='routes_from'
    )
    shipping_to = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='routes_to'
    )
    service = models.ForeignKey(
        ShippingService,
        on_delete=models.CASCADE,
        related_name='routes'
    )

    # Route details
    rate_name = models.CharField(max_length=100, blank=True)
    weight_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum weight in KG"
    )
    transit_time = models.CharField(max_length=50)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Profit margin as percentage"
    )

    # Additional fields
    min_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['shipping_from', 'shipping_to', 'service']
        ordering = ['shipping_from', 'shipping_to', 'service']

    def __str__(self):
        return f"{self.shipping_from} → {self.shipping_to} ({self.service})"

    def clean(self):
        if self.min_weight > self.weight_limit:
            raise ValidationError("Minimum weight cannot be greater than weight limit")

