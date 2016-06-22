import requests
import json
from uritemplate import expand
from django.conf import settings
from zc_common.jwt_auth.utils import service_jwt_payload_handler, jwt_encode_handler
from zc_common.settings import api_settings as zc_common_settings


def get_route_from_fk(resource_type, pk=None):
    """Gets a fully qualified URI for a given resource_type, pk"""
    routes = requests.get(zc_common_settings.GATEWAY_ROOT_PATH).json()

    for route in routes.iterkeys():
        if 'resource_type' in routes[route] and routes[route]['resource_type'] == resource_type:
            expanded = expand(route, {'id': pk})
            return '{0}{1}'.format(routes[route]['domain'], expanded)

    raise Exception('No route for resource_type: "{0}"'.format(resource_type))


def make_service_request(service_name, endpoint):
    """Makes a JWT authenticated service request to the URL provided and returns the response.
    Returns a dictionary of the returned response.
    """
    jwt_token = jwt_encode_handler(service_jwt_payload_handler(service_name))
    headers = {'Authorization': 'JWT {}'.format(jwt_token), 'Content-Type': 'application/vnd.api+json'}
    return json.loads(requests.get(endpoint, headers=headers).json())


def get_remote_resource(resource_type, pk):
    url = get_route_from_fk(resource_type, pk)
    response_data = make_service_request(url)
    return RemoteResourceWrapper(response_data)


class RemoteResourceWrapper(object):

    def __init__(self, data):
        self.data = data
        self.create_properties_from_data()

    def create_properties_from_data(self):
        data = self.data["data"]

        setattr(self, 'id', data['id'])
        setattr(self, 'type', data['type'])

        attributes = data['attributes']
        for key in attributes.keys():
            setattr(self, key, attributes[key])

        if 'relationships' in data:
            relationships = data['relationships']

            for key in relationships.keys():
                if isinstance(relationships[key], list):
                    rel_data = map(lambda x: x['data'], relationships[key])
                    setattr(self, key, rel_data)
                else:
                    setattr(self, key, relationships[key]['data'])