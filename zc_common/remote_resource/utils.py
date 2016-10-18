from __future__ import absolute_import

import sys
from zc_common.remote_resource.request import make_service_request, get_route_from_fk, ServiceRequestException


class EmitEventFailure(Exception):
    pass


def emit_event(service_name, event_type, event_name, resource_type, resource_id, user_id, meta_data=None):
    try:
        create_event_url = get_route_from_fk(event_type)

        event_data = generate_event_data(
            event_type,
            event_name,
            resource_type,
            resource_id,
            user_id,
            meta_data=meta_data
        )

        response = make_service_request(service_name, create_event_url, 'post', event_data)
        return response
    except ServiceRequestException:
        message = ("Error emitting {} to {}. resource_type: {}, resource_id: {}, user_id: {}, meta_data: {}"
                   .format(event_name, event_type, resource_type, resource_id, user_id, meta_data))
        raise EmitEventFailure(message), None, sys.exc_info()[2]


def generate_event_data(event_type, event_name, resource_type, resource_id, user_id, meta_data=None):
    data = {
        'data': {
            'type': event_type,
            'attributes': {
                'eventType': event_name,
                'resourceType': resource_type,
                'resourceId': resource_id,
                'userId': user_id
            }
        }
    }

    if meta_data and isinstance(meta_data, dict):
        data.update({
            'meta': meta_data
        })

    return data
