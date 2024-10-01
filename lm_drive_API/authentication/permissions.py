from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCustomerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        if request.method in ["POST", "GET"]:
            return True  # Allow access for these methods generally

        return False


class IsStaffOrReadOnly(BasePermission):
    """
    Custom permission to only allow staff members to edit an object.
    Non-staff users can read the object.
    """

    def has_permission(self, request, view):
        # Allow all read operations (GET, HEAD, OPTIONS) for everyone
        if request.method in SAFE_METHODS:
            return True
        # Allow write operations only for staff
        return request.user.is_staff



