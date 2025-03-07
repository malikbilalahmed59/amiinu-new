from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WarehouseViewSet, InboundShipmentViewSet, UserProductsByWarehouseView, OutboundShipmentViewSet, \
    WarehouseProductsView, ProductVariationsView, InventoryViewSet

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'inbound-shipments', InboundShipmentViewSet, basename='inbound-shipment')
router.register(r'outbound_shipments', OutboundShipmentViewSet, basename='outbound_shipment')
router.register(r'inventory', InventoryViewSet, basename='inventory')




urlpatterns = [
    path('', include(router.urls)),
    path('user-products/<int:warehouse_id>/', UserProductsByWarehouseView.as_view(), name='user-products'),

    path('warehouses/<int:warehouse_id>/products/', WarehouseProductsView.as_view(), name='warehouse-products'),
    path('products/<int:product_id>/variations/', ProductVariationsView.as_view(), name='product-variations'),



]
