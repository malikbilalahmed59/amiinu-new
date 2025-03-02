from rest_framework.permissions import BasePermission

class IsShipmentOrWarehouseOrAdmin(BasePermission):
    """
    Custom permission to allow only users with roles 'shipment', 'warehouse', or superadmins to access management endpoints.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role in ['shipment', 'warehouse']
        )
