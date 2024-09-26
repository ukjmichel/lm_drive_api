# permissions.py
from rest_framework import permissions


class IsCustomerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow customers to read and others to create/update/delete.
    """

    def has_permission(self, request, view):
        # Allow read-only access to everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow other methods only for authenticated users (not customers)
        return request.user.is_authenticated and not request.user.is_customer
