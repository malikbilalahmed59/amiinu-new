from rest_framework import serializers
from .models import Country, ShippingService, ShippingRoute


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class ShippingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingService
        fields = ['id', 'service_type']


class ShippingRouteSerializer(serializers.ModelSerializer):
    shipping_from_name = serializers.CharField(source='shipping_from.name', read_only=True)
    shipping_to_name = serializers.CharField(source='shipping_to.name', read_only=True)
    service_type = serializers.CharField(source='service.service_type', read_only=True)

    class Meta:
        model = ShippingRoute
        fields = [
            'id', 'shipping_from', 'shipping_to', 'service',
            'shipping_from_name', 'shipping_to_name', 'service_type',
            'rate_name', 'weight_limit', 'min_weight', 'transit_time',
            'price', 'profit_margin', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'shipping_from_name', 'shipping_to_name', 'service_type']