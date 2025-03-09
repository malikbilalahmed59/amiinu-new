from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManagementShipmentViewSet, AdminInboundShipmentViewSet, AdminOutboundShipmentViewSet

router = DefaultRouter()
router.register(r'shipments', ManagementShipmentViewSet, basename='management-shipments')
router.register(r'warehouse/inbound-shipments', AdminInboundShipmentViewSet, basename='admin-inbound-shipments')
router.register(r'warehouse/outbound-shipments', AdminOutboundShipmentViewSet, basename='admin-outbound-shipments')



urlpatterns = [
    path('', include(router.urls)),
]
