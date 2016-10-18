import re
from importlib import import_module

from mock import Mock

from django.contrib.admindocs.views import extract_views_from_urlpatterns, simplify_regex
from django.conf import settings

from .authentication import User
from .utils import jwt_payload_handler, service_jwt_payload_handler, jwt_encode_handler


def get_service_endpoint_urls(urlconfig=None, default_value='1'):
    """
    This function finds all endpoint urls in a service.

    Args:
        urlconfig: A django url config module to use. Defaults to settings.ROOT_URLCONF
        default_value: A string value to replace all url parameters with

    Returns:
        A list of urls with path parameters (i.e. <pk>) replaced with default_value
    """
    if not urlconfig:
        urlconfig = getattr(settings, 'ROOT_URLCONF')

    try:
        urlconfig_mod = import_module(urlconfig)
    except Exception as ex:
        raise Exception(
            "Unable to import url config module. Url Config: {0}. Message: {1}".format(urlconfig, ex.message))

    extracted_views = extract_views_from_urlpatterns(urlconfig_mod.urlpatterns)
    views_regex_url_patterns = [item[1] for item in extracted_views]
    simplified_regex_url_patterns = [simplify_regex(pattern) for pattern in views_regex_url_patterns]

    # Strip out urls we don't need to test.
    result_urls = []
    pattern = re.compile(r'<\w+>')

    for url in simplified_regex_url_patterns:
        if url.find('<format>') != -1:
            continue

        if url == u'/':
            continue

        if url == u'/health':
            continue

        parameters = pattern.findall(url)
        for param in parameters:
            url = url.replace(param, default_value)

        result_urls.append(url)

    return result_urls


class AuthenticationMixin:
    def create_user(self, roles, user_id):
        return User(roles=roles, pk=user_id)

    def create_user_token(self, user):
        payload = jwt_payload_handler(user)
        token = "JWT {}".format(jwt_encode_handler(payload))
        return token

    def create_service_token(self, service_name):
        payload = service_jwt_payload_handler(service_name)
        token = "JWT {}".format(jwt_encode_handler(payload))
        return token

    def get_staff_token(self, user_id):
        staff_user = self.create_user(['user', 'staff'], user_id)
        return self.create_user_token(staff_user)

    def get_user_token(self, user_id):
        user = self.create_user(['user'], user_id)
        return self.create_user_token(user)

    def get_guest_token(self, user_id):
        user = self.create_user(['user'], user_id)
        return self.create_user_token(user)

    def get_anonymous_token(self):
        return "JWT {}".format(jwt_encode_handler({'roles': ['anonymous']}))

    def get_service_token(self, service_name):
        return self.create_service_token(service_name)

    def authorize_as(self, user_type, **kwargs):
        method = getattr(self, 'get_%s_token' % user_type)
        if user_type == 'service':
            token = method(kwargs.get('service_name', 'Test'))
        elif user_type == 'anonymous':
            token = method()
        else:
            token = method(kwargs.get('user_id', 1))
        self.client.credentials(HTTP_AUTHORIZATION=token)


class PermissionTestMixin(object):
    def setUp(self):
        self.user = type('User', (Mock,), {'roles': [], 'id': 1})
        self.request = type('Request', (Mock,), {'user': self.user})
        self.view = type('View', (Mock,), {})
        self.obj = None

        # Create an instance of the Permission class in child class
        self.permission_obj = None

    def assert_has_permission(self, expected):
        has_perm = self.permission_obj.has_permission(self.request, self.view)
        self.assertEqual(has_perm, expected)

    def assert_has_object_permission(self, expected):
        has_perm = self.permission_obj.has_object_permission(self.request, self.view, self.obj)
        self.assertEqual(has_perm, expected)

    def assert_permission(self, expected):
        has_perm = (self.permission_obj.has_permission(self.request, self.view) and
                    self.permission_obj.has_object_permission(self.request, self.view, self.obj))
        self.assertEqual(has_perm, expected)
