from unittest import TestCase

from django.db import models

from zc_common.remote_resource.models import GenericRemoteForeignKey, RemoteResource


class FKModel(models.Model):
    resource_id = models.TextField(blank=True)
    resource_type = models.TextField(blank=True)
    owner = GenericRemoteForeignKey(resource_types=['User', 'Company'])

    class Meta:
        app_label = 'tests'


class TestGenericRemoteForeignKey(TestCase):
    def test_accepts_only_remote_resource(self):
        model = FKModel()
        with self.assertRaises(ValueError):
            model.owner = 1

        model.owner = RemoteResource('User', '1')

    def test_fills_sub_fields(self):
        model = FKModel()

        resource_type = 'User'
        resource_id = '1'

        model.owner = RemoteResource(resource_type, resource_id)

        self.assertEqual(model.resource_type, resource_type)
        self.assertEqual(model.resource_id, resource_id)

    def test_returns_remote_resource(self):
        model = FKModel()
        model.resource_type = 'User'
        model.resource_id = '1'

        self.assertTrue(isinstance(model.owner, RemoteResource))

    def test_accepts_only_acceptable_types(self):
        model = FKModel()
        with self.assertRaises(ValueError):
            model.owner = RemoteResource('Thing', '1')
