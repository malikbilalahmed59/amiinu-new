from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from shipments.models import Shipment
from .permissions import IsShipmentOrWarehouseOrAdmin, IsWarehouse
from .serializers import ManagementShipmentSerializer

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Case, When, Value, IntegerField

from warehouse.models import (
    InboundShipment,
    OutboundShipment
)
from .serializers import (
    InboundShipmentSerializer,
    OutboundShipmentSerializer
)
from .permissions import IsWarehouse


class AdminInboundShipmentViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing all inbound shipments.
    Only accessible to superusers and warehouse role users.

    Features:
    - Search by shipment number using ?search=<number>
    - Filter by warehouse ID using ?warehouse=<id>
    - Pending shipments are displayed first in FIFO order
    """
    serializer_class = InboundShipmentSerializer
    permission_classes = [IsWarehouse]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['warehouse']
    search_fields = ['shipment_number']

    def get_queryset(self):
        # Order by status (pending first) then by created_at (FIFO)
        queryset = InboundShipment.objects.all()

        # Annotate queryset to prioritize pending status
        queryset = queryset.annotate(
            status_priority=Case(
                When(status='pending', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', 'created_at')

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class AdminOutboundShipmentViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing all outbound shipments.
    Only accessible to superusers and warehouse role users.

    Features:
    - Search by shipment number using ?search=<number>
    - Filter by warehouse ID using ?warehouse=<id>
    - Pending shipments are displayed first in FIFO order
    """
    serializer_class = OutboundShipmentSerializer
    permission_classes = [IsWarehouse]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['warehouse']
    search_fields = ['shipment_number']

    def get_queryset(self):
        # Order by status (pending first) then by created_at (FIFO)
        queryset = OutboundShipment.objects.all()

        # Annotate queryset to prioritize pending status
        queryset = queryset.annotate(
            status_priority=Case(
                When(status='pending', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', 'created_at')

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class ManagementShipmentViewSet(ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ManagementShipmentSerializer
    permission_classes = [IsShipmentOrWarehouseOrAdmin]

    # Add this temporarily to your management app view to debug
    def get_queryset(self):
        queryset = self.queryset
        print(queryset.query)  # This will print the actual SQL query

        print(f"Total shipments in database: {queryset.count()}")
        print(f"Current user: {self.request.user}")
        print(f"User role: {self.request.user.role}")
        print(f"Is superuser: {self.request.user.is_superuser}")

        # List all shipments with their users
        for shipment in queryset:
            print(f"Shipment {shipment.shipment_number} belongs to user: {shipment.user}")

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Allow partial updates (PATCH)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Optionally, you can add some business logic here
        # For example, sending notifications when status changes
        if 'status' in request.data:
            self.handle_status_change(instance, request.data['status'])

        return Response(serializer.data)

    def handle_status_change(self, shipment, new_status):
        """
        Handle any business logic when status changes
        """
        # Example: Send email notifications, create logs, etc.
        old_status = shipment.status

        if old_status != new_status:
            # Log the status change
            # Send notifications
            # Update tracking information
            pass


