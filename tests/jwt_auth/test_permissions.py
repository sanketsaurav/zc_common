from unittest import TestCase
from mock import Mock

from zc_common.jwt_auth.authentication import User
from zc_common.jwt_auth.permissions import (is_staff, is_service, is_user, is_anonymous,
                                            USER_ROLES, STAFF_ROLES, ANONYMOUS_ROLES, SERVICE_ROLES)


class TestMixin(object):
    def setUp(self):
        self.user = User(roles=[])
        self.request = type('Request', (Mock,), {'user': self.user})
        self.callable = None

    def assert_has_permission(self, expected):
        has_perm = self.callable(self.request)
        self.assertEqual(has_perm, expected)


class TestIsUser(TestMixin, TestCase):
    def setUp(self):
        super(TestIsUser, self).setUp()
        self.callable = is_user

    def test_user_role__pass(self):
        self.user.roles = USER_ROLES
        self.assert_has_permission(True)

        self.user.roles = STAFF_ROLES
        self.assert_has_permission(True)

    def test_user_role__fail(self):
        self.user.roles = SERVICE_ROLES
        self.assert_has_permission(False)

        self.user.roles = ANONYMOUS_ROLES
        self.assert_has_permission(False)


class TestIsStaff(TestMixin, TestCase):
    def setUp(self):
        super(TestIsStaff, self).setUp()
        self.callable = is_staff

    def test_staff_roles__pass(self):
        self.user.roles = STAFF_ROLES
        self.assert_has_permission(True)

    def test_staff_roles__fail(self):
        self.user.roles = SERVICE_ROLES
        self.assert_has_permission(False)

        self.user.roles = ANONYMOUS_ROLES
        self.assert_has_permission(False)

        self.user.roles = USER_ROLES
        self.assert_has_permission(False)


class TestIsService(TestMixin, TestCase):
    def setUp(self):
        super(TestIsService, self).setUp()
        self.callable = is_service

    def test_service_role__pass(self):
        self.user.roles = SERVICE_ROLES
        self.assert_has_permission(True)

    def test_service_role__fail(self):
        self.user.roles = STAFF_ROLES
        self.assert_has_permission(False)

        self.user.roles = ANONYMOUS_ROLES
        self.assert_has_permission(False)

        self.user.roles = USER_ROLES
        self.assert_has_permission(False)


class TestIsAnonymous(TestMixin, TestCase):
    def setUp(self):
        super(TestIsAnonymous, self).setUp()
        self.callable = is_anonymous

    def test_anonymous_role__pass(self):
        self.user.roles = ANONYMOUS_ROLES
        self.assert_has_permission(True)

    def test_anonymous_role__fail(self):
        self.user.roles = STAFF_ROLES
        self.assert_has_permission(False)

        self.user.roles = SERVICE_ROLES
        self.assert_has_permission(False)

        self.user.roles = USER_ROLES
        self.assert_has_permission(False)
