from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from shipments.models import Shipment
from .permissions import IsShipmentOrWarehouseOrAdmin, IsWarehouse
from .serializers import ManagementShipmentSerializer
from rest_framework import viewsets, permissions
from warehouse.models import OutboundShipment
from .serializers import AdminOutboundShipmentSerializer
from rest_framework import viewsets, permissions
from warehouse.models import InboundShipment
from .serializers import AdminInboundShipmentSerializer

class AdminInboundShipmentViewSet(viewsets.ModelViewSet):
    """
    Viewset for admins to manage inbound shipments.
    """
    queryset = InboundShipment.objects.all().select_related('warehouse').prefetch_related('products')
    serializer_class = AdminInboundShipmentSerializer
    permission_classes = [IsWarehouse]

    def get_queryset(self):
        """
        Allow filtering shipments by warehouse if needed.
        """
        queryset = self.queryset
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        return queryset

class AdminOutboundShipmentViewSet(viewsets.ModelViewSet):
    """
    Viewset for admins to manage outbound shipments.
    """
    queryset = OutboundShipment.objects.all().select_related('warehouse', 'user').prefetch_related('items')
    serializer_class = AdminOutboundShipmentSerializer
    permission_classes = [IsWarehouse]

    def get_queryset(self):
        """
        Allow filtering shipments by warehouse if needed.
        """
        queryset = self.queryset
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        return queryset

class ManagementShipmentViewSet(ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ManagementShipmentSerializer
    permission_classes = [IsShipmentOrWarehouseOrAdmin]  # Only management/admin users can access

    def get_queryset(self):
        return self.queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # Partial updates allowed

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
