from rest_framework import serializers
from .models import Warehouse
from rest_framework import serializers
from .models import Variation, Product, InboundShipment

class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variation
        fields = '__all__'
class ProductSerializer(serializers.ModelSerializer):
    variations = VariationSerializer(many=True, required=False)  # ✅ Nested Variations

    class Meta:
        model = Product
        exclude = ['warehouse', 'inbound_shipments']  # ✅ Exclude because we assign in InboundShipmentSerializer

    def create(self, validated_data):
        variations_data = validated_data.pop('variations', [])  # ✅ Extract variations
        product = Product.objects.create(**validated_data)  # ✅ Create Product First

        for variation_data in variations_data:
            Variation.objects.create(product=product, **variation_data)  # ✅ Assign product

        return product


class InboundShipmentSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)  # ✅ Use ProductSerializer to handle nested variations

    class Meta:
        model = InboundShipment
        fields = ['id', 'warehouse', 'tracking_number', 'shipment_method', 'status', 'received_at', 'products']
        read_only_fields = ['id', 'status', 'received_at']

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])  # ✅ Extract products
        warehouse = validated_data.get('warehouse')  # ✅ Get warehouse

        # ✅ Create the inbound shipment
        inbound_shipment = InboundShipment.objects.create(**validated_data)

        for product_data in products_data:
            product_data['inbound_shipments'] = inbound_shipment  # ✅ Assign InboundShipment
            product_data['warehouse'] = warehouse  # ✅ Assign Warehouse
            ProductSerializer().create(product_data)  # ✅ Let ProductSerializer handle variations

        return inbound_shipment


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
