# serializers.py
import re
from rest_framework import serializers
from .models import SourcingRequest, Quotation, Shipping


class SourcingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourcingRequest
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

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
    class Meta:
        model = Quotation
        fields = '__all__'
        read_only_fields = ['sent_at']

    def validate_quotation_price(self, value):
        """
        Ensure quotation price is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Quotation price must be greater than 0.")
        return value

    def validate_payment_amount(self, value):
        """
        Ensure payment amount is positive if provided.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than 0.")
        return value


class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'

    def validate_tracking_number(self, value):
        """
        Basic validation for tracking number format.
        """
        if value and len(value) < 5:
            raise serializers.ValidationError("Tracking number seems too short.")
        return value