import mock
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

    def test_remote_resource_list_wrapper_multiple_relationship_links(self):
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

        self.assertEqual(resources[0].authors.links.self, '/articles/1/relationships/authors')
        self.assertEqual(resources[0].authors.links.related, '/articles/1/authors')
