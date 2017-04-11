import ujson

import datetime
import dateutil.parser
from inflection import camelize
from rest_framework import status
from rest_framework.reverse import reverse

from .tests import USER, STAFF


class ResourceCreateTestCase(object):

    def test_create__valid_data_incorrect_header(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data=self.json_request, content_type='application/json')

        self.failure_response_structure_test(response, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create__empty_request(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data={}, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_400_BAD_REQUEST)

    def test_create__missing_required_parameters(self):
        if not self.required_params:
            return True

        url = reverse(self.resource_view_name)
        self.create_json_format['data']['attributes'] = {'random_key': 'This is a random value'}

        missing_parameters_request = ujson.dumps(self.create_json_format)

        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data=missing_parameters_request, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_400_BAD_REQUEST)

    def test_create__without_relationships(self):
        if not self.relationship_keys:
            return True

        url = reverse(self.resource_view_name)
        self.create_json_format['data']['relationships'] = {}
        no_relationships_request = ujson.dumps(self.create_json_format)

        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data=no_relationships_request, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_400_BAD_REQUEST)

    def test_create__with_malformed_relationship_data(self):
        if not self.relationship_keys:
            return True

        url = reverse(self.resource_view_name)
        key = camelize(self.relationship_keys[0], False)
        self.create_json_format['data']['relationships'][key]['data'] = {
            # No type provided
            'id': '1234'}

        empty_relationships_request = ujson.dumps(self.create_json_format)

        response = self.client_post_auth(url, user_role=self.USER_ROLE, data=empty_relationships_request,
                                         content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_400_BAD_REQUEST)

    def test_create__post_non_json_data_correctly_errors(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data='invalid_JSON_obj', content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_400_BAD_REQUEST)

    def test_create__unauthorized(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, data=self.json_request, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)


class ResourceCreateWithoutPermissionTestCase(object):

    def test_create__valid_data_incorrect_header(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data=self.json_request, content_type='application/json')

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_create__empty_request(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data={}, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_create__missing_required_parameters(self):
        if not self.required_params:
            return True

        url = reverse(self.resource_view_name)
        self.create_json_format['data']['attributes'] = {'random_key': 'This is a random value'}

        missing_parameters_request = ujson.dumps(self.create_json_format)

        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data=missing_parameters_request, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_create__without_relationships(self):
        if not self.relationship_keys:
            return True

        url = reverse(self.resource_view_name)
        self.create_json_format['data']['relationships'] = {}
        no_relationships_request = ujson.dumps(self.create_json_format)

        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data=no_relationships_request, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_create__with_malformed_relationship_data(self):
        if not self.relationship_keys:
            return True

        url = reverse(self.resource_view_name)
        key = camelize(self.relationship_keys[0], False)
        self.create_json_format['data']['relationships'][key]['data'] = {
            # No type provided
            'id': '1234'}

        empty_relationships_request = ujson.dumps(self.create_json_format)

        response = self.client_post_auth(url, user_role=self.USER_ROLE, data=empty_relationships_request,
                                         content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_create__post_non_json_data_correctly_errors(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, user_role=self.USER_ROLE,
                                         data='invalid_JSON_obj', content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_create__unauthorized(self):
        url = reverse(self.resource_view_name)
        response = self.client_post_auth(url, data=self.json_request, content_type='application/vnd.api+json')

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)


class ResourceUpdateTestCase(object):

    def get_patch_response(self, request_data):
        user_id = getattr(getattr(self.resource, 'user', None), 'id', None)

        return self.client_patch_auth(
            reverse(self.resource_view_name, args=(self.resource.id,)),
            user_role=self.USER_ROLE,
            user_id=user_id,
            company_permissions=getattr(self, 'company_permissions', {}),
            data=ujson.dumps(request_data),
            content_type='application/vnd.api+json'
        )

    def test_update__resource(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.get_patch_response(update_data)

        self.success_response_structure_test(response, status.HTTP_200_OK)

        setattr(self.resource, attribute_name, new_attribute_value)

        self.validate_instance_in_response(response, self.resource, self.attributes,
                                           relationship_keys=self.relationship_keys)

        db_obj = self.resource_class.objects.get(id=self.resource.id)
        db_value = getattr(db_obj, attribute_name)
        if isinstance(db_value, datetime.datetime):
            new_attribute_value = dateutil.parser.parse(new_attribute_value)

        elif isinstance(db_value, datetime.date):
            new_attribute_value = new_attribute_value.isoformat()

        elif isinstance(db_value, datetime.time):
            new_attribute_value = new_attribute_value.isoformat()

        self.assertEqual(db_value, new_attribute_value)

    def test_update__incorrect_type(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['type'] = 'RandomType'
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.get_patch_response(update_data)

        self.failure_response_structure_test(response, status.HTTP_409_CONFLICT)

    def test_update__multiple_fields(self):
        if len(self.new_attribute_values) < 2:
            return True

        attribute_name_1 = self.attributes[0]
        new_attribute_value_1 = self.new_attribute_values[0]

        attribute_name_2 = self.attributes[1]
        new_attribute_value_2 = self.new_attribute_values[1]

        update_data = self.patch_request_stub
        update_data['data']['attributes'] = {
            attribute_name_1: new_attribute_value_1,
            attribute_name_2: new_attribute_value_2
        }

        response = self.get_patch_response(update_data)

        setattr(self.resource, attribute_name_1, new_attribute_value_1)
        setattr(self.resource, attribute_name_2, new_attribute_value_2)

        self.success_response_structure_test(response, status.HTTP_200_OK)

        self.validate_instance_in_response(response, self.resource, self.attributes,
                                           relationship_keys=self.relationship_keys)

        db_obj = self.resource_class.objects.get(id=self.resource.id)
        self.assertEqual(getattr(db_obj, attribute_name_1), new_attribute_value_1)
        self.assertEqual(getattr(db_obj, attribute_name_2), new_attribute_value_2)

    def test_update__missing_item_404(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['id'] = 12457
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.client_patch_auth(
            reverse(self.resource_view_name, args=(12457,)),
            user_role=self.USER_ROLE,
            data=ujson.dumps(update_data),
            content_type='application/vnd.api+json'
        )

        self.failure_response_structure_test(response, status.HTTP_404_NOT_FOUND)

    def test_update__unauthorized(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.client_patch_auth(
            reverse(self.resource_view_name, args=(self.resource.id,)),
            data=ujson.dumps(update_data),
            content_type='application/vnd.api+json'
        )

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)


class ResourceUpdateLimitedPermissionTestCase(object):

    def get_patch_response(self, request_data):
        user_id = getattr(getattr(self.resource, 'user', None), 'id', None)

        return self.client_patch_auth(
            reverse(self.resource_view_name, args=(self.resource.id,)),
            user_role=self.USER_ROLE,
            user_id=user_id,
            company_permissions=getattr(self, 'company_permissions', {}),
            data=ujson.dumps(request_data),
            content_type='application/vnd.api+json'
        )

    def test_update__resource(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.get_patch_response(update_data)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_update__incorrect_type(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['type'] = 'RandomType'
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.get_patch_response(update_data)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_update__multiple_fields(self):
        if len(self.new_attribute_values) < 2:
            return True

        attribute_name_1 = self.attributes[0]
        new_attribute_value_1 = self.new_attribute_values[0]

        attribute_name_2 = self.attributes[1]
        new_attribute_value_2 = self.new_attribute_values[1]

        update_data = self.patch_request_stub
        update_data['data']['attributes'] = {
            attribute_name_1: new_attribute_value_1,
            attribute_name_2: new_attribute_value_2
        }

        response = self.get_patch_response(update_data)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_update__missing_item_404(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['id'] = 12457
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.client_patch_auth(
            reverse(self.resource_view_name, args=(12457,)),
            user_role=self.USER_ROLE,
            data=ujson.dumps(update_data),
            content_type='application/vnd.api+json'
        )

        self.failure_response_structure_test(response, status.HTTP_404_NOT_FOUND)

    def test_update__unauthorized(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.client_patch_auth(
            reverse(self.resource_view_name, args=(self.resource.id,)),
            data=ujson.dumps(update_data),
            content_type='application/vnd.api+json'
        )

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)


class ResourceUpdateWithoutPermissionTestCase(ResourceUpdateLimitedPermissionTestCase):

    # Overriding method, when no permission we return a 403 instead of a 404
    def test_update__missing_item_404(self):
        attribute_name = self.attributes[0]
        new_attribute_value = self.new_attribute_values[0]

        update_data = self.patch_request_stub
        update_data['data']['id'] = 12457
        update_data['data']['attributes'] = {attribute_name: new_attribute_value}

        response = self.client_patch_auth(
            reverse(self.resource_view_name, args=(12457,)),
            user_role=self.USER_ROLE,
            data=ujson.dumps(update_data),
            content_type='application/vnd.api+json'
        )

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)


class ResourceFlaggedDeleteTestCase(object):

    def test_resource(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(
            url,
            user_role=self.USER_ROLE,
            company_permissions=getattr(self, 'company_permissions', {}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify that the object still exists and that the deleted_at field has been set
        deleted_resource = self.resource_class.objects.filter(id=self.resource.id)
        self.assertEqual(deleted_resource.count(), 1)
        self.assertIsNotNone(deleted_resource[0].deleted_at)

    def test_delete__404_for_nonexistant_resource(self):
        url = reverse(self.resource_view_name, args=(9999,))
        response = self.client_delete_auth(url, user_role=self.USER_ROLE)

        self.failure_response_structure_test(response, status.HTTP_404_NOT_FOUND)

    def test_delete__unauthorized(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url)

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)


class ResourceDeleteTestCase(object):

    def test_delete_resource__by_user(self):
        if not hasattr(self.resource, 'user'):
            return True
        resource = self.resource_class.objects.filter(id=self.resource.id)
        self.assertEqual(resource.count(), 1)

        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(
            url,
            user_role=self.USER_ROLE,
            user_id=self.resource.user.id,
            company_permissions=getattr(self, 'company_permissions', {}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        deleted_resource = self.resource_class.objects.filter(id=self.resource.id)
        self.assertEqual(deleted_resource.count(), 0)

    def test_delete_resource__by_staff(self):
        resource = self.resource_class.objects.filter(id=self.resource.id)
        self.assertEqual(resource.count(), 1)

        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(
            url,
            user_role=STAFF,
            company_permissions=getattr(self, 'company_permissions', {}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        deleted_resource = self.resource_class.objects.filter(id=self.resource.id)
        self.assertEqual(deleted_resource.count(), 0)

    def test_delete__404_for_nonexistant_resource(self):
        url = reverse(self.resource_view_name, args=(9999,))
        response = self.client_delete_auth(url, user_role=STAFF)

        self.failure_response_structure_test(response, status.HTTP_404_NOT_FOUND)

    def test_delete__unauthorized(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url)

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)

    def test_delete__forbidden(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url, user_role=USER)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)


class ResourceNoDeleteTestCase(object):

    def test_delete_resource__by_user(self):
        if not hasattr(self.resource, 'user'):
            return True
        resource = self.resource_class.objects.filter(id=self.resource.id)
        self.assertEqual(resource.count(), 1)

        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url, user_role=self.USER_ROLE, user_id=self.resource.user.id)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_delete_resource__by_staff(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url, user_role=self.USER_ROLE)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_delete__for_nonexistant_resource(self):
        url = reverse(self.resource_view_name, args=(9999,))
        response = self.client_delete_auth(url, user_role=self.USER_ROLE)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)

    def test_delete__unauthorized(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url)

        self.failure_response_structure_test(response, status.HTTP_401_UNAUTHORIZED)

    def test_delete__forbidden(self):
        url = reverse(self.resource_view_name, args=(self.resource.id,))
        response = self.client_delete_auth(url, user_role=self.USER_ROLE)

        self.failure_response_structure_test(response, status.HTTP_403_FORBIDDEN)


class ResourceDeleteWithoutPermissionTestCase(ResourceNoDeleteTestCase):
    pass


class ResourceDeleteLimitedTestCase(ResourceNoDeleteTestCase):

    def test_delete__for_nonexistant_resource(self):
        url = reverse(self.resource_view_name, args=(9999,))
        response = self.client_delete_auth(url, user_role=self.USER_ROLE)

        self.failure_response_structure_test(response, status.HTTP_404_NOT_FOUND)
