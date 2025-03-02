from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from shipments.models import Shipment
from .permissions import IsShipmentOrWarehouseOrAdmin
from .serializers import ManagementShipmentSerializer

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
