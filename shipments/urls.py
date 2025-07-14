# urls.py for shipment app

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShipmentViewSet
from .views import dashboard_analytics, profit_report

router = DefaultRouter()
router.register(r'shipments', ShipmentViewSet, basename='shipment')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/dashboard/', dashboard_analytics, name='dashboard-analytics'),
    path('analytics/profit-report/', profit_report, name='profit-report'),
]