from rest_framework import serializers
from .models import Shipment, Container, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'hs_code']


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

    class Meta:
        model = Shipment
        fields = [
            'id','user', 'shipment_number', 'shipment_type', 'international_shipping_type', 'incoterm',
            'special_instructions', 'insure_shipment', 'insurance_value', 'pickup_address', 'delivery_address',
            'pickup_date', 'recipient_name', 'recipient_email', 'recipient_phone', 'sender_tax_vat',
            'sender_email', 'delivery_price', 'payment_status', 'status', 'estimated_delivery_date'
            , 'created_at', 'updated_at', 'containers'
        ]

    def validate(self, attrs):
        shipment_type = attrs.get('shipment_type')
        international_shipping_type = attrs.get('international_shipping_type')
        containers = attrs.get('containers', [])

        for container_data in containers:
            serializer = ContainerSerializer(data=container_data, context={'shipment': self.instance})
            serializer.is_valid(raise_exception=True)

        return attrs

    def create(self, validated_data):
        containers_data = validated_data.pop('containers', [])
        shipment = Shipment.objects.create(**validated_data)

        for container_data in containers_data:
            products_data = container_data.pop('products', [])
            container = Container.objects.create(shipment=shipment, **container_data)

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        return shipment

    def update(self, instance, validated_data):
        containers_data = validated_data.pop('containers', [])
        instance = super().update(instance, validated_data)

        # Update containers
        instance.containers.all().delete()
        for container_data in containers_data:
            products_data = container_data.pop('products', [])
            container = Container.objects.create(shipment=instance, **container_data)

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        return instance
