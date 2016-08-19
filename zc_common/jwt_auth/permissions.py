from rest_framework.permissions import BasePermission
from .utils import USER_ROLE, STAFF_ROLE, SERVICE_ROLE, ANONYMOUS_ROLE


class IsUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated() and USER_ROLE in user.roles


class IsStaff(IsUser):
    def has_permission(self, request, view):
        user = request.user
        return super(IsStaff, self).has_permission(request, view) and STAFF_ROLE in user.roles


class IsOwner(IsUser):
    def has_object_permission(self, request, view, obj):
        if not obj.user:
            return False
        return str(request.user.id) == str(obj.user)


class IsAnonymous(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated() and ANONYMOUS_ROLE in user.roles


class IsService(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated() and SERVICE_ROLE in user.roles


class IsStaffOrService(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated() and (
            (USER_ROLE in user.roles and STAFF_ROLE in user.roles) or SERVICE_ROLE in user.roles)
