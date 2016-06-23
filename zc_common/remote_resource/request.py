import requests
from inflection import underscore
from uritemplate import expand, variables
from zc_common.jwt_auth.utils import service_jwt_payload_handler, jwt_encode_handler
from zc_common.settings import zc_settings


class RemoteResourceWrapper(object):

    def __init__(self, data):
        self.data = data
        self.create_properties_from_data()

    def create_properties_from_data(self):
        if 'id' in self.data:
            setattr(self, 'id', self.data.get('id'))

        if 'type' in self.data:
            setattr(self, 'type', self.data.get('type'))

        if 'attributes' in self.data:
            attributes = self.data['attributes']
            for key in attributes.keys():
                setattr(self, underscore(key), attributes[key])

        if 'relationships' in self.data:
            relationships = self.data['relationships']

            for key in relationships.keys():
                if isinstance(relationships[key]['data'], list):
                    setattr(self, underscore(key), RemoteResourceListWrapper(relationships[key]['data']))
                else:
                    setattr(self, underscore(key), RemoteResourceWrapper(relationships[key]['data']))


class RemoteResourceListWrapper(list):
    def __init__(self, data):
        self.data = data
        self.add_items_from_data()

    def add_items_from_data(self):
        map(lambda x: self.append(RemoteResourceWrapper(x)), self.data)


def get_route_from_fk(resource_type, url_param_values={}):
    """Gets a fully qualified URI for a given resource_type and url_param_values.
    url_param_values should be a dict instance with keys being url parameters.
    """
    routes = requests.get(zc_settings.GATEWAY_ROOT_PATH).json()

    for route in routes.iterkeys():
        if 'resource_type' in routes[route] and routes[route]['resource_type'] == resource_type:
            if len(variables(route)) != len(url_param_values):
                raise Exception('No parameters were supplied. Required params: {0}'.format(variables(route)))

            expanded = expand(route, url_param_values)
            return '{0}{1}'.format(routes[route]['domain'], expanded)

    raise Exception('No route for resource_type: "{0}"'.format(resource_type))


def make_service_request(service_name, endpoint):
    """Makes a JWT authenticated service request to the URL provided and returns the response.
    Returns a dictionary of the returned response.
    """
    jwt_token = jwt_encode_handler(service_jwt_payload_handler(service_name))
    headers = {'Authorization': 'JWT {}'.format(jwt_token), 'Content-Type': 'application/vnd.api+json'}
    response = requests.get(endpoint, headers=headers)
    return response.json()


def get_remote_resource(service_name, resource_type, url_param_values):
    url = get_route_from_fk(resource_type, url_param_values)
    response_data = make_service_request(service_name, url)

    if 'data' in response_data:
        resource_data = response_data['data']
        if isinstance(resource_data, list):
            return RemoteResourceListWrapper(resource_data)
        return RemoteResourceWrapper(resource_data)

    msg = "Error while retrieving resource. ServiceName: {0}, ResourceType: {1}, UrlParamValues: {2}, " \
          "ResponseData: {3}".format(service_name, resource_type, url_param_values, response_data)
    raise Exception(msg)
