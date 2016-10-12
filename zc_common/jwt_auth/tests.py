import re
from importlib import import_module
from unittest import TestCase

from mock import Mock

from django.contrib.admindocs.views import extract_views_from_urlpatterns, simplify_regex
from django.core.urlresolvers import resolve
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
    """
    This class attempt to make a distinction on using permission classes and their actual implementation.
    The goal is to be able to test permissions in similar way that DRF uses permission classes. Here is an example use:

    class UserPermissionTest(PermissionTestMixin, TestCase):
        permission_class_instance = UserPermission()
        PERMISSION_MAPPINGS = [
            {
                'url': '/url',
                'method': 'POST',
                'roles': ['user', 'staff'],
                'expected': False,
                'user_id': 10,    # This is optional.
                'instance': User.objects.first()  # This is optional.
            }
        ]

    """

    PERMISSION_MAPPINGS = []
    permission_class_instance = None

    def has_permission(self, url, method, roles, user_id, instance):
        resolver_match = resolve(url)

        user = type('TestUser', (Mock,), {'roles': roles, 'id': user_id})
        request = type('TestRequest', (Mock,), {'user': user, 'method': method})
        view = type('TestView', (Mock,), {'kwargs': resolver_match.kwargs})

        if not view.kwargs:
            return self.permission_class_instance.has_permission(request, view)
        return (self.permission_class_instance.has_permission(request, view) and
                self.permission_class_instance.has_object_permission(request, view, instance))

    def test_permissions(self):
        # I will modify this method so that each iteration generates it's own test.
        for permission_mapping in self.PERMISSION_MAPPINGS:
            url = permission_mapping.get('url')
            method = permission_mapping.get('method').upper()
            roles = permission_mapping.get('roles')
            expected = permission_mapping.get('expected')
            user_id = permission_mapping.get('user_id', 1)
            instance = permission_mapping.get('instance', None)

            has_perm = self.has_permission(url, method, roles, user_id, instance)
            message = ("Expecting {} for {} {} with roles={}. I got instead {}"
                       .format(expected, method, url, roles, has_perm))
            self.assertEqual(has_perm, expected, message)
