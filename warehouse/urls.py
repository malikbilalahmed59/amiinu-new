from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, InboundShipmentViewSet, UserProductsByWarehouseView

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'inbound-shipments', InboundShipmentViewSet, basename='inbound-shipment')


urlpatterns = [
    path('', include(router.urls)),
    path('user-products/<int:warehouse_id>/', UserProductsByWarehouseView.as_view(), name='user-products'),

]
