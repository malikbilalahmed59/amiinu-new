from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Warehouse
from .serializers import WarehouseSerializer
from .permissions import IsWarehouseOrSuperUser
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import InboundShipment, Product
from .serializers import InboundShipmentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Product, Warehouse
from .serializers import ProductSerializer

class UserProductsByWarehouseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, warehouse_id):
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            if request.user:
                products = Product.objects.filter(warehouse=warehouse)
                serializer = ProductSerializer(products, many=True)
                return Response(serializer.data, status=200)
            return Response({"error": "Not authorized"}, status=403)
        except Warehouse.DoesNotExist:
            return Response({"error": "Warehouse not found"}, status=404)

class InboundShipmentViewSet(viewsets.ModelViewSet):
    queryset = InboundShipment.objects.all()
    serializer_class = InboundShipmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # No need to modify warehouse handling


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, IsWarehouseOrSuperUser]
