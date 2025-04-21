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


    def get_queryset(self):
        return self.queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # Partial updates allowed

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
