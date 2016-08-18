from unittest import TestCase

from zc_common.jwt_auth.authentication import User
from zc_common.jwt_auth.permissions import IsUser, IsStaff, IsService, IsOwner, IsAnonymous, IsStaffOrService
from zc_common.jwt_auth.utils import USER_ROLE, STAFF_ROLE, SERVICE_ROLE, ANONYMOUS_ROLE


class PermissionTestMixin(object):
    def setUp(self):
        self.request = type('Request', (object,), {})

    def has_permission(self, user, result):
        self.request.user = user
        self.assertEqual(self.permission_class.has_permission(self.request, None), result)


class IsUserTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(IsUserTestCase, self).setUp()
        self.permission_class = IsUser()

    def test_user_role__pass(self):
        user = User(roles=[USER_ROLE])
        self.has_permission(user, True)

    def test_missing_user_role__fail(self):
        user = User(roles=[STAFF_ROLE, SERVICE_ROLE, ANONYMOUS_ROLE])
        self.has_permission(user, False)


class IsStaffTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(IsStaffTestCase, self).setUp()
        self.permission_class = IsStaff()

    def test_missing_user_role__fail(self):
        user = User(roles=[USER_ROLE])
        self.has_permission(user, False)

    def test_missing_staff_role__fail(self):
        user = User(roles=[STAFF_ROLE])
        self.has_permission(user, False)

    def test_user_and_staff_roles__pass(self):
        user = User(roles=[USER_ROLE, STAFF_ROLE])
        self.has_permission(user, True)

    def test_missing_user_and_staff_roles__fail(self):
        user = User(roles=[SERVICE_ROLE])
        self.has_permission(user, False)


class IsOwnerTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(IsOwnerTestCase, self).setUp()
        self.permission_class = IsOwner()

    def has_object_permission(self, user, obj, perm_result, obj_perm_result):
        self.has_permission(user, perm_result)
        self.assertEqual(self.permission_class.has_object_permission(self.request, None, obj), obj_perm_result)

    def test_missing_user_role__fail(self):
        user = User(roles=[SERVICE_ROLE, STAFF_ROLE, ANONYMOUS_ROLE], id='1')
        resource = type('Resource', (object, ), {'user': '1'})
        self.has_object_permission(user, resource, False, True)

    def test_not_owner__fail(self):
        user = User(roles=[USER_ROLE], id='1')
        resource = type('Resource', (object, ), {'user': '2'})
        self.has_object_permission(user, resource, True, False)

    def test_is_owner_and_has_user_role__pass(self):
        user = User(roles=[USER_ROLE], id='1')
        resource = type('Resource', (object,), {'user': '1'})
        self.has_object_permission(user, resource, True, True)


class IsServiceTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(IsServiceTestCase, self).setUp()
        self.permission_class = IsService()

    def test_missing_service_role__fail(self):
        user = User(roles=[USER_ROLE, STAFF_ROLE, ANONYMOUS_ROLE])
        self.has_permission(user, False)

    def test_service_role__pass(self):
        user = User(roles=[SERVICE_ROLE])
        self.has_permission(user, True)


class IsAnonymousTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(IsAnonymousTestCase, self).setUp()
        self.permission_class = IsAnonymous()

    def test_missing_anonymous_role__fail(self):
        user = User(roles=[USER_ROLE, STAFF_ROLE])
        self.has_permission(user, False)

    def test_anonymous_role__pass(self):
        user = User(roles=[ANONYMOUS_ROLE])
        self.has_permission(user, True)


class IsStaffOrServiceTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(IsStaffOrServiceTestCase, self).setUp()
        self.permission_class = IsStaffOrService()

    def test_missing_user_role__fail(self):
        user = User(roles=[STAFF_ROLE])
        self.has_permission(user, False)

    def test_missing_staff_role__fail(self):
        user = User(roles=[USER_ROLE])
        self.has_permission(user, False)

    def test_missing_service_role__fail(self):
        user = User(roles=[ANONYMOUS_ROLE])
        self.has_permission(user, False)

    def test_user_and_staff_roles__pass(self):
        user = User(roles=[USER_ROLE, STAFF_ROLE])
        self.has_permission(user, True)

    def test_service_role__pass(self):
        user = User(roles=[SERVICE_ROLE])
        self.has_permission(user, True)

