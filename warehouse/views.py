from rest_framework import viewsets, permissions, status, exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Warehouse,
    InboundShipment,
    OutboundShipment,
    Product,
    Variation,
    VariationOption
)
from .serializers import (
    WarehouseSerializer,
    InboundShipmentSerializer,
    OutboundShipmentSerializer,
    ProductSerializer,
    VariationSerializer,
    VariationOptionSerializer
)


class InboundShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = InboundShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InboundShipment.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class OutboundShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = OutboundShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OutboundShipment.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        user = self.request.user

        if warehouse_id:
            return Product.objects.filter(
                warehouse_id=warehouse_id,
                inbound_shipments__user=user
            ).distinct()

        return Product.objects.filter(
            inbound_shipments__user=user
        ).distinct()

    def perform_create(self, serializer):
        warehouse_id = self.kwargs.get('warehouse_id')
        product = serializer.save(warehouse_id=warehouse_id)

        if not product.inbound_shipments.filter(user=self.request.user).exists():
            raise exceptions.PermissionDenied("You are not authorized to add this product")

    def perform_update(self, serializer):
        product = self.get_object()
        if product.inbound_shipments.user != self.request.user:
            raise exceptions.PermissionDenied("You are not authorized to update this product")

        serializer.save()

    def perform_destroy(self, instance):
        if not instance.inbound_shipments.filter(user=self.request.user).exists():
            raise exceptions.PermissionDenied("You are not authorized to delete this product")
        instance.delete()


class VariationViewSet(viewsets.ModelViewSet):
    serializer_class = VariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        user = self.request.user

        if not inventory_id or not warehouse_id:
            raise exceptions.NotFound("Product ID and Warehouse ID are required")

        return Variation.objects.filter(
            product_id=inventory_id,
            product__warehouse_id=warehouse_id,
            product__inbound_shipments__user=user
        ).distinct()

    def perform_create(self, serializer):
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')

        if not Product.objects.filter(id=inventory_id, warehouse_id=warehouse_id, inbound_shipments__user=self.request.user).exists():
            raise exceptions.PermissionDenied("You are not authorized to add variations to this product")

        serializer.save(product_id=inventory_id)


class VariationOptionViewSet(viewsets.ModelViewSet):
    serializer_class = VariationOptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        variation_id = self.kwargs.get('variation_id')
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        user = self.request.user

        if not variation_id or not inventory_id or not warehouse_id:
            raise exceptions.NotFound("Variation ID, Product ID, and Warehouse ID are required")

        return VariationOption.objects.filter(
            variation_id=variation_id,
            variation__product_id=inventory_id,
            variation__product__warehouse_id=warehouse_id,
            variation__product__inbound_shipments__user=user
        ).distinct()


class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]