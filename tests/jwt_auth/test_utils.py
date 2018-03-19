from unittest import TestCase

from zc_common.jwt_auth.authentication import User
from zc_common.jwt_auth.utils import jwt_payload_handler


class UtilsTest(TestCase):

    def setUp(self):
        self.user = User(id='123456')

    def test_jwt_payload_handler__have_required_keys(self):
        payload = jwt_payload_handler(self.user)

        self.assertIn('id', payload)
        self.assertIn('roles', payload)
