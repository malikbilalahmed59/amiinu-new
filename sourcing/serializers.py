import re
from rest_framework import serializers
from .models import SourcingRequest


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
