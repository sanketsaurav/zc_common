from rest_framework.permissions import BasePermission


class DefaultPermission(BasePermission):
    """
    Requires the request to include a jwt token.
    """

    def has_permission(self, request, view):
        return hasattr(request.user, 'roles')
