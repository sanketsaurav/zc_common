from .request import make_service_request, get_route_from_fk


def emit_event(service_name, event_type, event_name, resource_type, resource_id, user_id, meta_data=None):
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
