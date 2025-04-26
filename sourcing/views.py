# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import SourcingRequest, Quotation, Shipping
from .serializers import SourcingRequestSerializer, QuotationSerializer, ShippingSerializer


class SourcingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SourcingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'supplier':
            return SourcingRequest.objects.all()
        return SourcingRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        status_counts = (
            queryset.values('status')
            .annotate(total=Count('status'))
        )
        summary = {choice[0]: 0 for choice in SourcingRequest.STATUS_CHOICES}
        for entry in status_counts:
            summary[entry['status']] = entry['total']

        return Response({
            'sourcing_requests': serializer.data,
            'status_summary': summary,
        })


class QuotationBySourcingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'supplier':
            return Quotation.objects.all()
        return Quotation.objects.filter(sourcing_request__user=self.request.user)

    def get_object(self):
        """Override to get quotation by sourcing request ID"""
        sourcing_request_id = self.kwargs.get('pk')
        sourcing_request = get_object_or_404(SourcingRequest, pk=sourcing_request_id)

        # Check permissions
        if not (self.request.user.is_staff or
                self.request.user.is_superuser or
                self.request.user.role == 'supplier' or
                sourcing_request.user == self.request.user):
            self.permission_denied(self.request)

        # Get or create quotation for this sourcing request
        quotation, created = Quotation.objects.get_or_create(sourcing_request=sourcing_request)
        return quotation

    def create(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can create quotations."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get sourcing request from body
        sourcing_request_id = request.data.get('sourcing_request')
        sourcing_request = get_object_or_404(SourcingRequest, pk=sourcing_request_id)

        # Check if quotation already exists
        if hasattr(sourcing_request, 'quotation'):
            return Response(
                {"detail": "Quotation already exists for this sourcing request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can update quotations."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


class ShippingBySourcingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'supplier':
            return Shipping.objects.all()
        return Shipping.objects.filter(sourcing_request__user=self.request.user)

    def get_object(self):
        """Override to get shipping by sourcing request ID"""
        sourcing_request_id = self.kwargs.get('pk')
        sourcing_request = get_object_or_404(SourcingRequest, pk=sourcing_request_id)

        # Check permissions
        if not (self.request.user.is_staff or
                self.request.user.is_superuser or
                self.request.user.role == 'supplier' or
                sourcing_request.user == self.request.user):
            self.permission_denied(self.request)

        # Get or create shipping for this sourcing request
        shipping, created = Shipping.objects.get_or_create(sourcing_request=sourcing_request)
        return shipping

    def create(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can create shipping records."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get sourcing request from body
        sourcing_request_id = request.data.get('sourcing_request')
        sourcing_request = get_object_or_404(SourcingRequest, pk=sourcing_request_id)

        # Check if shipping already exists
        if hasattr(sourcing_request, 'shipping'):
            return Response(
                {"detail": "Shipping record already exists for this sourcing request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can update shipping records."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_shipped(self, request, pk=None):
        """Custom action to mark an item as shipped"""
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can mark items as shipped."},
                status=status.HTTP_403_FORBIDDEN
            )

        shipping = self.get_object()
        shipping.shipped_date = timezone.now()
        shipping.save()

        shipping.sourcing_request.status = 'shipped'
        shipping.sourcing_request.save()

        serializer = self.get_serializer(shipping)
        return Response(serializer.data)