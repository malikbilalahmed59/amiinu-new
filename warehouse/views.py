from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Warehouse
from .serializers import WarehouseSerializer
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
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import InboundShipment, OutboundShipment
from .serializers import InboundShipmentSerializer, OutboundShipmentSerializer

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import InboundShipment, OutboundShipment
from .serializers import InboundShipmentSerializer, OutboundShipmentSerializer


class InboundShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = InboundShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only shipments for the authenticated user
        return InboundShipment.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # The user will be set automatically in the serializer
        serializer.save()

    # Ensure the serializer always has access to the request
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class OutboundShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = OutboundShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only shipments for the authenticated user
        return OutboundShipment.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # The user will be set automatically in the serializer
        serializer.save()

    # Ensure the serializer always has access to the request
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context





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
