from rest_framework import permissions

USER_ACTOR = 'user'
STAFF_ACTOR = 'staff'
SERVICE_ACTOR = 'service'
ANONYMOUS_ACTOR = 'anonymous'

USER_ROLES = [USER_ACTOR]
STAFF_ROLES = [USER_ACTOR, STAFF_ACTOR]
SERVICE_ROLES = [SERVICE_ACTOR]
ANONYMOUS_ROLES = [ANONYMOUS_ACTOR]


def is_staff(request):
    return USER_ACTOR in request.user.roles and STAFF_ACTOR in request.user.roles


def is_user(request):
    return USER_ACTOR in request.user.roles


def is_service(request):
    return SERVICE_ACTOR in request.user.roles


def is_anonymous(request):
    return ANONYMOUS_ACTOR in request.user.roles


class BasePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return self.has_read_permission(request, view)

        if request.method == 'DELETE':
            return self.has_delete_permission(request, view)

        if request.method in ['POST', 'PUT', 'PATCH']:
            return self.has_write_permission(request, view)

        return False

    def has_read_permission(self, request, view):
        return False

    def has_delete_permission(self, request, view):
        return False

    def has_write_permission(self, request, view):
        if request.method == 'POST':
            return self.has_create_permission(request, view)

        if request.method == 'PUT' or request.method == 'PATCH':
            return self.has_update_permission(request, view)

    def has_create_permission(self, request, view):
        return False

    def has_update_permission(self, request, view):
        return False


class EventViewPermission(BasePermission):
    def has_create_permission(self, request, view):
        return is_service(request)


class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_staff(request)
