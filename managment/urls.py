from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManagementShipmentViewSet

router = DefaultRouter()
router.register(r'shipments', ManagementShipmentViewSet, basename='management-shipments')

urlpatterns = [
    path('', include(router.urls)),
]
