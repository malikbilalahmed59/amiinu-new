from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShippingRateViewSet, address_suggestions, ControlRateViewSet

router = DefaultRouter()
router.register(r'shipping-rates', ShippingRateViewSet, basename='shipping-rates')
router.register(r'control-rates', ControlRateViewSet, basename='control-rates')


urlpatterns = [
    path('', include(router.urls)),
    path('address-suggestions/', address_suggestions, name='address_suggestions'),
]