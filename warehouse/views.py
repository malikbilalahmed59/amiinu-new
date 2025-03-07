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
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import OutboundShipment
from .serializers import OutboundShipmentSerializer
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

class InventoryViewSet(viewsets.ModelViewSet):
    """API for managing inventory (products) by user."""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter products based on the user and optionally by warehouse."""
        user = self.request.user
        queryset = Product.objects.filter(warehouse__inbound_shipments__user=user).distinct()

        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        return queryset

    def perform_create(self, serializer):
        """Ensure user is linked to the product via inbound shipments."""
        product = serializer.save()
        if not product.inbound_shipments.filter(user=self.request.user).exists():
            return Response({"error": "You are not authorized to add this product"}, status=403)

    def perform_update(self, serializer):
        """Allow updates only if the user has access."""
        product = self.get_object()
        if not product.inbound_shipments.filter(user=self.request.user).exists():
            return Response({"error": "You are not authorized to update this product"}, status=403)
        serializer.save()

    def perform_destroy(self, instance):
        """Allow deletion only if the user has access."""
        if not instance.inbound_shipments.filter(user=self.request.user).exists():
            return Response({"error": "You are not authorized to delete this product"}, status=403)
        instance.delete()





class OutboundShipmentViewSet(viewsets.ModelViewSet):
    queryset = OutboundShipment.objects.all()
    serializer_class = OutboundShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Assign logged-in user

    def get_queryset(self):
        # Allow users to only see shipments they created
        return OutboundShipment.objects.filter(user=self.request.user)

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









class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):  # ✅ Only GET allowed
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]


class WarehouseProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, warehouse_id):
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            products = Product.objects.filter(warehouse=warehouse)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=200)
        except Warehouse.DoesNotExist:
            return Response({"error": "Warehouse not found"}, status=404)

class ProductVariationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=200)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
