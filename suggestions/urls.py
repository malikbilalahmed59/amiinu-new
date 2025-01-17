from django.urls import path
from .views import address_suggestions, reset_usage_view

urlpatterns = [
    path('address-suggestions/', address_suggestions, name='address_suggestions'),
    path('reset-usage/', reset_usage_view, name='reset_usage'),

]