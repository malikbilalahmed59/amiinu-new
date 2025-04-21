from rest_framework.permissions import BasePermission

class IsShipmentOrWarehouseOrAdmin(BasePermission):

    def has_permission(self, request, view):
        # Superusers and staff always have permission
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
            return True

        # Otherwise, check the role as usual
        return request.user.is_authenticated and request.user.role in ['shipment', 'warehouse']




class IsWarehouse(BasePermission):
    """
    Custom permission to allow only superusers and warehouse users to access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == "warehouse"
        )
