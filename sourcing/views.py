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

    def destroy(self, request, *args, **kwargs):
        """
        Override to properly handle sourcing request deletion with related records.
        """
        instance = self.get_object()

        # The delete method in the model will handle deleting related records
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class QuotationBySourcingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Quotation.objects.all()

        # Filter by sourcing request ID if provided in query params
        sourcing_request_id = self.request.query_params.get('sourcing_request_id')
        if sourcing_request_id:
            queryset = queryset.filter(sourcing_request_id=sourcing_request_id)

        # Apply user-based filtering
        if not (self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'supplier'):
            queryset = queryset.filter(sourcing_request__user=self.request.user)

        return queryset

    def get_object(self):
        """
        Get the quotation object directly by its ID or
        by sourcing request ID if sourcing_request_id is provided in query params
        """
        # Check if sourcing_request_id is in query params
        sourcing_request_id = self.request.query_params.get('sourcing_request_id')

        if sourcing_request_id:
            # Get by sourcing request ID
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
        else:
            # Standard get by ID
            pk = self.kwargs.get('pk')
            quotation = get_object_or_404(Quotation, pk=pk)

            # Check permissions
            if not (self.request.user.is_staff or
                    self.request.user.is_superuser or
                    self.request.user.role == 'supplier' or
                    quotation.sourcing_request.user == self.request.user):
                self.permission_denied(self.request)

            return quotation

    def destroy(self, request, *args, **kwargs):
        """
        Override to properly handle quotation deletion.
        Supports deletion by either quotation ID or sourcing request ID.
        Only staff, admins, or suppliers can delete quotations.
        """
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can delete quotations."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if delete is by sourcing request ID
        sourcing_request_id = request.query_params.get('sourcing_request_id')

        if sourcing_request_id:
            # Delete by sourcing request ID
            sourcing_request = get_object_or_404(SourcingRequest, pk=sourcing_request_id)

            # Check permissions
            if not (request.user.is_staff or
                    request.user.is_superuser or
                    request.user.role == 'supplier' or
                    sourcing_request.user == request.user):
                return Response(
                    {"detail": "You do not have permission to delete this quotation."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Find and delete the quotation
            try:
                quotation = Quotation.objects.get(sourcing_request=sourcing_request)
                quotation.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Quotation.DoesNotExist:
                return Response(
                    {"detail": "Quotation for this sourcing request does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Standard deletion by quotation ID
            quotation = self.get_object()
            quotation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Custom action to reject a quotation"""
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can reject quotations."},
                status=status.HTTP_403_FORBIDDEN
            )

        quotation = self.get_object()

        # Validate rejection reason
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {"detail": "Rejection reason is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update quotation status and rejection reason
        quotation.status = 'rejected'
        quotation.rejection_reason = rejection_reason
        quotation.save()

        # Update sourcing request status to reflect rejection
        quotation.sourcing_request.status = 'cancelled'
        quotation.sourcing_request.save()

        serializer = self.get_serializer(quotation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        """Custom action to accept a quotation"""
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can accept quotations."},
                status=status.HTTP_403_FORBIDDEN
            )

        quotation = self.get_object()

        # Update quotation status
        quotation.status = 'accepted'
        quotation.save()

        # Update sourcing request status
        quotation.sourcing_request.status = 'quotation_sent'
        quotation.sourcing_request.save()

        serializer = self.get_serializer(quotation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_paid(self, request, pk=None):
        """Custom action to mark a quotation as paid"""
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can mark quotations as paid."},
                status=status.HTTP_403_FORBIDDEN
            )

        quotation = self.get_object()

        # Update payment information
        payment_amount = request.data.get('payment_amount')
        if not payment_amount:
            return Response(
                {"detail": "Payment amount is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment_amount = float(payment_amount)
            if payment_amount <= 0:
                raise ValueError("Payment amount must be positive")
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid payment amount."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update quotation with payment details
        quotation.payment_amount = payment_amount
        quotation.payment_status = True
        quotation.payment_date = timezone.now()
        quotation.save()

        # Update sourcing request status
        quotation.sourcing_request.status = 'paid'
        quotation.sourcing_request.save()

        serializer = self.get_serializer(quotation)
        return Response(serializer.data)


class ShippingBySourcingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Shipping.objects.all()

        # Filter by sourcing request ID if provided in query params
        sourcing_request_id = self.request.query_params.get('sourcing_request_id')
        if sourcing_request_id:
            queryset = queryset.filter(sourcing_request_id=sourcing_request_id)

        # Apply user-based filtering
        if not (self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'supplier'):
            queryset = queryset.filter(sourcing_request__user=self.request.user)

        return queryset

    def get_object(self):
        """
        Get the shipping object directly by its ID or
        by sourcing request ID if sourcing_request_id is provided in query params
        """
        # Check if sourcing_request_id is in query params
        sourcing_request_id = self.request.query_params.get('sourcing_request_id')

        if sourcing_request_id:
            # Get by sourcing request ID
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
        else:
            # Standard get by ID
            pk = self.kwargs.get('pk')
            shipping = get_object_or_404(Shipping, pk=pk)

            # Check permissions
            if not (self.request.user.is_staff or
                    self.request.user.is_superuser or
                    self.request.user.role == 'supplier' or
                    shipping.sourcing_request.user == self.request.user):
                self.permission_denied(self.request)

            return shipping

    def destroy(self, request, *args, **kwargs):
        """
        Override to properly handle shipping record deletion.
        Supports deletion by either shipping ID or sourcing request ID.
        Only staff, admins, or suppliers can delete shipping records.
        """
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can delete shipping records."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if delete is by sourcing request ID
        sourcing_request_id = request.query_params.get('sourcing_request_id')

        if sourcing_request_id:
            # Delete by sourcing request ID
            sourcing_request = get_object_or_404(SourcingRequest, pk=sourcing_request_id)

            # Check permissions
            if not (request.user.is_staff or
                    request.user.is_superuser or
                    request.user.role == 'supplier' or
                    sourcing_request.user == request.user):
                return Response(
                    {"detail": "You do not have permission to delete this shipping record."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Find and delete the shipping record
            try:
                shipping = Shipping.objects.get(sourcing_request=sourcing_request)
                shipping.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Shipping.DoesNotExist:
                return Response(
                    {"detail": "Shipping record for this sourcing request does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Standard deletion by shipping ID
            shipping = self.get_object()
            shipping.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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

        # Ensure tracking number is provided
        tracking_number = request.data.get('tracking_number')
        if not tracking_number:
            return Response(
                {"detail": "Tracking number is required to mark an item as shipped."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate tracking number length
        if len(tracking_number) < 5:
            return Response(
                {"detail": "Tracking number seems too short."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update shipping information
        shipping.tracking_number = tracking_number
        shipping.shipped_date = timezone.now()

        # Set estimated delivery date if provided
        estimated_delivery_date = request.data.get('estimated_delivery_date')
        if estimated_delivery_date:
            shipping.estimated_delivery_date = estimated_delivery_date

        shipping.save()

        # Update sourcing request status
        shipping.sourcing_request.status = 'shipped'
        shipping.sourcing_request.save()

        serializer = self.get_serializer(shipping)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_delivered(self, request, pk=None):
        """Custom action to mark an item as delivered"""
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'supplier'):
            return Response(
                {"detail": "Only administrators and suppliers can mark items as delivered."},
                status=status.HTTP_403_FORBIDDEN
            )

        shipping = self.get_object()

        # Ensure the item has been shipped first
        if not shipping.shipped_date:
            return Response(
                {"detail": "Item must be shipped before it can be marked as delivered."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update sourcing request status
        shipping.sourcing_request.status = 'delivered'
        shipping.sourcing_request.save()

        serializer = self.get_serializer(shipping)
        return Response(serializer.data)