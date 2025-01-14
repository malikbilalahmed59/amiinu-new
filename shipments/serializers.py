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
        fields = ['id', 'container_type', 'package_type', 'length', 'width', 'height', 'weight', 'quantity', 'products']


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

    def create(self, validated_data):
        containers_data = validated_data.pop('containers')
        shipment = Shipment.objects.create(**validated_data)

        for container_data in containers_data:
            products_data = container_data.pop('products')
            container = Container.objects.create(shipment=shipment, **container_data)

            for product_data in products_data:
                Product.objects.create(container=container, **product_data)

        return shipment

    def update(self, instance, validated_data):
        containers_data = validated_data.pop('containers', [])
        instance = super().update(instance, validated_data)

        # Handle Containers
        existing_containers = {container.id: container for container in instance.containers.all()}
        for container_data in containers_data:
            products_data = container_data.pop('products', [])
            container_id = container_data.get('id')

            if container_id and container_id in existing_containers:
                container = existing_containers[container_id]
                for attr, value in container_data.items():
                    setattr(container, attr, value)
                container.save()

                # Handle Products
                existing_products = {product.id: product for product in container.products.all()}
                for product_data in products_data:
                    product_id = product_data.get('id')

                    if product_id and product_id in existing_products:
                        product = existing_products[product_id]
                        for attr, value in product_data.items():
                            setattr(product, attr, value)
                        product.save()
                    else:
                        Product.objects.create(container=container, **product_data)
            else:
                new_container = Container.objects.create(shipment=instance, **container_data)
                for product_data in products_data:
                    Product.objects.create(container=new_container, **product_data)

        return instance
