import json
from inflection import camelize, underscore, pluralize

from django.test import TestCase
from rest_framework.test import APITestCase


class ResponseTestCase(APITestCase):
    SUCCESS_HIGH_LEVEL_KEYS = ['data']
    SUCCESS_DATA_KEYS = ['id', 'type']

    FAILURE_HIGH_LEVEL_KEYS = ['errors']
    FAILURE_DATA_KEYS = ['status', 'source', 'detail']

    INSTANCE_TOP_LEVEL_KEYS = ['type', 'id', 'attributes']

    def convert_to_list(self, data):
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return [data]

        try:
            return data.all()
        except AttributeError:
            return [data]

    def validate_instance_in_data(self, data, instance, attributes, relationship_keys=None):
        self.assertTrue(
            all(key in data for key in self.INSTANCE_TOP_LEVEL_KEYS))

        instance_attributes = data['attributes']
        for key in attributes:
            instance_attribute = getattr(instance, key)

            if hasattr(instance_attribute, '__call__'):
                instance_attribute = instance_attribute()

            self.assertEqual(
                instance_attributes[camelize(key, False)], instance_attribute)

        if not relationship_keys:
            return True

        relationships = data['relationships']

        for relationship_name in relationship_keys:
            name = camelize(relationship_name, False)
            self.assertTrue(name in relationships)
            data = self.convert_to_list(relationships[name]['data'])
            instance_relationship = self.convert_to_list(
                getattr(instance, relationship_name))

            for data_object, instance_object in zip(data, instance_relationship):
                self.assertEqual(data_object['id'], str(instance_object.id))

                try:
                    instance_type = instance_object.type
                except AttributeError:
                    instance_type = instance_object.__class__.__name__

                self.assertEqual(data_object['type'], instance_type)

    def validate_instance_in_response(self, response, instance, attributes, relationship_keys=None):
        data = self.load_json(response)['data']
        self.validate_instance_in_data(
            data, instance, attributes, relationship_keys)

    def validate_instance_list_in_response(self, response, instances, attributes, relationship_keys=None):
        instance_data = self.load_json(response)['data']
        self.assertEqual(len(instance_data), len(instances))

        instance_data.sort(key=lambda x: x['id'])
        list(instances).sort(key=lambda x: x.id)

        for data, instance in zip(instance_data, instances):
            self.validate_instance_in_data(
                data, instance, attributes, relationship_keys)

    def success_response_structure_test(self, response, status, relationship_keys=None):
        """
        This can be extended in the future to cover stricter validation of the
        response as follows:

        * Top level response MUST contain AT LEAST ONE of ['data', 'meta']
        * Top level response MUST contain ['links']  # Our requirement
            - Top level links MUST contain ['self']; MAY contain ['related']

        * Resource object MUST contain ['id', 'type']
        * Resource object MUST contain AT LEAST ONE of ['attributes', 'relationships']
        * Resource object MAY contain ['links', 'meta']

        * Relationship object MUST contain AT LEAST ONE of ['links', 'data', 'meta']
            - Relationship links object MUST contain AT LEAST ONE of ['self', 'related']
        """
        self.assertEqual(response.status_code, status)

        response_content = self.load_json(response)

        self.assertTrue(
            all(key in response_content for key in self.SUCCESS_HIGH_LEVEL_KEYS))

        for data in self.convert_to_list(response_content['data']):
            self.assertTrue(all(key in data for key in self.SUCCESS_DATA_KEYS))

            if relationship_keys:
                self.assertTrue('relationships' in data)
                relationships = data['relationships']
                self.assertTrue(
                    all(camelize(key, False) in relationships for key in relationship_keys))

                for relationship_name, relationship in relationships.iteritems():
                    self.assertTrue(
                        all(key in relationship for key in ['data', 'links']))

                    for relationship_data in self.convert_to_list(relationship['data']):
                        self.assertTrue(
                            all(key in relationship_data for key in ['type', 'id']))

                    links = relationship['links']

                    resource_pk = self.resource.pk if hasattr(self, 'resource') else '[0-9A-Za-z]*'

                    self.assertRegexpMatches(links['self'], r'^https?://.*/{}/{}/relationships/{}'.format(
                        self.resource_name, resource_pk, underscore(relationship_name)))

                    if hasattr(self, 'remote_relationship_keys') and relationship_name in self.remote_relationship_keys:
                        self.assertRegexpMatches(links['related'], r'^https?://.*/{}/\w'.format(
                            pluralize(underscore(self.get_remote_relationship_name(relationship_name)))))
                    else:
                        self.assertRegexpMatches(links['related'], r'^https?://.*/{}/{}/{}'.format(
                            self.resource_name, resource_pk, underscore(relationship_name)))

    def get_remote_relationship_name(self, relationship_name):
        """
        If there are any remote relationships whose related link doesn't map
        directly to its field name, a mapping dictionary can be declared on
        the test class named self.relationship_name_mapping.

        Example:
        self.relationship_name_mapping = {
            'homeAddress': 'address',
            'workAddress': 'address'
        }
        """
        if hasattr(self, 'relationship_name_mapping') and self.relationship_name_mapping.get(relationship_name):
            return self.relationship_name_mapping[relationship_name]
        return relationship_name

    def failure_response_structure_test(self, response, status):
        self.assertEqual(response.status_code, status)

        response_content = self.load_json(response)

        self.assertTrue(
            all(key in response_content for key in self.FAILURE_HIGH_LEVEL_KEYS))

        for error in response_content['errors']:
            self.assertTrue(
                all(key in error for key in self.FAILURE_DATA_KEYS))

    def load_json(self, response):
        return json.loads(response.content.decode())
