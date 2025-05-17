from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShippingRateViewSet, address_suggestions

router = DefaultRouter()
router.register(r'shipping-rates', ShippingRateViewSet, basename='shipping-rates')

urlpatterns = [
    path('', include(router.urls)),
    path('address-suggestions/', address_suggestions, name='address_suggestions'),
]