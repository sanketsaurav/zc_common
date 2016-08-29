from unittest import TestCase
from mock import Mock

from zc_common.jwt_auth.authentication import User
from zc_common.jwt_auth import permissions
from zc_common.jwt_auth.tests import PermissionTestMixin


class TestMixin(object):
    def setUp(self):
        self.user = User(roles=[])
        self.request = type('Request', (Mock,), {'user': self.user})
        self.callable = None

    def assert_has_permission(self, expected):
        has_perm = self.callable(self.request)
        self.assertEqual(has_perm, expected)


class IsUserTestCase(TestMixin, TestCase):
    def setUp(self):
        super(IsUserTestCase, self).setUp()
        self.callable = permissions.is_user

    def test_user_role__pass(self):
        self.user.roles = permissions.USER_ROLES
        self.assert_has_permission(True)

        self.user.roles = permissions.STAFF_ROLES
        self.assert_has_permission(True)

    def test_user_role__fail(self):
        self.user.roles = permissions.SERVICE_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.ANONYMOUS_ROLES
        self.assert_has_permission(False)


class IsStaffTestCase(TestMixin, TestCase):
    def setUp(self):
        super(IsStaffTestCase, self).setUp()
        self.callable = permissions.is_staff

    def test_staff_roles__pass(self):
        self.user.roles = permissions.STAFF_ROLES
        self.assert_has_permission(True)

    def test_staff_roles__fail(self):
        self.user.roles = permissions.SERVICE_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.ANONYMOUS_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.USER_ROLES
        self.assert_has_permission(False)


class IsServiceTestCase(TestMixin, TestCase):
    def setUp(self):
        super(IsServiceTestCase, self).setUp()
        self.callable = permissions.is_service

    def test_service_role__pass(self):
        self.user.roles = permissions.SERVICE_ROLES
        self.assert_has_permission(True)

    def test_service_role__fail(self):
        self.user.roles = permissions.STAFF_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.ANONYMOUS_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.USER_ROLES
        self.assert_has_permission(False)


class IsAnonymousTestCase(TestMixin, TestCase):
    def setUp(self):
        super(IsAnonymousTestCase, self).setUp()
        self.callable = permissions.is_anonymous

    def test_anonymous_role__pass(self):
        self.user.roles = permissions.ANONYMOUS_ROLES
        self.assert_has_permission(True)

    def test_anonymous_role__fail(self):
        self.user.roles = permissions.STAFF_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.SERVICE_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.USER_ROLES
        self.assert_has_permission(False)


class EventViewPermissionTestCase(PermissionTestMixin, TestCase):
    def setUp(self):
        super(EventViewPermissionTestCase, self).setUp()
        self.permission_obj = permissions.EventViewPermission()

    def test_create_permission__pass(self):
        self.request.method = 'POST'
        self.user.roles = permissions.SERVICE_ROLES
        self.assert_has_permission(True)

    def test_create_permission__fail(self):
        self.request.method = 'POST'

        self.user.roles = permissions.STAFF_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.USER_ROLES
        self.assert_has_permission(False)

        self.user.roles = permissions.ANONYMOUS_ROLES
        self.assert_has_permission(False)
