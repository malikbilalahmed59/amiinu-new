from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SourcingRequestViewSet

router = DefaultRouter()
router.register(r'sourcing-requests', SourcingRequestViewSet, basename='sourcing-request')

urlpatterns = [
    path('', include(router.urls)),
]
