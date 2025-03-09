from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, InboundShipmentViewSet, OutboundShipmentViewSet, InventoryViewSet, VariationViewSet, VariationOptionViewSet

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'inbound-shipments', InboundShipmentViewSet, basename='inbound-shipment')
router.register(r'outbound-shipments', OutboundShipmentViewSet, basename='outbound-shipment')
router.register(r'inventory', InventoryViewSet, basename='user-inventory')

# Nested Inventory Routing
warehouse_inventory_router = DefaultRouter()
warehouse_inventory_router.register(r'inventory', InventoryViewSet, basename='warehouse-inventory')

# Nested Variations Routing
inventory_variations_router = DefaultRouter()
inventory_variations_router.register(r'variations', VariationViewSet, basename='inventory-variations')

# Nested Variation Options Routing
variations_options_router = DefaultRouter()
variations_options_router.register(r'options', VariationOptionViewSet, basename='variation-options')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:warehouse_id>/', include(warehouse_inventory_router.urls)),  # Warehouse -> Inventory
    path('<int:warehouse_id>/inventory/<int:inventory_id>/', include(inventory_variations_router.urls)),  # Inventory -> Variations
    path('<int:warehouse_id>/inventory/<int:inventory_id>/variations/<int:variation_id>/', include(variations_options_router.urls)),  # Variations -> Options
]
