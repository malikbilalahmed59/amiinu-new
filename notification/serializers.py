from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    app_display_name = serializers.CharField(source='get_app_name_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'app_name', 'app_display_name', 'notification_type',
            'notification_type_display', 'title', 'message', 'is_read',
            'created_at', 'reference_number', 'reference_url'
        ]
        read_only_fields = ['id', 'created_at', 'app_display_name',
                            'notification_type_display']