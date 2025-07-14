from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import  address_suggestions, ControlRateViewSet, CountryViewSet, ShippingServiceViewSet, \
    calculate_shipping_rates

router = DefaultRouter()
# router.register(r'shipping-rates', ShippingRateViewSet, basename='shipping-rates')
router.register(r'control-countries', CountryViewSet, basename='countries')
router.register(r'control-services', ShippingServiceViewSet, basename='services')
router.register(r'control-rates', ControlRateViewSet, basename='control-rates')


urlpatterns = [
    path('', include(router.urls)),
    path('address-suggestions/', address_suggestions, name='address_suggestions'),
        path('shipping-rates/', calculate_shipping_rates, name='calculate_shipping_rates'),
]