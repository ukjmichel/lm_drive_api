from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCustomerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        if request.method in ["POST", "GET"]:
            return True  # Allow access for these methods generally

        return False


class IsAdminUser(BasePermission):
    """
    Allows access to staff (admin) users only, regardless of JWT token.
    """

    def has_permission(self, request, view):
        return request.user.is_staff


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff
