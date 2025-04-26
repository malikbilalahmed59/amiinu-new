# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SourcingRequestViewSet,
    QuotationBySourcingRequestViewSet,
    ShippingBySourcingRequestViewSet
)

router = DefaultRouter()
router.register(r'sourcing-requests', SourcingRequestViewSet, basename='sourcing-request')
router.register(r'quotations', QuotationBySourcingRequestViewSet, basename='quotation')
router.register(r'shipping', ShippingBySourcingRequestViewSet, basename='shipping')

urlpatterns = [
    path('', include(router.urls)),
]