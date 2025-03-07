from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .serializers import InventoryViewSet
from .views import WarehouseViewSet, InboundShipmentViewSet, UserProductsByWarehouseView, OutboundShipmentViewSet

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'inbound-shipments', InboundShipmentViewSet, basename='inbound-shipment')
router.register(r'outbound_shipments', OutboundShipmentViewSet, basename='outbound_shipment')
router.register(r'inventory', InventoryViewSet, basename='inventory')




urlpatterns = [
    path('', include(router.urls)),
    path('user-products/<int:warehouse_id>/', UserProductsByWarehouseView.as_view(), name='user-products'),

]
