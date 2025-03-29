from rest_framework import serializers
from .models import Warehouse, Variation, Product, InboundShipment, VariationOption
from .models import OutboundShipment, OutboundShipmentItem


class VariationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariationOption
        fields = '__all__'


class VariationSerializer(serializers.ModelSerializer):
    options = VariationOptionSerializer(many=True)

    class Meta:
        model = Variation
        fields = ['id', 'product', 'type', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        variation = Variation.objects.create(**validated_data)

        for option_data in options_data:
            VariationOption.objects.create(variation=variation, **option_data)

        return variation


class ProductSerializer(serializers.ModelSerializer):
    variations = VariationSerializer(many=True, required=False)

    class Meta:
        model = Product
        exclude = ['warehouse', 'inbound_shipments']

    def create(self, validated_data):
        variations_data = validated_data.pop('variations', [])
        product = Product.objects.create(**validated_data)

        for variation_data in variations_data:
            VariationSerializer().create({**variation_data, 'product': product})

        return product


class InboundShipmentSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = InboundShipment
        fields = [
            'id', 'warehouse', 'user', 'tracking_number', 'shipment_method',
            'status', 'pending_at', 'in_transit_at', 'received_at',
            'completed_at', 'cancelled_at', 'created_at', 'updated_at',
            'products'
        ]
        read_only_fields = [
            'id', 'shipment_number', 'status', 'pending_at', 'in_transit_at', 'received_at',
            'completed_at', 'cancelled_at', 'created_at', 'updated_at'
        ]
        # Remove user from required fields - we'll set it in create
        extra_kwargs = {
            'user': {'required': False}
        }

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        warehouse = validated_data.get('warehouse')

        # Get the user from the request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        inbound_shipment = InboundShipment.objects.create(**validated_data)

        for product_data in products_data:
            product_data['inbound_shipments'] = inbound_shipment
            product_data['warehouse'] = warehouse
            ProductSerializer().create(product_data)

        return inbound_shipment

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if products_data is not None:
            # DELETE existing nested products and everything below
            instance.products.all().delete()

            warehouse = instance.warehouse
            for product_data in products_data:
                product_data['inbound_shipments'] = instance
                product_data['warehouse'] = warehouse
                ProductSerializer().create(product_data)

        return instance




class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'


class OutboundShipmentItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    variation_name = serializers.CharField(source='variation_option.name', read_only=True)

    class Meta:
        model = OutboundShipmentItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'variation_option',
                  'variation_name', 'quantity']

    def validate(self, data):
        """
        Validate if the requested quantity is available in stock.
        """
        product = data.get('product')
        variation_option = data.get('variation_option')
        quantity = data.get('quantity')

        if variation_option and variation_option.quantity < quantity:
            raise serializers.ValidationError(f"Not enough stock for {variation_option.name}")

        return data


class OutboundShipmentSerializer(serializers.ModelSerializer):
    items = OutboundShipmentItemSerializer(many=True)
    warehouse_country = serializers.CharField(source='warehouse.country', read_only=True)

    class Meta:
        model = OutboundShipment
        fields = [
            'id', 'warehouse', 'warehouse_country', 'user', 'customer_name',
            'customer_address', 'tracking_number', 'shipment_method',
            'status', 'pending_at', 'shipped_at', 'delivered_at',
            'cancelled_at', 'estimated_delivery', 'created_at', 'updated_at',
            'items'
        ]
        read_only_fields = [
            'id', 'shipment_number', 'status', 'pending_at', 'shipped_at',
            'delivered_at', 'cancelled_at', 'created_at', 'updated_at'
        ]
        # Remove user from required fields - we'll set it in create
        extra_kwargs = {
            'user': {'required': False}
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # Get the user from the request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        outbound_shipment = OutboundShipment.objects.create(**validated_data)

        for item_data in items_data:
            OutboundShipmentItem.objects.create(outbound_shipment=outbound_shipment, **item_data)

            # Reduce stock after shipment is created
            variation_option = item_data.get('variation_option')
            if variation_option:
                variation_option.quantity -= item_data.get('quantity')
                variation_option.save()

        return outbound_shipment