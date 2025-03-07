from rest_framework import serializers
from .models import Warehouse
from rest_framework import serializers
from .models import Variation, Product, InboundShipment

from rest_framework import serializers
from .models import InboundShipment, Product, Variation, VariationOption


class VariationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariationOption
        fields = '__all__'  # ✅ Includes 'name' & 'quantity'


class VariationSerializer(serializers.ModelSerializer):
    options = VariationOptionSerializer(many=True)  # ✅ NESTED OPTIONS

    class Meta:
        model = Variation
        fields = ['id', 'product', 'type', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])  # ✅ Extract options
        variation = Variation.objects.create(**validated_data)

        for option_data in options_data:
            VariationOption.objects.create(variation=variation, **option_data)  # ✅ Create options

        return variation


class ProductSerializer(serializers.ModelSerializer):
    variations = VariationSerializer(many=True, required=False)  # ✅ NESTED VARIATIONS

    class Meta:
        model = Product
        exclude = ['warehouse', 'inbound_shipments']  # ✅ Warehouse assigned in InboundShipmentSerializer

    def create(self, validated_data):
        variations_data = validated_data.pop('variations', [])  # ✅ Extract variations
        product = Product.objects.create(**validated_data)  # ✅ Create Product First

        for variation_data in variations_data:
            VariationSerializer().create({**variation_data, 'product': product})  # ✅ Assign product

        return product


class InboundShipmentSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)  # ✅ NESTED PRODUCTS

    class Meta:
        model = InboundShipment
        fields = ['id', 'warehouse', 'tracking_number', 'shipment_method', 'status', 'received_at', 'products']
        read_only_fields = ['id', 'status', 'received_at']

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])  # ✅ Extract products
        warehouse = validated_data.get('warehouse')  # ✅ Get warehouse

        inbound_shipments = InboundShipment.objects.create(**validated_data)  # ✅ Create shipment

        for product_data in products_data:
            product_data['inbound_shipments'] = inbound_shipments  # ✅ Assign shipment
            product_data['warehouse'] = warehouse  # ✅ Assign warehouse
            ProductSerializer().create(product_data)  # ✅ Delegate to ProductSerializer

        return inbound_shipments


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
