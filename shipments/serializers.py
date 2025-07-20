from rest_framework import serializers

from suggestions.models import ShippingRoute
from .models import Shipment, Container, Product
from decimal import Decimal


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'hs_code','product_value','product_quantity']


class ContainerSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, required=True)

    class Meta:
        model = Container
        fields = [
            'id', 'container_type', 'package_type', 'length', 'width', 'height', 'weight', 'quantity', 'products'
        ]

    def validate(self, attrs):
        shipment = self.context.get('shipment')

        if shipment:
            if isinstance(shipment, dict):
                shipment_type = shipment.get('shipment_type')
                international_shipping_type = shipment.get('international_shipping_type')
            else:
                shipment_type = shipment.shipment_type
                international_shipping_type = shipment.international_shipping_type

            container_type = attrs.get('container_type')
            package_type = attrs.get('package_type')

            if shipment_type == 'international':
                if international_shipping_type == 'fcl_sea' and not container_type:
                    raise serializers.ValidationError(
                        "For FCL shipments, 'container_type' must be specified and 'package_type' must be empty."
                    )
                elif international_shipping_type in ['lcl_sea', 'economy_air', 'express_air'] and not package_type:
                    raise serializers.ValidationError(
                        "For LCL or air shipments, 'package_type' must be specified and 'container_type' must be empty."
                    )
        return attrs

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        container = Container.objects.create(**validated_data)

        for product_data in products_data:
            Product.objects.create(container=container, **product_data)

        return container


class ShipmentSerializer(serializers.ModelSerializer):
    containers = ContainerSerializer(many=True, required=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    shipment_number = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    estimated_delivery_date = serializers.ReadOnlyField()
    total_weight = serializers.FloatField(read_only=True)

    # New fields for profit tracking (mostly read-only)
    shipping_route_id = serializers.IntegerField(write_only=True, required=False)
    base_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    profit_margin_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    profit_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    origin_country_name = serializers.CharField(source='origin_country.name', read_only=True)
    destination_country_name = serializers.CharField(source='destination_country.name', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'user', 'shipment_number', 'shipment_type', 'international_shipping_type', 'incoterm',
            'special_instructions', 'insure_shipment', 'insurance_value', 'is_dangerous_goods',
            'is_one_percent_insured',
            'pickup_address', 'delivery_address', 'pickup_date', 'recipient_name', 'recipient_email',
            'recipient_phone', 'sender_tax_vat', 'sender_email', 'delivery_price', 'payment_status',
            'status', 'estimated_delivery_date', 'created_at', 'updated_at', 'total_weight', 'containers',
            'shipping_route_id', 'base_cost', 'profit_margin_percentage', 'profit_amount',
            'origin_country_name', 'destination_country_name'
        ]

    def validate(self, attrs):
        shipment_type = attrs.get('shipment_type')
        international_shipping_type = attrs.get('international_shipping_type')
        containers = attrs.get('containers', [])

        for container_data in containers:
            serializer = ContainerSerializer(data=container_data,
                                             context={'shipment': self.instance or self.initial_data})
            serializer.is_valid(raise_exception=True)

        return attrs

    def create(self, validated_data):
        containers_data = validated_data.pop('containers', [])
        is_one_percent_insured = validated_data.get('is_one_percent_insured')
        delivery_price = validated_data.get('delivery_price')
        shipping_route_id = validated_data.pop('shipping_route_id', None)

        # If shipping_route_id is provided, fetch the route and set profit data
        if shipping_route_id:
            try:
                shipping_route = ShippingRoute.objects.get(id=shipping_route_id)
                validated_data['shipping_route'] = shipping_route
                validated_data['base_cost'] = shipping_route.price
                validated_data['profit_margin_percentage'] = shipping_route.profit_margin
                validated_data['origin_country'] = shipping_route.shipping_from
                validated_data['destination_country'] = shipping_route.shipping_to

                # Calculate profit amount if delivery_price is set
                if delivery_price:
                    validated_data['profit_amount'] = Decimal(delivery_price) - shipping_route.price
            except ShippingRoute.DoesNotExist:
                pass

        shipment = Shipment.objects.create(**validated_data)

        total_weight = 0.0
        for container_data in containers_data:
            products_data = container_data.pop('products', [])
            container = Container.objects.create(shipment=shipment, **container_data)
            total_weight += container.weight * container.quantity

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        shipment.total_weight = total_weight

        if is_one_percent_insured and delivery_price:
            shipment.insure_shipment = True
            shipment.insurance_value = round(Decimal(delivery_price) * Decimal('0.01'), 2)

        shipment.save()
        return shipment

    def update(self, instance, validated_data):
        containers_data = validated_data.pop('containers', [])
        is_one_percent_insured = validated_data.get('is_one_percent_insured', instance.is_one_percent_insured)
        delivery_price = validated_data.get('delivery_price', instance.delivery_price)
        shipping_route_id = validated_data.pop('shipping_route_id', None)

        # Update shipping route if provided
        if shipping_route_id:
            try:
                shipping_route = ShippingRoute.objects.get(id=shipping_route_id)
                validated_data['shipping_route'] = shipping_route
                validated_data['base_cost'] = shipping_route.price
                validated_data['profit_margin_percentage'] = shipping_route.profit_margin
                validated_data['origin_country'] = shipping_route.shipping_from
                validated_data['destination_country'] = shipping_route.shipping_to

                # Recalculate profit
                if delivery_price:
                    validated_data['profit_amount'] = Decimal(delivery_price) - shipping_route.price
            except ShippingRoute.DoesNotExist:
                pass

        instance = super().update(instance, validated_data)

        instance.containers.all().delete()

        total_weight = 0.0
        for container_data in containers_data:
            products_data = container_data.pop('products', [])
            container = Container.objects.create(shipment=instance, **container_data)
            total_weight += container.weight * container.quantity

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        instance.total_weight = total_weight

        if is_one_percent_insured and delivery_price:
            instance.insure_shipment = True
            instance.insurance_value = round(Decimal(delivery_price) * Decimal('0.01'), 2)

        instance.save()
        return instance