from rest_framework.permissions import BasePermission, SAFE_METHODS

class CanCreateProducts(BasePermission):
    """Allow reading products to anyone, but restrict create/update/delete to privileged roles."""
    allowed_roles = {'owner', 'admin', 'warehouse'}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in self.allowed_roles