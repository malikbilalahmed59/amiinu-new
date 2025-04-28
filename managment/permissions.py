from rest_framework.permissions import BasePermission

class IsShipmentOrWarehouseOrAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
                request.user.is_superuser or (request.user.role == "warehouse"or request.user.role == "shipment")
        )




class IsWarehouse(BasePermission):
    """
    Custom permission to allow only superusers and warehouse users to access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == "warehouse"
        )
