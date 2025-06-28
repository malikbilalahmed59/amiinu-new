from rest_framework import serializers
from .models import Country, ShippingService, ShippingRoute


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class ShippingServiceSerializer(serializers.ModelSerializer):
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)

    class Meta:
        model = ShippingService
        fields = ['id', 'service_type', 'service_type_display']


class ShippingRouteSerializer(serializers.ModelSerializer):
    shipping_from_detail = CountrySerializer(source='shipping_from', read_only=True)
    shipping_to_detail = CountrySerializer(source='shipping_to', read_only=True)
    service_detail = ShippingServiceSerializer(source='service', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)

    # For create/update operations
    shipping_from_name = serializers.CharField(write_only=True, required=False)
    shipping_to_name = serializers.CharField(write_only=True, required=False)
    service_type_value = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ShippingRoute
        fields = [
            'id', 'shipping_from', 'shipping_to', 'service',
            'shipping_from_detail', 'shipping_to_detail', 'service_detail',
            'shipping_from_name', 'shipping_to_name', 'service_type_value',
            'rate_name', 'condition', 'condition_display',
            'weight_limit', 'min_weight', 'transit_time', 'price',
            'profit_margin', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # Handle country and service creation/retrieval
        shipping_from_name = validated_data.pop('shipping_from_name', None)
        shipping_to_name = validated_data.pop('shipping_to_name', None)
        service_type_value = validated_data.pop('service_type_value', None)

        if shipping_from_name:
            shipping_from, _ = Country.objects.get_or_create(name=shipping_from_name)
            validated_data['shipping_from'] = shipping_from

        if shipping_to_name:
            shipping_to, _ = Country.objects.get_or_create(name=shipping_to_name)
            validated_data['shipping_to'] = shipping_to

        if service_type_value:
            service, _ = ShippingService.objects.get_or_create(service_type=service_type_value)
            validated_data['service'] = service

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle country and service updates
        shipping_from_name = validated_data.pop('shipping_from_name', None)
        shipping_to_name = validated_data.pop('shipping_to_name', None)
        service_type_value = validated_data.pop('service_type_value', None)

        if shipping_from_name:
            shipping_from, _ = Country.objects.get_or_create(name=shipping_from_name)
            validated_data['shipping_from'] = shipping_from

        if shipping_to_name:
            shipping_to, _ = Country.objects.get_or_create(name=shipping_to_name)
            validated_data['shipping_to'] = shipping_to

        if service_type_value:
            service, _ = ShippingService.objects.get_or_create(service_type=service_type_value)
            validated_data['service'] = service

        return super().update(instance, validated_data)
