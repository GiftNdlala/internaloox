from rest_framework.permissions import BasePermission, SAFE_METHODS

class CanCreateProducts(BasePermission):
    """Allow reading products to anyone, but restrict create/update/delete to privileged roles."""
    allowed_roles = {'owner', 'admin', 'warehouse_manager', 'warehouse'}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return getattr(user, 'role', None) in self.allowed_roles
        except Exception:
            return False