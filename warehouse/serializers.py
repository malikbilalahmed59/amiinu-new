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

from rest_framework import serializers
from .models import OutboundShipment, OutboundShipmentItem, Product, VariationOption, Warehouse

class OutboundShipmentItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)  # ✅ Include SKU
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
    warehouse_country = serializers.CharField(source='warehouse.country', read_only=True)  # ✅ Warehouse Name

    class Meta:
        model = OutboundShipment
        fields = ['id', 'warehouse', 'warehouse_country', 'user', 'customer_name',
                  'customer_address', 'tracking_number', 'shipment_method', 'status', 'estimated_delivery', 'items']
        read_only_fields = ['id', 'user', 'status']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        outbound_shipment = OutboundShipment.objects.create(**validated_data)

        for item_data in items_data:
            OutboundShipmentItem.objects.create(outbound_shipment=outbound_shipment, **item_data)

            # Reduce stock after shipment is created
            variation_option = item_data.get('variation_option')
            if variation_option:
                variation_option.quantity -= item_data.get('quantity')
                variation_option.save()

        return outbound_shipment

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

class InventoryViewSet(viewsets.ModelViewSet):
    """API for managing inventory (products) by user."""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter products based on the user and optionally by warehouse."""
        user = self.request.user
        queryset = Product.objects.filter(warehouse__inbound_shipments__user=user).distinct()

        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        return queryset

    def perform_create(self, serializer):
        """Ensure user is linked to the product via inbound shipments."""
        product = serializer.save()
        if not product.inbound_shipments.filter(user=self.request.user).exists():
            return Response({"error": "You are not authorized to add this product"}, status=403)

    def perform_update(self, serializer):
        """Allow updates only if the user has access."""
        product = self.get_object()
        if not product.inbound_shipments.filter(user=self.request.user).exists():
            return Response({"error": "You are not authorized to update this product"}, status=403)
        serializer.save()

    def perform_destroy(self, instance):
        """Allow deletion only if the user has access."""
        if not instance.inbound_shipments.filter(user=self.request.user).exists():
            return Response({"error": "You are not authorized to delete this product"}, status=403)
        instance.delete()
