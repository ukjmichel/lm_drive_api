from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """
    Allows access to the owner of the customer profile or staff (admins).
    """

    def has_permission(self, request, view):
        # Allow read access for all users
        if request.method in SAFE_METHODS:
            return True
        # Allow write access for the owner or staff
        return request.user.is_staff or (
            hasattr(request.user, "customer")
            and request.user.customer.pk == view.get_object().pk
        )


class IsAdminUser(BasePermission):
    """
    Allows access to staff (admin) users only, regardless of JWT token.
    """

    def has_permission(self, request, view):
        return request.user.is_staff
