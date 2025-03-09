from rest_framework import serializers
from shipments.models import Shipment, Container, Product
from shipments.serializers import ContainerSerializer  # Reuse existing container serializer
from rest_framework import serializers
from warehouse.models import OutboundShipment, OutboundShipmentItem, VariationOption
from warehouse.serializers import OutboundShipmentItemSerializer
from rest_framework import serializers
from warehouse.models import InboundShipment, OutboundShipment, OutboundShipmentItem, VariationOption
from warehouse.serializers import ProductSerializer, OutboundShipmentItemSerializer  # ✅ Reusing existing serializers


class AdminInboundShipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Admins to GET and PATCH Inbound Shipments.
    """
    products = ProductSerializer(many=True)

    class Meta:
        model = InboundShipment
        fields = ['id', 'warehouse', 'tracking_number', 'shipment_method', 'status', 'received_at', 'products']
        read_only_fields = ['id', 'received_at']

    def update(self, instance, validated_data):
        """
        Allows admin to update the inbound shipment status and other fields if needed.
        """
        instance.status = validated_data.get('status', instance.status)
        instance.tracking_number = validated_data.get('tracking_number', instance.tracking_number)
        instance.shipment_method = validated_data.get('shipment_method', instance.shipment_method)
        instance.shipment_received_at = validated_data.get('received_at', instance.received_at)
        instance.save()
        return instance


class AdminOutboundShipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Admins to GET and PATCH Outbound Shipments, including updating item quantities.
    """
    items = OutboundShipmentItemSerializer(many=True)

    class Meta:
        model = OutboundShipment
        fields = ['id', 'warehouse', 'user', 'customer_name', 'customer_address',
                  'tracking_number', 'shipment_method', 'status', 'estimated_delivery', 'items']
        read_only_fields = ['id', 'user']

    def update(self, instance, validated_data):
        """
        Allows admin to update the outbound shipment details and adjust item quantities.
        """
        items_data = validated_data.pop('items', [])

        # ✅ Update Shipment Details
        instance.status = validated_data.get('status', instance.status)
        instance.tracking_number = validated_data.get('tracking_number', instance.tracking_number)
        instance.shipment_method = validated_data.get('shipment_method', instance.shipment_method)
        instance.estimated_delivery = validated_data.get('estimated_delivery', instance.estimated_delivery)
        instance.save()

        # ✅ Update Each Item in the Shipment
        for item_data in items_data:
            item_id = item_data.get('id')
            if not item_id:
                continue  # Skip if no ID is provided

            try:
                item_instance = OutboundShipmentItem.objects.get(id=item_id, outbound_shipment=instance)
            except OutboundShipmentItem.DoesNotExist:
                continue  # Skip if item does not belong to this shipment

            new_quantity = item_data.get('quantity', item_instance.quantity)
            variation_option = item_instance.variation_option

            # ✅ Adjust stock
            if variation_option:
                stock_diff = new_quantity - item_instance.quantity
                variation_option.quantity -= stock_diff
                variation_option.save()

            # ✅ Update Item
            item_instance.quantity = new_quantity
            item_instance.save()

        return instance


class ManagementShipmentSerializer(serializers.ModelSerializer):
    containers = ContainerSerializer(many=True, required=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'shipment_number', 'shipment_type', 'international_shipping_type', 'incoterm',
            'special_instructions', 'insure_shipment', 'insurance_value', 'pickup_address', 'delivery_address',
            'pickup_date', 'recipient_name', 'recipient_email', 'recipient_phone', 'sender_tax_vat',
            'sender_email', 'delivery_price', 'payment_status', 'status', 'estimated_delivery_date',
            'tracking_company', 'tracking_number', 'created_at', 'updated_at', 'containers'
        ]
        read_only_fields = [  # Prevent management from modifying user-specific fields
            'id', 'shipment_number', 'shipment_type', 'international_shipping_type', 'incoterm',
            'special_instructions', 'insure_shipment', 'insurance_value', 'pickup_address', 'delivery_address',
            'pickup_date', 'recipient_name', 'recipient_email', 'recipient_phone', 'sender_tax_vat',
            'sender_email', 'delivery_price', 'payment_status', 'created_at', 'updated_at', 'containers'
        ]

    def update(self, instance, validated_data):
        """Management can only update status, estimated delivery date, tracking details."""
        instance.status = validated_data.get('status', instance.status)
        instance.estimated_delivery_date = validated_data.get('estimated_delivery_date',
                                                              instance.estimated_delivery_date)
        instance.tracking_company = validated_data.get('tracking_company', instance.tracking_company)
        instance.tracking_number = validated_data.get('tracking_number', instance.tracking_number)
        instance.save()
        return instance
