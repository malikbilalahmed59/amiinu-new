from rest_framework import serializers
from .models import Shipment, Container, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'quantity', 'unit_price', 'weight_per_unit', 'hs_code']


class ContainerSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = Container
        fields = [
            'id', 'container_type', 'package_type', 'length', 'width', 'height', 'weight', 'quantity', 'products'
        ]

    def validate(self, attrs):
        """
        Validates container_type and package_type based on shipment type and international shipping type.
        """
        shipment = self.context.get('shipment')  # Pass shipment instance via serializer context

        # Allow initial validation without a shipment instance
        if not shipment:
            return attrs

        shipment_type = shipment.shipment_type
        international_shipping_type = shipment.international_shipping_type

        container_type = attrs.get('container_type')
        package_type = attrs.get('package_type')

        if shipment_type == 'international':
            if international_shipping_type in ['fcl_sea']:
                if not container_type:
                    raise serializers.ValidationError(
                        "For FCL shipments, 'container_type' must be specified and 'package_type' must be empty."
                    )
                if package_type:
                    raise serializers.ValidationError(
                        "For FCL shipments, 'package_type' should not be specified."
                    )
            elif international_shipping_type in ['lcl_sea', 'economy_air', 'express_air']:
                if not package_type:
                    raise serializers.ValidationError(
                        "For LCL or air shipments, 'package_type' must be specified and 'container_type' must be empty."
                    )
                if container_type:
                    raise serializers.ValidationError(
                        "For LCL or air shipments, 'container_type' should not be specified."
                    )
        return attrs


class ShipmentSerializer(serializers.ModelSerializer):
    containers = ContainerSerializer(many=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Shipment
        fields = [
            'id', 'shipment_type', 'international_shipping_type', 'incoterm', 'special_instructions',
            'insure_shipment', 'insurance_value', 'pickup_address', 'delivery_address', 'pickup_date',
            'recipient_name', 'recipient_email', 'recipient_phone', 'receiver_name', 'receiver_email',
            'receiver_phone', 'receiver_vat_no', 'delivery_price', 'payment_status', 'containers', 'user'
        ]

    def validate(self, attrs):
        """
        Perform shipment-level validation, including containers.
        """
        shipment_type = attrs.get('shipment_type')
        international_shipping_type = attrs.get('international_shipping_type')
        containers = attrs.get('containers', [])

        # Validate containers against shipment type and international shipping type
        for container_data in containers:
            container_type = container_data.get('container_type')
            package_type = container_data.get('package_type')

            if shipment_type == 'international':
                if international_shipping_type in ['fcl_sea']:
                    if not container_type:
                        raise serializers.ValidationError(
                            "For FCL shipments, 'container_type' must be specified and 'package_type' must be empty."
                        )
                    if package_type:
                        raise serializers.ValidationError(
                            "For FCL shipments, 'package_type' should not be specified."
                        )
                elif international_shipping_type in ['lcl_sea', 'economy_air', 'express_air']:
                    if not package_type:
                        raise serializers.ValidationError(
                            "For LCL or air shipments, 'package_type' must be specified and 'container_type' must be empty."
                        )
                    if container_type:
                        raise serializers.ValidationError(
                            "For LCL or air shipments, 'container_type' should not be specified."
                        )
        return attrs

    def create(self, validated_data):
        containers_data = validated_data.pop('containers')
        shipment = Shipment.objects.create(**validated_data)

        for container_data in containers_data:
            products_data = container_data.pop('products')
            serializer = ContainerSerializer(data=container_data, context={'shipment': shipment})
            serializer.is_valid(raise_exception=True)
            container = serializer.save(shipment=shipment)

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        return shipment

    def update(self, instance, validated_data):
        containers_data = validated_data.pop('containers', [])
        instance = super().update(instance, validated_data)

        # Handle containers and validation
        for container_data in containers_data:
            products_data = container_data.pop('products', [])
            serializer = ContainerSerializer(data=container_data, context={'shipment': instance})
            serializer.is_valid(raise_exception=True)
            container = serializer.save(shipment=instance)

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        return instance
