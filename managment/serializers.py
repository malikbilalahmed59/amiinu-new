from django.utils import timezone  # this is the correct one for Django

from rest_framework import serializers
from shipments.models import Shipment, Container, Product
from shipments.serializers import ContainerSerializer  # Reuse existing container serializer
from rest_framework import serializers
from warehouse.models import InboundShipment, OutboundShipment, OutboundShipmentItem
from warehouse.serializers import ProductSerializer, OutboundShipmentItemSerializer
from rest_framework import serializers



class InboundShipmentSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.address', read_only=True)

    class Meta:
        model = InboundShipment
        fields = ['user_email', 'warehouse_name',
            'id', 'warehouse', 'user', 'tracking_number', 'shipment_method',
            'status', 'pending_at', 'in_transit_at', 'received_at',
            'completed_at', 'cancelled_at', 'created_at', 'updated_at',
            'products', 'status',
        ]
        read_only_fields = [
            'id', 'shipment_number' ,'pending_at', 'in_transit_at', 'received_at',
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
        products_data = validated_data.pop('products', [])
        warehouse = validated_data.get('warehouse', instance.warehouse)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Delete existing products and recreate (simpler alternative to full sync logic)
        instance.products.all().delete()
        for product_data in products_data:
            product_data['inbound_shipments'] = instance
            product_data['warehouse'] = warehouse
            ProductSerializer().create(product_data)

        return instance


class OutboundShipmentSerializer(serializers.ModelSerializer):
    items = OutboundShipmentItemSerializer(many=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.address', read_only=True)

    class Meta:
        model = OutboundShipment
        fields = ['user_email', 'warehouse_name',
            'id', 'warehouse', 'user', 'customer_name',
            'customer_address', 'tracking_number', 'shipment_method',
            'status', 'pending_at', 'shipped_at', 'delivered_at',
            'cancelled_at', 'estimated_delivery', 'created_at', 'updated_at',
            'items', 'shipment_number'
        ]
        read_only_fields = [

            'id', 'pending_at', 'shipped_at',
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

        return outbound_shipment

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        old_status = instance.status
        new_status = validated_data.get('status', old_status)

        # Update status timestamps
        if old_status == 'pending' and new_status == 'shipped':
            validated_data['shipped_at'] = timezone.now()

            # Decrement inventory for all shipment items
            self._reduce_inventory_quantities(instance)

        # Update instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle nested items update only if items_data is provided (for PATCH support)
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OutboundShipmentItem.objects.create(outbound_shipment=instance, **item_data)

        return instance

    def _reduce_inventory_quantities(self, shipment):
        for item in shipment.items.all():
            # Get the variation option
            variation_option = item.variation_option
            if variation_option:
                # Reduce the quantity
                variation_option.quantity -= item.quantity
                variation_option.save()

































class ManagementShipmentSerializer(serializers.ModelSerializer):
    containers = ContainerSerializer(many=True, required=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'shipment_number', 'shipment_type', 'international_shipping_type', 'incoterm',
            'special_instructions', 'insure_shipment', 'insurance_value', 'is_dangerous_goods', 'is_one_percent_insured',
            'pickup_address', 'delivery_address', 'pickup_date', 'recipient_name', 'recipient_email',
            'recipient_phone', 'sender_tax_vat', 'sender_email', 'delivery_price', 'payment_status',
            'status', 'estimated_delivery_date', 'tracking_company', 'tracking_number',
            'created_at', 'updated_at', 'containers'
        ]

        read_only_fields = [
            'id', 'shipment_number', 'shipment_type', 'international_shipping_type',
            'special_instructions', 'insure_shipment', 'insurance_value', 'is_dangerous_goods', 'is_one_percent_insured',
            'pickup_address', 'delivery_address', 'pickup_date', 'recipient_name', 'recipient_email',
            'recipient_phone', 'sender_tax_vat', 'sender_email', 'delivery_price', 'payment_status',
            'created_at', 'updated_at', 'containers'
        ]



