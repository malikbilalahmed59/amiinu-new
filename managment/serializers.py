from rest_framework import serializers
from shipments.models import Shipment, Container, Product
from shipments.serializers import ContainerSerializer  # Reuse existing container serializer


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
