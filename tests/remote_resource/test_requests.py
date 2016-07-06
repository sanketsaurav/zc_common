import mock
import json
from django.test import TestCase
from zc_common.remote_resource.request import (
    RemoteResourceWrapper, RemoteResourceListWrapper, get_route_from_fk, make_service_request, get_remote_resource,
    RouteNotFoundException, GET, POST)


class WrappersTestCase(TestCase):

    def test_remote_resource_wrapper(self):
        data = {
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {
                    "title": "Omakase"
                }
            }
        }

        resource = RemoteResourceWrapper(data['data'])

        self.assertEqual(resource.title, "Omakase")
        self.assertEqual(resource.type, "articles")
        self.assertEqual(resource.id, "1")

    def test_remote_resource_list_wrapper(self):
        data = {
            "data": [
                {
                    "type": "articles",
                    "id": "1",
                    "attributes": {
                        "title": "Omakase"
                    }
                }
            ]
        }

        resource = RemoteResourceListWrapper(data['data'])

        self.assertEqual(resource[0].title, "Omakase")
        self.assertEqual(resource[0].type, "articles")
        self.assertEqual(resource[0].id, "1")

    def test_remote_resource_wrapper_one_relationship(self):
        data = {
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {
                    "title": "Omakase"
                },
                "relationships": {
                    "author": {
                        "links": {
                            "self": "/articles/1/relationships/author",
                            "related": "/articles/1/author"
                        },
                        "data": {"type": "People", "id": "9"}
                    }
                }
            }
        }

        resource = RemoteResourceWrapper(data['data'])

        self.assertEqual(resource.author.type, "People")
        self.assertEqual(resource.author.id, "9")

    def test_remote_resource_wrapper_multiple_relationship(self):
        data = {
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {
                    "title": "Omakase"
                },
                "relationships": {
                    "authors": {
                        "links": {
                            "self": "/articles/1/relationships/authors",
                            "related": "/articles/1/authors"
                        },
                        "data": [
                            {"type": "People", "id": "9"},
                        ]
                    }
                }
            }
        }

        resource = RemoteResourceWrapper(data['data'])

        self.assertEqual(resource.authors[0].type, "People")
        self.assertEqual(resource.authors[0].id, "9")

    def test_remote_resource_list_wrapper_one_relationship(self):
        data = {
            "data": [
                {
                    "type": "articles",
                    "id": "1",
                    "attributes": {
                        "title": "Omakase"
                    },
                    "relationships": {
                        "author": {
                            "links": {
                                "self": "/articles/1/relationships/author",
                                "related": "/articles/1/author"
                            },
                            "data": {"type": "People", "id": "9"}
                        }
                    }
                }
            ]
        }

        resources = RemoteResourceListWrapper(data['data'])

        self.assertEqual(resources[0].author.type, 'People')
        self.assertEqual(resources[0].author.id, '9')

    def test_remote_resource_list_wrapper_multiple_relationship(self):
        data = {
            "data": [
                {
                    "type": "articles",
                    "id": "1",
                    "attributes": {
                        "title": "Omakase"
                    },
                    "relationships": {
                        "authors": {
                            "links": {
                                "self": "/articles/1/relationships/authors",
                                "related": "/articles/1/authors"
                            },
                            "data": [
                                {"type": "People", "id": "9"},
                            ]
                        }
                    }
                }
            ]
        }

        resources = RemoteResourceListWrapper(data['data'])

        self.assertEqual(resources[0].authors[0].type, 'People')
        self.assertEqual(resources[0].authors[0].id, '9')


@mock.patch('zc_common.remote_resource.request.requests')
@mock.patch('zc_common.remote_resource.request.zc_settings')
class GetRouteFromForeignKeyTestCase(TestCase):
    def setUp(self):
        self.gateway_root_path = 'http://mp-gateway.zerocater.com'
        self.mappings = {
            '/users{/id}': {
                'domain': 'https://mp-users.zerocater.com',
                'resource_type': 'User'
            }
        }
        self.get_response = mock.Mock()
        self.get_response.json.return_value = self.mappings

    def bind_mock_objects(self, mock_zc_settings, mock_requests):
        mock_zc_settings.GATEWAY_ROOT_PATH = self.gateway_root_path
        mock_requests.get.return_value = self.get_response

    def test_wrong_resource_type(self, mock_zc_settings, mock_requests):
        self.bind_mock_objects(mock_zc_settings, mock_requests)
        resource_type = 'Movie'
        self.assertRaises(RouteNotFoundException, get_route_from_fk, resource_type)

    def test_correct_resource_type_with_one_pk(self, mock_zc_settings, mock_requests):
        self.bind_mock_objects(mock_zc_settings, mock_requests)
        expected_url = 'https://mp-users.zerocater.com/users/1'

        result_url = get_route_from_fk('User', 1)

        mock_requests.get.assert_called_once_with(self.gateway_root_path)
        self.assertEqual(expected_url, result_url)

    def test_correct_resource_type_with_multiple_pk(self, mock_zc_settings, mock_requests):
        self.bind_mock_objects(mock_zc_settings, mock_requests)
        expected_url = 'https://mp-users.zerocater.com/users?filter[id__in]=1,2,3'

        result_url = get_route_from_fk('User', [1, 2, 3])

        mock_requests.get.assert_called_once_with(self.gateway_root_path)
        self.assertEqual(expected_url, result_url)


@mock.patch('zc_common.remote_resource.request.requests')
@mock.patch('zc_common.remote_resource.request.jwt_encode_handler', autospec=True)
@mock.patch('zc_common.remote_resource.request.service_jwt_payload_handler', autospec=True)
class MakeServiceRequestTestCase(TestCase):
    def setUp(self):
        self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' \
                'eyJzZXJ2aWNlTmFtZSI6Im1wLXVzZXJzIiwicm9sZXMiOlsic2VydmljZSJdfQ.' \
                'AorXWnXhKzht7Psn_P_JVcEIRZptdk4synXUf6fr7_0'

        self.service_name = 'test'
        self.payload = {
            'serviceName': self.service_name,
            'roles': ['Service']
        }
        self.endpoint = 'http://mp-users.herokuapp.com/users/1'
        self.headers = {'Authorization': 'JWT {}'.format(self.token), 'Content-Type': 'application/vnd.api+json'}

    def bind_mocked_objects(self, mock_jwt_payload_handler, mock_jwt_encode_handler):
        mock_jwt_payload_handler.return_value = self.payload
        mock_jwt_encode_handler.return_value = self.token

    def assert_mocked_objects(self, mock_jwt_payload_handler, mock_jwt_encode_handler):
        mock_jwt_payload_handler.assert_called_once_with(self.service_name)
        mock_jwt_encode_handler.assert_called_once_with(self.payload)

    def test_get_endpoint(self, mock_jwt_payload_handler, mock_jwt_encode_handler,  mock_requests):
        expected_response_data = '{"data": null}'
        get_response_object = mock.Mock()
        get_response_object.text = expected_response_data
        get_response_object.status_code = 200

        self.bind_mocked_objects(mock_jwt_payload_handler, mock_jwt_encode_handler)
        mock_requests.get.return_value = get_response_object

        response = make_service_request(self.service_name, self.endpoint, method=GET)
        actual_response_data = response.text

        self.assert_mocked_objects(mock_jwt_payload_handler, mock_jwt_encode_handler)
        mock_requests.get.assert_called_once_with(self.endpoint, headers=self.headers, json=None)
        self.assertEqual(actual_response_data, expected_response_data)

    def test_post_endpoint(self, mock_jwt_payload_handler, mock_jwt_encode_handler,  mock_requests):
        expected_response_data = ''
        post_data = {
            'data': {
                'type': 'User',
                'attributes': {
                    'email': 'test@zerocater.com',
                    'password': 'test',
                    'name': 'Test This'
                }
            }
        }
        post_response_object = mock.Mock()
        post_response_object.text = expected_response_data
        post_response_object.status_code = 200

        self.bind_mocked_objects(mock_jwt_payload_handler, mock_jwt_encode_handler)
        mock_requests.post.return_value = post_response_object

        response = make_service_request(self.service_name, self.endpoint, method=POST, data=post_data)
        actual_response_data = response.text

        self.assert_mocked_objects(mock_jwt_payload_handler, mock_jwt_encode_handler)
        mock_requests.post.assert_called_once_with(self.endpoint, headers=self.headers, json=post_data)
        self.assertEqual(actual_response_data, expected_response_data)


@mock.patch('zc_common.remote_resource.request.make_service_request', autospec=True)
@mock.patch('zc_common.remote_resource.request.get_route_from_fk', autospec=True)
class GetRemoteResourceTestCase(TestCase):

    def setUp(self):
        self.service_name = 'mp-users'
        self.resource_type = 'User'
        self.params = {'id': '1'}
        self.endpoint = 'http://mp-users.herukoapp.com/users/1'

    def test_resource_retrieval(self, mock_get_route_from_fk, mock_make_service_request):
        response_data = {
            'data': {
                'id': '1',
                'type': 'User'
            }
        }

        response_from_make_service_request = mock.Mock()
        response_from_make_service_request.text = json.dumps(response_data)
        mock_get_route_from_fk.return_value = self.endpoint
        mock_make_service_request.return_value = response_from_make_service_request

        wrapped_resource = get_remote_resource(self.service_name, self.resource_type, self.params)

        mock_get_route_from_fk.assert_called_once_with(self.resource_type, self.params)
        mock_make_service_request.assert_called_once_with(self.service_name, self.endpoint)
        self.assertTrue(isinstance(wrapped_resource, RemoteResourceWrapper))
        self.assertEqual(wrapped_resource.id, response_data['data']['id'])
        self.assertEqual(wrapped_resource.type, response_data['data']['type'])

    def test_resource_list_retrieval(self, mock_get_route_from_fk, mock_make_service_request):
        response_data = {
            'data': [
                {
                    'id': '1',
                    'type': 'User'
                }
            ]
        }

        response_from_make_service_request = mock.Mock()
        response_from_make_service_request.text = json.dumps(response_data)
        mock_get_route_from_fk.return_value = self.endpoint
        mock_make_service_request.return_value = response_from_make_service_request

        wrapped_resource = get_remote_resource(self.service_name, self.resource_type, self.params)

        mock_get_route_from_fk.assert_called_once_with(self.resource_type, self.params)
        mock_make_service_request.assert_called_once_with(self.service_name, self.endpoint)
        self.assertTrue(isinstance(wrapped_resource, RemoteResourceListWrapper))
        self.assertTrue(isinstance(wrapped_resource[0], RemoteResourceWrapper))

    def test_error_retrieving_resource(self, mock_get_route_from_fk, mock_make_service_request):
        response_data = {
            'errors': [
                {
                    'status': '404',
                    'detail': 'No user with matching id'
                }
            ]
        }

        response_from_make_service_request = mock.Mock()
        response_from_make_service_request.text = response_data
        mock_get_route_from_fk.return_value = self.endpoint
        mock_make_service_request.return_value = response_from_make_service_request
        self.assertRaises(Exception, get_remote_resource, self.service_name, self.resource_type, self.params)
