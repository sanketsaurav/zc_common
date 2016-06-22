import requests
from django.test import TestCase
from zc_common.settings import zc_settings
from zc_common.remote_resource.request import \
    RemoteResourceWrapper, get_route_from_fk, make_service_request, get_remote_resource


class RequestTestCase(TestCase):

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

        resource = RemoteResourceWrapper(data)

        self.assertEqual(resource.title, "Omakase")
        self.assertEqual(resource.author, {"type": "People", "id": "9"})

    def test_remote_resource_wrapper_multiple_relationship(self):
        data = {
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {
                    "title": "Omakase"
                },
                "relationships": {
                    "authors": [
                        {
                            "links": {
                                "self": "/articles/1/relationships/author",
                                "related": "/articles/1/author"
                            },
                            "data": {"type": "People", "id": "9"}
                        }
                    ]
                }
            }
        }

        resource = RemoteResourceWrapper(data)

        self.assertEqual(resource.title, "Omakase")
        self.assertEqual(resource.authors, [{"type": "People", "id": "9"}])


class TestRouteRetrieval(TestCase):

    def test_wrong_resource_type(self):
        resource_type = 'Movie'
        self.assertRaises(Exception, get_route_from_fk, resource_type)

    def test_correct_resource_type(self):
        print zc_settings.GATEWAY_ROOT_PATH
        expected_url = 'https://mp-users.herokuapp.com/users/1'
        result_url = get_route_from_fk('User', {'id': 1})
        self.assertEqual(expected_url, result_url)

    def test_missing_required_parameters(self):
        resource_type = 'User'
        self.assertRaises(Exception, get_route_from_fk, resource_type)


class TestServiceRequest(TestCase):
    pass


class TestRemoteResourceRetrieval(TestCase):
    pass
