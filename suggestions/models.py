# models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import csv
import io
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
    CONDITION_CHOICES = [
        ('flat_rate', 'Flat Rate'),
        ('per_kg', 'Per KG'),
        ('per_cubic_meter', 'Per Cubic Meter'),
        ('tiered', 'Tiered Pricing'),
    ]

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
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
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

    @classmethod
    def create_or_update_from_csv(cls, csv_file):
        """
        Create or update shipping routes from CSV file
        Expected CSV format:
        shipping_from,shipping_to,service_type,rate_name,condition,weight_limit,transit_time,price,profit_margin,min_weight
        """
        results = {
            'created': 0,
            'updated': 0,
            'errors': []
        }

        try:
            # Read CSV content
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Get or create countries
                    from_country, _ = Country.objects.get_or_create(
                        name=row['shipping_from'].strip()
                    )
                    to_country, _ = Country.objects.get_or_create(
                        name=row['shipping_to'].strip()
                    )

                    # Get or create shipping service (FIXED - only service_type)
                    service, _ = ShippingService.objects.get_or_create(
                        service_type=row['service_type'].strip()
                    )

                    # Check if route exists
                    route, created = cls.objects.get_or_create(
                        shipping_from=from_country,
                        shipping_to=to_country,
                        service=service,
                        defaults={
                            'rate_name': row.get('rate_name', '').strip(),
                            'condition': row['condition'].strip(),
                            'weight_limit': float(row['weight_limit']),
                            'transit_time': row['transit_time'].strip(),
                            'price': float(row['price']),
                            'profit_margin': float(row['profit_margin']),
                            'min_weight': float(row.get('min_weight', 0)),
                        }
                    )

                    if created:
                        results['created'] += 1
                    else:
                        # Update existing route
                        route.rate_name = row.get('rate_name', '').strip()
                        route.condition = row['condition'].strip()
                        route.weight_limit = float(row['weight_limit'])
                        route.transit_time = row['transit_time'].strip()
                        route.price = float(row['price'])
                        route.profit_margin = float(row['profit_margin'])
                        route.min_weight = float(row.get('min_weight', 0))
                        route.save()
                        results['updated'] += 1

                except Exception as e:
                    results['errors'].append(f"Row {row_num}: {str(e)}")

        except Exception as e:
            results['errors'].append(f"File processing error: {str(e)}")

        return results