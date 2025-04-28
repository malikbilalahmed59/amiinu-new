from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by app_name
        app_name = self.request.query_params.get('app', None)
        if app_name:
            queryset = queryset.filter(app_name=app_name)

        # Filter by notification type
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        # Search by title or message
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )

        return queryset

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        queryset = self.get_queryset()
        queryset.update(is_read=True)
        return Response({'status': 'all notifications marked as read'})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get notification summary with counts by app and type"""
        queryset = self.get_queryset()

        summary = {
            'total': queryset.count(),
            'unread': queryset.filter(is_read=False).count(),
            'by_app': {},
            'by_type': {}
        }

        # Count by app
        for app_choice in Notification.APP_CHOICES:
            app_name = app_choice[0]
            app_queryset = queryset.filter(app_name=app_name)
            summary['by_app'][app_name] = {
                'total': app_queryset.count(),
                'unread': app_queryset.filter(is_read=False).count(),
                'display_name': app_choice[1]
            }

        # Count by type
        for type_choice in Notification.NOTIFICATION_TYPES:
            type_name = type_choice[0]
            type_queryset = queryset.filter(notification_type=type_name)
            summary['by_type'][type_name] = {
                'total': type_queryset.count(),
                'unread': type_queryset.filter(is_read=False).count(),
                'display_name': type_choice[1]
            }

        return Response(summary)