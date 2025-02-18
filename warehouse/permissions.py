from rest_framework import permissions

class IsWarehouseOrSuperUser(permissions.BasePermission):
    """
    Custom permission to allow only superusers and warehouse users to create, update, and delete.
    All authenticated users can read (GET).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return request.user and (request.user.is_superuser or request.user.role == 'warehouse')
