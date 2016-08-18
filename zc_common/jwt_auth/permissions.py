from rest_framework.permissions import BasePermission
from .utils import USER_ROLE, STAFF_ROLE, SERVICE_ROLE, ANONYMOUS_ROLE


class IsUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return request.user and request.user.is_authenticated() and USER_ROLE in user.roles


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
        return request.user and request.user.is_authenticated() and ANONYMOUS_ROLE in user.roles


class IsService(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return request.user and request.user.is_authenticated() and SERVICE_ROLE in user.roles


class IsStaffOrService(IsStaff, IsService):
    def has_permission(self, request, view):
        return IsStaff.has_permission(self, request, view) or IsService.has_permission(self, request, view)
