import re
from rest_framework import serializers
from .models import SourcingRequest, Quotation, Shipping


class SourcingRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = SourcingRequest
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'reference_number']

    def validate_whatsapp_number(self, value):
        """
        Custom validation for WhatsApp number format.
        """
        # Regex pattern for WhatsApp number (starts with +, followed by 7-15 digits)
        whatsapp_regex = r'^\+\d{7,15}$'
        if not re.match(whatsapp_regex, value):
            raise serializers.ValidationError({
                "message": "Invalid WhatsApp number. Format: '+<country_code><number>', e.g., +1234567890."
            })
        return value


class QuotationSerializer(serializers.ModelSerializer):
    sourcing_request_reference = serializers.CharField(source='sourcing_request.reference_number', read_only=True)
    user_email = serializers.EmailField(source='sourcing_request.user.email', read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'sourcing_request', 'sourcing_request_reference', 'user_email',
            'air_shipment_cost', 'sea_shipment_cost', 'truck_shipment_cost',
            'unit_price', 'note', 'status', 'rejection_reason',
            'sent_at', 'payment_amount', 'payment_status', 'payment_date'
        ]
        read_only_fields = ['sent_at']

    def validate(self, data):
        """
        Custom validation to ensure proper data when rejecting a quotation.
        """
        if 'status' in data and data['status'] == 'rejected':
            if not data.get('rejection_reason'):
                raise serializers.ValidationError(
                    {"rejection_reason": "Rejection reason is required when rejecting a quotation."}
                )
        return data

    def validate_air_shipment_cost(self, value):
        """
        Ensure shipment cost is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Air shipment cost must be greater than 0.")
        return value

    def validate_sea_shipment_cost(self, value):
        """
        Ensure shipment cost is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Sea shipment cost must be greater than 0.")
        return value

    def validate_truck_shipment_cost(self, value):
        """
        Ensure shipment cost is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Truck shipment cost must be greater than 0.")
        return value

    def validate_unit_price(self, value):
        """
        Ensure unit price is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Unit price must be greater than 0.")
        return value

    def validate_payment_amount(self, value):
        """
        Ensure payment amount is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than 0.")
        return value


class ShippingSerializer(serializers.ModelSerializer):
    sourcing_request_reference = serializers.CharField(source='sourcing_request.reference_number', read_only=True)

    class Meta:
        model = Shipping
        fields = [
            'id', 'sourcing_request', 'sourcing_request_reference',
            'tracking_number', 'shipped_date', 'estimated_delivery_date'
        ]

    def validate_tracking_number(self, value):
        """
        Basic validation for tracking number format.
        """
        if value and len(value) < 5:
            raise serializers.ValidationError("Tracking number seems too short.")
        return value